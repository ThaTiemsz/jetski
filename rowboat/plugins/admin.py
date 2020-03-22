import re
import csv
import time
import gevent
import humanize
import operator

from StringIO import StringIO
from peewee import fn
from holster.emitter import Priority
from rapidfuzz import fuzz
from simplejson import JSONDecodeError

from datetime import datetime, timedelta

from disco.bot import CommandLevels
from disco.types.user import User as DiscoUser
from disco.types.channel import Channel as DiscoChannel
from disco.types.guild import GuildMember
from disco.types.message import MessageTable, MessageEmbed, MessageEmbedField, MessageEmbedThumbnail
from disco.types.permissions import Permissions
from disco.util.functional import chunks
from disco.util.sanitize import S
from disco.api.http import Routes, APIException

from rowboat.plugins import RowboatPlugin as Plugin, CommandFail, CommandSuccess
from rowboat.util.timing import Eventual
from rowboat.util.images import get_dominant_colors_user
from rowboat.util.input import parse_duration, humanize_duration
from rowboat.util.gevent import wait_many
from rowboat.redis import rdb
from rowboat.types import Field, DictField, ListField, snowflake, SlottedModel
from rowboat.types.plugin import PluginConfig
from rowboat.plugins.modlog import Actions
from rowboat.models.user import User, Infraction
from rowboat.models.guild import GuildMemberBackup, GuildBan, GuildEmoji, GuildVoiceSession
from rowboat.models.message import Message, Reaction, MessageArchive
from rowboat.constants import (
    GREEN_TICK_EMOJI_ID, RED_TICK_EMOJI_ID, GREEN_TICK_EMOJI, RED_TICK_EMOJI
)

EMOJI_RE = re.compile(r'<:[a-zA-Z0-9_]+:([0-9]+)>')

CUSTOM_EMOJI_STATS_SERVER_SQL = """
SELECT gm.emoji_id, gm.name, count(*) FROM guild_emojis gm
JOIN messages m ON m.emojis @> ARRAY[gm.emoji_id]
WHERE gm.deleted=false AND gm.guild_id={guild} AND m.guild_id={guild}
GROUP BY 1, 2
ORDER BY 3 {}
LIMIT 30
"""

CUSTOM_EMOJI_STATS_GLOBAL_SQL = """
SELECT gm.emoji_id, gm.name, count(*) FROM guild_emojis gm
JOIN messages m ON m.emojis @> ARRAY[gm.emoji_id]
WHERE gm.deleted=false AND gm.guild_id={guild}
GROUP BY 1, 2
ORDER BY 3 {}
LIMIT 30
"""


def clamp(string, size):
    if len(string) > size:
        return string[:size] + '...'
    return string


def maybe_string(obj, exists, notexists, **kwargs):
    if obj:
        return exists.format(o=obj, **kwargs)
    return notexists.format(**kwargs)


class PersistConfig(SlottedModel):
    roles = Field(bool, default=False)
    nickname = Field(bool, default=False)
    voice = Field(bool, default=False)

    role_ids = ListField(snowflake, default=[])


class AdminConfig(PluginConfig):
    confirm_actions = Field(bool, default=True)

    # Role saving information
    persist = Field(PersistConfig, default=None)

    # Aliases to roles, can be used in place of IDs in commands
    role_aliases = DictField(unicode, snowflake)

    # Group roles can be joined/left by any user
    group_roles = DictField(lambda value: unicode(value).lower(), snowflake)
    group_confirm_reactions = Field(bool, default=False)

    # Locked roles cannot be changed unless they are unlocked w/ command
    locked_roles = ListField(snowflake)

    # The mute role
    mute_role = Field(snowflake, default=None)
    reason_edit_level = Field(int, default=int(CommandLevels.ADMIN))

    # Infraction DMs
    infraction_dms = Field(bool, default=False)
    dms_include_mod = Field(bool, default=True)

def infraction_message(event, user, action, server, moderator, reason, expires='Never', auto=False):
    infractions = {
        'warn': {
            'name': 'Warning',
            'context': 'warned'
        },
        'mute': {
            'name': 'Mute',
            'context': 'muted'
        },
        'tempmute': {
            'name': 'Tempmute',
            'context': 'temporarily muted'
        },
        'kick': {
            'name': 'Kick',
            'context': 'kicked'
        },
        'ban': {
            'name': 'Ban',
            'context': 'banned'
        },
        'tempban': {
            'name': 'Tempban',
            'context': 'temporarily banned'
        }
    }

    if reason == None:
        reason = '*Not specified*'
    
    if expires != 'Never':
        # Hacky time humanizer
        now = datetime.utcnow()
        diff_delta = expires - now
        diff = int(diff_delta.total_seconds())
        minutes, seconds = divmod(diff, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        weeks, days = divmod(days, 30)
        units = [weeks, days, hours, minutes, seconds]
        unit_strs = ['week', 'day', 'hour', 'minute', 'second']
        expires = ''
        for x in range(0, 5):
            if units[x] == 0:
                continue
            else:
                if units[x] > 1:
                    expires += '{} {}s, '.format(units[x], unit_strs[x])
                else:
                    expires += '{} {}, '.format(units[x], unit_strs[x])
        expires = expires[:-2]
    
    embed = MessageEmbed()
    embed.title = '{}'.format(server)
    embed.set_footer(text='This is an automated message. Contact the moderators for more information.')
    embed.timestamp = datetime.utcnow().isoformat()

    if action in ('mute', 'tempmute', 'warn'):
        embed.color = 0xfdfd96
    elif action == 'kick':
        embed.color = 0xffb347
    else:
        embed.color = 0xff6961

    embed.add_field(name='Action', value=infractions[action]['name'], inline=True)

    # Also hacky method to avoid SpamPlugin attribute errors on dms_include_mod
    if auto:
        embed.add_field(name='Moderator', value=moderator, inline=True)
    else:
        if event.config.dms_include_mod:
            embed.add_field(name='Moderator', value=moderator, inline=True)
    
    embed.add_field(name='Reason', value=reason, inline=True)
    embed.add_field(name='Expires in', value=expires, inline=True)
    
    return infractions, embed

@Plugin.with_config(AdminConfig)
class AdminPlugin(Plugin):
    def load(self, ctx):
        super(AdminPlugin, self).load(ctx)

        self.cleans = {}
        self.inf_task = Eventual(self.clear_infractions)
        self.spawn_later(5, self.queue_infractions)

        self.unlocked_roles = {}
        self.role_debounces = {}
    
    def send_infraction_dm(self, event, user, action, server, moderator, reason, expires='Never'):
        if not event.config.infraction_dms:
            return
        
        infractions, embed = infraction_message(event, user, action, server, moderator, reason, expires)

        try:
            dm = self.client.api.users_me_dms_create(user)

            preposition = ''
            if action in ('kick', 'ban', 'tempban'):
                preposition = 'from'
            else:
                preposition = 'in'
            
            return dm.send_message('You\'ve been {} {} **{}**.'.format(infractions[action]['context'], preposition, server), embed=embed)
        except:
            raise

    def queue_infractions(self):
        next_infraction = list(Infraction.select().where(
            (Infraction.active == 1) &
            (~(Infraction.expires_at >> None))
        ).order_by(Infraction.expires_at.asc()).limit(1))

        if not next_infraction:
            self.log.info('[INF] no infractions to wait for')
            return

        self.log.info('[INF] waiting until %s for %s', next_infraction[0].expires_at, next_infraction[0].id)
        self.inf_task.set_next_schedule(next_infraction[0].expires_at)

    def clear_infractions(self):
        expired = list(Infraction.select().where(
            (Infraction.active == 1) &
            (Infraction.expires_at < datetime.utcnow())
        ))

        self.log.info('[INF] attempting to clear %s expired infractions', len(expired))

        for item in expired:
            guild = self.state.guilds.get(item.guild_id)
            if not guild:
                self.log.warning('[INF] failed to clear infraction %s, no guild exists', item.id)
                continue

            # TODO: hacky
            type_ = {i.index: i for i in Infraction.Types.attrs}[item.type_]
            if type_ == Infraction.Types.TEMPBAN:
                self.call(
                    'ModLogPlugin.create_debounce',
                    guild.id,
                    ['GuildBanRemove'],
                    user_id=item.user_id,
                )

                guild.delete_ban(item.user_id)

                # TODO: perhaps join on users above and use username from db
                self.call(
                    'ModLogPlugin.log_action_ext',
                    Actions.MEMBER_TEMPBAN_EXPIRE,
                    guild.id,
                    user_id=item.user_id,
                    user=unicode(self.state.users.get(item.user_id) or item.user_id),
                    inf=item
                )
            elif type_ == Infraction.Types.TEMPMUTE or Infraction.Types.TEMPROLE:
                member = guild.get_member(item.user_id)
                if member:
                    if item.metadata['role'] in member.roles:
                        self.call(
                            'ModLogPlugin.create_debounce',
                            guild.id,
                            ['GuildMemberUpdate'],
                            user_id=item.user_id,
                            role_id=item.metadata['role'],
                        )

                        member.remove_role(item.metadata['role'])

                        self.call(
                            'ModLogPlugin.log_action_ext',
                            Actions.MEMBER_TEMPMUTE_EXPIRE,
                            guild.id,
                            member=member,
                            inf=item
                        )
                else:
                    GuildMemberBackup.remove_role(
                        item.guild_id,
                        item.user_id,
                        item.metadata['role'])
            else:
                self.log.warning('[INF] failed to clear infraction %s, type is invalid %s', item.id, item.type_)
                continue

            # TODO: n+1
            item.active = False
            item.save()

        # Wait a few seconds to backoff from a possible bad loop, and requeue new infractions
        gevent.sleep(5)
        self.queue_infractions()

    def restore_user(self, event, member):
        try:
            backup = GuildMemberBackup.get(guild_id=event.guild_id, user_id=member.user.id)
        except GuildMemberBackup.DoesNotExist:
            return

        kwargs = {}

        if event.config.persist.nickname and backup.nick is not None:
            kwargs['nick'] = backup.nick

        if event.config.persist.roles:
            roles = set(event.guild.roles.keys())

            if event.config.persist.role_ids:
                roles &= set(event.config.persist.role_ids)

            roles = set(backup.roles) & roles
            if roles:
                kwargs['roles'] = list(roles)

        if event.config.persist.voice:
            if backup.mute:
                kwargs['mute'] = backup.mute

            if backup.deaf:
                kwargs['deaf'] = backup.deaf

        if not kwargs:
            return

        self.call(
            'ModLogPlugin.create_debounce',
            event,
            ['GuildMemberUpdate'],
        )

        member.modify(**kwargs)

        self.call(
            'ModLogPlugin.log_action_ext',
            Actions.MEMBER_RESTORE,
            event.guild.id,
            member=member,
            elements=', '.join(kwargs.keys())
        )

    @Plugin.listen('GuildMemberRemove', priority=Priority.BEFORE)
    def on_guild_member_remove(self, event):
        if event.user.id in event.guild.members:
            GuildMemberBackup.create_from_member(event.guild.members.get(event.user.id))

    @Plugin.listen('GuildMemberAdd')
    def on_guild_member_add(self, event):
        if not event.config.persist:
            return

        self.restore_user(event, event.member)

    @Plugin.listen('GuildMemberUpdate', priority=Priority.BEFORE)
    def on_guild_member_update(self, event):
        pre_member = event.guild.members.get(event.id)
        if not pre_member:
            return

        pre_roles = set(pre_member.roles)
        post_roles = set(event.roles)
        if pre_roles == post_roles:
            return

        removed = pre_roles - post_roles

        # If the user was unmuted, mark any temp-mutes as inactive
        if event.config.mute_role in removed:
            Infraction.clear_active(event, event.user.id, [Infraction.Types.TEMPMUTE])

    @Plugin.listen('GuildBanRemove')
    def on_guild_ban_remove(self, event):
        Infraction.clear_active(event, event.user.id, [Infraction.Types.BAN, Infraction.Types.TEMPBAN])

    @Plugin.listen('GuildRoleUpdate', priority=Priority.BEFORE)
    def on_guild_role_update(self, event):
        if event.role.id not in event.config.locked_roles:
            return

        if event.role.id in self.unlocked_roles and self.unlocked_roles[event.role.id] > time.time():
            return

        if event.role.id in self.role_debounces:
            if self.role_debounces.pop(event.role.id) > time.time():
                return

        role_before = event.guild.roles.get(event.role.id)
        if not role_before:
            return

        to_update = {}
        for field in ('name', 'hoist', 'color', 'permissions', 'position'):
            if getattr(role_before, field) != getattr(event.role, field):
                to_update[field] = getattr(role_before, field)

        if to_update:
            self.log.warning('Rolling back update to role %s (in %s), role is locked', event.role.id, event.guild_id)
            self.role_debounces[event.role.id] = time.time() + 60
            event.role.update(**to_update)

    @Plugin.command('unban', '<user:snowflake> [reason:str...]', level=CommandLevels.MOD)
    def unban(self, event, user, reason=None):
        try:
            GuildBan.get(user_id=user, guild_id=event.guild.id)
            event.guild.delete_ban(user)
            GuildBan.delete().where(
                (GuildBan.user_id == event.author.id) &
                (GuildBan.guild_id == event.guild.id)
            )
        except (GuildBan.DoesNotExist, APIException) as e:
            if hasattr(e, 'code') and e.code != 10026: # Unknown Ban
                raise APIException(e.response)
            raise CommandFail('user with id `{}` is not banned'.format(user))

        Infraction.create(
            guild_id=event.guild.id,
            user_id=user,
            actor_id=event.author.id,
            type_=Infraction.Types.UNBAN,
            reason=reason
        )
        raise CommandSuccess('unbanned user with id `{}`'.format(user))

    @Plugin.command('archive', group='infractions', level=CommandLevels.ADMIN)
    def infractions_archive(self, event):
        user = User.alias()
        actor = User.alias()

        q = Infraction.select(Infraction, user, actor).join(
            user,
            on=((Infraction.user_id == user.user_id).alias('user'))
        ).switch(Infraction).join(
            actor,
            on=((Infraction.actor_id == actor.user_id).alias('actor'))
        ).where(Infraction.guild_id == event.guild.id)

        buff = StringIO()
        w = csv.writer(buff)

        for inf in q:
            w.writerow([
                inf.id,
                inf.user_id,
                unicode(inf.user).encode('utf-8'),
                inf.actor_id,
                unicode(inf.actor).encode('utf-8'),
                unicode({i.index: i for i in Infraction.Types.attrs}[inf.type_]).encode('utf-8'),
                unicode(inf.reason).encode('utf-8'),
            ])

        event.msg.reply('Ok, here is an archive of all infractions', attachments=[
            ('infractions.csv', buff.getvalue())
        ])

    def find_infraction(self, event, infraction):
        if isinstance(infraction, int) or infraction.isdigit():
            try:
                return Infraction.get(id=infraction)
            except Infraction.DoesNotExist:
                return

        infraction = infraction.lower()
        q = (Infraction.guild_id == event.guild.id)
        if infraction in ('ml', 'mylatest'):
            q &= (Infraction.actor_id == event.author.id)
        elif infraction not in ('l', 'latest'):
            raise CommandFail('invalid argument: must be an infraction ID, `l/latest`, or `ml/mylatest`')

        try:
            return Infraction.select(Infraction).where(q).order_by(Infraction.created_at.desc()).limit(1).get()
        except Infraction.DoesNotExist:
            return

    @Plugin.command('info', '<infraction:int>', group='infractions', level=CommandLevels.MOD)
    def infraction_info(self, event, infraction):
        try:
            user = User.alias()
            actor = User.alias()

            infraction = Infraction.select(Infraction, user, actor).join(
                user,
                on=((Infraction.user_id == user.user_id).alias('user'))
            ).switch(Infraction).join(
                actor,
                on=((Infraction.actor_id == actor.user_id).alias('actor'))
            ).where(
                    (Infraction.id == infraction) &
                    (Infraction.guild_id == event.guild.id)
            ).get()
        except Infraction.DoesNotExist:
            raise CommandFail('cannot find an infraction with ID `{}`'.format(infraction))

        type_ = {i.index: i for i in Infraction.Types.attrs}[infraction.type_]
        embed = MessageEmbed()

        if type_ in (Infraction.Types.MUTE, Infraction.Types.TEMPMUTE, Infraction.Types.TEMPROLE, Infraction.Types.WARNING):
            embed.color = 0xfdfd96
        elif type_ in (Infraction.Types.KICK, Infraction.Types.SOFTBAN):
            embed.color = 0xffb347
        else:
            embed.color = 0xff6961

        embed.title = str(type_).title()
        embed.set_thumbnail(url=infraction.user.get_avatar_url())
        embed.add_field(name='User', value=unicode(infraction.user), inline=True)
        embed.add_field(name='Moderator', value=unicode(infraction.actor), inline=True)
        embed.add_field(name='ID', value=unicode(infraction.id), inline=True)
        embed.add_field(name='Active', value='yes' if infraction.active else 'no', inline=True)
        if infraction.active and infraction.expires_at:
            embed.add_field(name='Expires in', value=humanize_duration(infraction.expires_at - datetime.utcnow()))
        embed.add_field(name='Reason', value=infraction.reason or '*Not specified*', inline=False)
        embed.timestamp = infraction.created_at.isoformat()
        event.msg.reply('', embed=embed)

    @Plugin.command('search', '[query:user|str...]', group='infractions', level=CommandLevels.MOD)
    def infraction_search(self, event, query=None):
        q = (Infraction.guild_id == event.guild.id)

        if query and isinstance(query, list) and isinstance(query[0], DiscoUser):
            query = query[0].id
        elif query:
            query = u' '.join(map(unicode, query))

        if query and (isinstance(query, int) or query.isdigit()):
            q &= (
                (Infraction.id == int(query)) |
                (Infraction.user_id == int(query)) |
                (Infraction.actor_id == int(query)))
        elif query:
            q &= (Infraction.reason ** query)

        user = User.alias()
        actor = User.alias()

        infractions = Infraction.select(Infraction, user, actor).join(
            user,
            on=((Infraction.user_id == user.user_id).alias('user'))
        ).switch(Infraction).join(
            actor,
            on=((Infraction.actor_id == actor.user_id).alias('actor'))
        ).where(q).order_by(Infraction.created_at.desc()).limit(8)

        if not infractions:
            return event.msg.reply('No infractions found for the given query.')

        tbl = MessageTable()

        tbl.set_header('ID', 'Created', 'Type', 'User', 'Moderator', 'Active', 'Reason')
        for inf in infractions:
            type_ = {i.index: i for i in Infraction.Types.attrs}[inf.type_]
            reason = inf.reason or ''
            if len(reason) > 256:
                reason = reason[:256] + '...'

            if inf.active:
                active = 'yes'
                if inf.expires_at:
                    active += ' (expires in {})'.format(humanize.naturaldelta(inf.expires_at - datetime.utcnow()))
            else:
                active = 'no'

            old_size = tbl.size_index.copy()

            tbl.add(
                inf.id,
                inf.created_at.isoformat(),
                str(type_),
                unicode(inf.user),
                unicode(inf.actor),
                active,
                clamp(reason, 128)
            )

            if len(tbl.compile()) > 2000:
                tbl.entries.pop()
                tbl.size_index = old_size.copy()
                break

        event.msg.reply(tbl.compile())

    # Thanks OGNovuh / Terminator966
    @Plugin.command('recent', aliases=['latest'], group='infractions', level=CommandLevels.MOD)
    def infractions_recent(self, event):
        user = User.alias()
        actor = User.alias()

        infraction = Infraction.select(Infraction, user, actor).join(
            user,
            on=((Infraction.user_id == user.user_id).alias('user'))
        ).switch(Infraction).join(
            actor,
            on=((Infraction.actor_id == actor.user_id).alias('actor'))
        ).where(
            (Infraction.guild_id == event.guild.id)
        ).order_by(Infraction.created_at.desc()).limit(1).get()
        
        type_ = {i.index: i for i in Infraction.Types.attrs}[infraction.type_]
        embed = MessageEmbed()

        if type_ in (Infraction.Types.MUTE, Infraction.Types.TEMPMUTE, Infraction.Types.TEMPROLE, Infraction.Types.WARNING):
            embed.color = 0xfdfd96
        elif type_ in (Infraction.Types.KICK, Infraction.Types.SOFTBAN):
            embed.color = 0xffb347
        else:
            embed.color = 0xff6961

        embed.title = str(type_).title()
        embed.set_thumbnail(url=infraction.user.get_avatar_url())
        embed.add_field(name='User', value=unicode(infraction.user), inline=True)
        embed.add_field(name='Moderator', value=unicode(infraction.actor), inline=True)
        embed.add_field(name='ID', value=unicode(infraction.id), inline=True)
        embed.add_field(name='Active', value='yes' if infraction.active else 'no', inline=True)
        if infraction.active and infraction.expires_at:
            embed.add_field(name='Expires in', value=humanize_duration(infraction.expires_at - datetime.utcnow()))
        embed.add_field(name='Reason', value=infraction.reason or '*Not specified*', inline=False)
        embed.timestamp = infraction.created_at.isoformat()
        event.msg.reply('', embed=embed)

    # Thanks OGNovuh / Terminator966
    @Plugin.command('delete', '<infraction:int>', group='infractions', aliases=['remove', 'del', 'rem', 'rm', 'rmv'], level=-1)
    def infraction_delete(self, event, infraction):
        try:
            inf = Infraction.select(Infraction).where(
                (Infraction.id == infraction)
            ).get()
        except Infraction.DoesNotExist:
            raise CommandFail('cannot find an infraction with ID `{}`'.format(infraction))

        msg = event.msg.reply('Ok, delete infraction #{}?'.format(infraction))
        msg.chain(False).\
            add_reaction(GREEN_TICK_EMOJI).\
            add_reaction(RED_TICK_EMOJI)

        try:
            mra_event = self.wait_for_event(
                'MessageReactionAdd',
                message_id=msg.id,
                conditional=lambda e: (
                    e.emoji.id in (GREEN_TICK_EMOJI_ID, RED_TICK_EMOJI_ID) and
                    e.user_id == event.author.id
                )).get(timeout=10)
        except gevent.Timeout:
            return
        finally:
            msg.delete()

        if mra_event.emoji.id != GREEN_TICK_EMOJI_ID:
            return
        
        inf.delete_instance()
        self.queue_infractions()

        raise CommandSuccess('deleted infraction #{}.'.format(infraction))

    @Plugin.command('duration', '<infraction:int|str> <duration:str>', group='infractions', level=CommandLevels.MOD)
    def infraction_duration(self, event, infraction, duration):
        inf = self.find_infraction(event, infraction)

        if inf.actor_id != event.author.id and event.user_level < CommandLevels.ADMIN:
            raise CommandFail('only administrators can modify the duration of infractions created by other moderators')

        if not inf.active:
            raise CommandFail('that infraction is not active and cannot be updated')

        expires_dt = parse_duration(duration, inf.created_at)

        converted = False
        if inf.type_ in [Infraction.Types.MUTE.index, Infraction.Types.BAN.index]:
            inf.type_ = (
                Infraction.Types.TEMPMUTE
                if inf.type_ == Infraction.Types.MUTE.index else
                Infraction.Types.TEMPBAN
            )
            converted = True
        elif inf.type_ not in [
                Infraction.Types.TEMPMUTE.index,
                Infraction.Types.TEMPBAN.index,
                Infraction.Types.TEMPROLE.index]:
            raise CommandFail('cannot set the duration for that type of infraction')

        inf.expires_at = expires_dt
        inf.save()
        self.queue_infractions()

        if converted:
            raise CommandSuccess('ok, I\'ve made that infraction temporary, it will now expire on {}'.format(
                inf.expires_at.isoformat()
            ))
        else:
            raise CommandSuccess('ok, I\'ve updated that infractions duration, it will now expire on {}'.format(
                inf.expires_at.isoformat()
            ))

    @Plugin.command('reason', '<infraction:int|str> <reason:str...>', level=CommandLevels.MOD)
    @Plugin.command('reason', '<infraction:int|str> <reason:str...>', group='infractions', level=CommandLevels.MOD)
    def reason(self, event, infraction, reason):
        inf = self.find_infraction(event, infraction)

        if inf is None or inf.guild_id != event.guild.id:
            event.msg.reply('Unknown infraction ID')
            return

        if not inf.actor_id:
            inf.actor_id = event.author.id

        if inf.actor_id != event.author.id and event.user_level < event.config.reason_edit_level:
            raise CommandFail('you do not have the permissions required to edit other moderators infractions')

        inf.reason = reason
        inf.save()

        raise CommandSuccess('I\'ve updated the reason for infraction #{}'.format(inf.id))

    # Full credit goes to: Xenthys
    @Plugin.command('roles', '[pattern:str...]', level=CommandLevels.MOD)
    def roles(self, event, pattern=None):
        buff = ''
        g = event.guild

        total = {}
        members = g.members.values()
        for member in members:
            for role_id in member.roles:
                total[role_id] = total.get(role_id, 0) + 1

        roles = g.roles.values()
        roles = sorted(roles, key=lambda r: r.position, reverse=True)
        for role in roles:
            if pattern and role.name.lower().find(pattern.lower()) == -1: continue
            role_members = total.get(role.id, 0) if role.id != g.id else len(g.members)
            role = S(u'{} - {} ({} member{})\n'.format(
                role.id,
                role.name,
                role_members,
                's' if role_members != 1 else ''
            ), escape_codeblocks=True)
            if len(role) + len(buff) > 1990:
                event.msg.reply(u'```dns\n{}```'.format(buff))
                buff = ''
            buff += role

        if not buff:
            return

        return event.msg.reply(u'```dns\n{}```'.format(buff))

    @Plugin.command('restore', '<user:user>', level=CommandLevels.MOD, group='backups')
    def restore(self, event, user):
        member = event.guild.get_member(user)
        if member:
            self.restore_user(event, member)
        else:
            raise CommandFail('invalid user')

    @Plugin.command('clear', '<user_id:snowflake>', level=CommandLevels.MOD, group='backups')
    def backups_clear(self, event, user_id):
        deleted = bool(GuildMemberBackup.delete().where(
            (GuildMemberBackup.user_id == user_id) &
            (GuildMemberBackup.guild_id == event.guild.id)
        ).execute())

        if deleted:
            event.msg.reply(':ok_hand: I\'ve cleared the member backup for that user')
        else:
            raise CommandFail('I couldn\'t find any member backups for that user')

    def can_act_on(self, event, victim_id, throw=True):
        if event.author.id == victim_id:
            if not throw:
                return False
            raise CommandFail('cannot execute that action on yourself')

        victim_level = self.bot.plugins.get('CorePlugin').get_level(event.guild, victim_id)
        if event.user_level <= victim_level:
            if not throw:
                return False
            raise CommandFail('invalid permissions')
        
        perms = event.guild.get_permissions(self.state.me)
        if not perms.ban_members and not perms.administrator:
            if not throw:
                return False
            raise CommandFail('missing permissions')
        
        if hasattr(event, 'action') and event.action in ('kick', 'ban'):
            member_me = event.guild.get_member(self.state.me)
            member = event.guild.get_member(victim_id)
            if member.roles:
                highest_role_me = sorted(
                    [member_me.guild.roles.get(r) for r in member_me.roles],
                    key=lambda r: r.position,
                    reverse=True)
                highest_role = sorted(
                    [event.guild.roles.get(r) for r in member.roles],
                    key=lambda i: i.position,
                    reverse=True)
                if member.owner or (highest_role[0].position >= highest_role_me[0].position):
                    if not throw:
                        return False
                    raise CommandFail('cannot execute that action on that member')

        return True

    @Plugin.command('mute', '<user:user|snowflake> [reason:str...]', level=CommandLevels.MOD)
    @Plugin.command('tempmute', '<user:user|snowflake> <duration:str> [reason:str...]', level=CommandLevels.MOD)
    def tempmute(self, event, user, duration=None, reason=None):
        if not duration and reason:
            duration = parse_duration(reason.split(' ')[0], safe=True)
            if duration:
                if ' ' in reason:
                    reason = reason.split(' ', 1)[-1]
                else:
                    reason = None
        elif duration:
            duration = parse_duration(duration)

        member = event.guild.get_member(user)
        if member:
            self.can_act_on(event, member.id)
            if not event.config.mute_role:
                raise CommandFail('mute is not setup on this server')

            if event.config.mute_role in member.roles:
                raise CommandFail(u'{} is already muted'.format(member.user))

            # If we have a duration set, this is a tempmute
            if duration:
                # Create the infraction
                try:
                    self.send_infraction_dm(event, member.id, 'tempmute', event.msg.guild.name, unicode(u'{}#{}'.format(event.author.username, event.author.discriminator)).encode('utf-8'), reason, duration)
                except APIException:
                    pass
                Infraction.tempmute(self, event, member, reason, duration)
                self.queue_infractions()

                if event.config.confirm_actions:
                    event.msg.reply(maybe_string(
                        reason,
                        u':ok_hand: {u} is now muted for {t} (`{o}`)',
                        u':ok_hand: {u} is now muted for {t}',
                        u=member.user,
                        t=humanize_duration(duration - datetime.utcnow()),
                    ))
            else:
                existed = False
                # If the user is already muted check if we can take this from a temp
                #  to perma mute.
                if event.config.mute_role in member.roles:
                    existed = Infraction.clear_active(event, member.id, [Infraction.Types.TEMPMUTE])

                    # The user is 100% muted and not tempmuted at this point, so lets bail
                    if not existed:
                        raise CommandFail(u'{} is already muted'.format(member.user))

                try:
                    self.send_infraction_dm(event, member.id, 'mute', event.msg.guild.name, unicode(u'{}#{}'.format(event.author.username, event.author.discriminator)).encode('utf-8'), reason)
                except APIException:
                    pass
                Infraction.mute(self, event, member, reason)

                if event.config.confirm_actions:
                    existed = u' [was temp-muted]' if existed else ''
                    event.msg.reply(maybe_string(
                        reason,
                        u':ok_hand: {u} is now muted (`{o}`)' + existed,
                        u':ok_hand: {u} is now muted' + existed,
                        u=member.user,
                    ))
        else:
            raise CommandFail('invalid user')

    @Plugin.command(
        'temprole',
        '<user:user|snowflake> <role:snowflake|str> <duration:str> [reason:str...]',
        level=CommandLevels.MOD)
    def temprole(self, event, user, role, duration, reason=None):
        member = event.guild.get_member(user)
        if not member:
            raise CommandFail('invalid user')

        self.can_act_on(event, member.id)
        role_id = role if isinstance(role, (int, long)) else event.config.role_aliases.get(role.lower())
        if not role_id or role_id not in event.guild.roles:
            raise CommandFail('invalid or unknown role')

        if role_id in member.roles:
            raise CommandFail(u'{} is already in that role'.format(member.user))

        expire_dt = parse_duration(duration)
        Infraction.temprole(self, event, member, role_id, reason, expire_dt)
        self.queue_infractions()

        if event.config.confirm_actions:
            event.msg.reply(maybe_string(
                reason,
                u':ok_hand: {u} is now in the {r} role for {t} (`{o}`)',
                u':ok_hand: {u} is now in the {r} role for {t}',
                r=event.guild.roles[role_id].name,
                u=member.user,
                t=humanize_duration(expire_dt - datetime.utcnow()),
            ))

    @Plugin.command('unmute', '<user:user|snowflake>', level=CommandLevels.MOD)
    def unmute(self, event, user, reason=None):
        # TOOD: eventually we should pull the role from the GuildMemberBackup if they arent in server
        member = event.guild.get_member(user)

        if member:
            self.can_act_on(event, member.id)
            if not event.config.mute_role:
                raise CommandFail('mute is not setup on this server')

            if event.config.mute_role not in member.roles:
                raise CommandFail(u'{} is not muted'.format(member.user))

            Infraction.clear_active(event, member.id, [Infraction.Types.MUTE, Infraction.Types.TEMPMUTE])

            self.call(
                'ModLogPlugin.create_debounce',
                event,
                ['GuildMemberUpdate'],
                role_id=event.config.mute_role,
            )

            member.remove_role(event.config.mute_role)

            self.call(
                'ModLogPlugin.log_action_ext',
                Actions.MEMBER_UNMUTED,
                event.guild.id,
                member=member,
                actor=unicode(event.author) if event.author.id != member.id else 'Automatic',
            )

            if event.config.confirm_actions:
                event.msg.reply(u':ok_hand: {} is now unmuted'.format(member.user))
        else:
            raise CommandFail('invalid user')

    @Plugin.command('kick', '<user:user|snowflake> [reason:str...]', level=CommandLevels.MOD)
    def kick(self, event, user, reason=None):
        event.action = 'kick'
        member = event.guild.get_member(user)
        if member:
            self.can_act_on(event, member.id)
            try:
                self.send_infraction_dm(event, member.id, 'kick', event.msg.guild.name, unicode(u'{}#{}'.format(event.author.username, event.author.discriminator)).encode('utf-8'), reason)
            except APIException:
                pass
            Infraction.kick(self, event, member, reason)
            if event.config.confirm_actions:
                event.msg.reply(maybe_string(
                    reason,
                    u':ok_hand: kicked {u} (`{o}`)',
                    u':ok_hand: kicked {u}',
                    u=member.user,
                ))
        else:
            raise CommandFail('invalid user')

    @Plugin.command('mkick', parser=True, level=CommandLevels.MOD)
    @Plugin.parser.add_argument('users', type=long, nargs='+')
    @Plugin.parser.add_argument('-r', '--reason', default='', help='reason for modlog')
    #@Plugin.parser.add_argument('-c', '--clean', type=int, default=0, help='days of messages to clean')
    def mkick(self, event, args):
        event.action = 'kick'
        members = []; cannot = []
        users = list(set(args.users))
        for user_id in users:
            member = event.guild.get_member(user_id)
            if member and self.can_act_on(event, member.id, throw=False):
                members.append(member)
            else:
                cannot.append(user_id)

        if not members:
            raise CommandFail('invalid user{}'.format('s' if len(users)>1 else ''))

        nope = ''
        if cannot:
            nope = '\n*Ignoring {} user{} who cannot be kicked.*'.format(len(cannot), 's' if len(cannot)>1 else '')
        msg = event.msg.reply(u'Ok, kick {} user{} for `{}`?{}'.format(
            len(members), 's' if len(members)>1 else '', args.reason or 'no reason', nope
        ))
        msg.chain(False).add_reaction(GREEN_TICK_EMOJI).add_reaction(RED_TICK_EMOJI)

        try:
            mra_event = self.wait_for_event(
                'MessageReactionAdd',
                message_id=msg.id,
                conditional=lambda e: (
                    e.emoji.id in (GREEN_TICK_EMOJI_ID, RED_TICK_EMOJI_ID) and
                    e.user_id == event.author.id
                )).get(timeout=10)
        except gevent.Timeout:
            return
        finally:
            msg.delete()

        if mra_event.emoji.id != GREEN_TICK_EMOJI_ID:
            return

        failed = []
        succeeded = []
        for member in members:
            try:
                self.send_infraction_dm(event, member.id if hasattr(member, 'id') else member, 'kick', event.msg.guild.name, unicode(u'{}#{}'.format(event.author.username, event.author.discriminator)).encode('utf-8'), args.reason)
                Infraction.kick(self, event, member, args.reason)
                succeeded.append(member)
            except APIException:
                if not isinstance(member, (int, long)):
                    User.from_disco_user(member.user)
                    member = member.user.id
                failed.append(member)

        members = len(members)
        total = len(succeeded)
        if total == 0:
            raise CommandFail('could not kick any member')

        #self.perform_cleanup(succeeded, args.clean, event.guild.id)

        reply = 'kicked {}/{} member{}'.format(total, members, 's' if members>1 else '')
        if failed:
            reply += '\nThe following ID{} could not be kicked: `{}`'.format(
                's' if len(failed)>1 else '',
                '`, `'.join([str(id) for id in failed])
            )

        raise CommandSuccess(reply)

    @Plugin.command('ban', '<user:user|snowflake> [reason:str...]', level=CommandLevels.MOD)
    @Plugin.command('forceban', '<user:snowflake> [reason:str...]', level=CommandLevels.MOD)
    def ban(self, event, user, reason=None):
        if isinstance(user, (int, long)):
            user_id = user
            self.can_act_on(event, user)
        else:
            user_id = user.id
            member = event.guild.get_member(user)
            if member:
                user = member
                event.action = 'ban'
                self.can_act_on(event, user_id)
            else:
                user = user_id

        try:
            self.send_infraction_dm(
                event,
                user_id,
                'ban',
                event.msg.guild.name,
                unicode(u'{}#{}'.format(event.author.username, event.author.discriminator)).encode('utf-8'),
                reason,
            )
        except APIException:
            pass

        try:
            Infraction.ban(self, event, user, reason, guild=event.guild)
        except APIException:
            raise CommandFail('invalid user')

        if event.config.confirm_actions:
            event.msg.reply(maybe_string(
                reason,
                u':ok_hand: banned {u} (`{o}`)',
                u':ok_hand: banned {u}',
                u=user.user if isinstance(user, GuildMember) else user,
            ))

    @Plugin.command('mban', parser=True, level=CommandLevels.MOD)
    @Plugin.parser.add_argument('users', type=long, nargs='+')
    @Plugin.parser.add_argument('-r', '--reason', default='', help='reason for modlog')
    @Plugin.parser.add_argument('-h', '--hide', action='store_true', help='hide names like forceban')
    #@Plugin.parser.add_argument('-c', '--clean', type=int, default=0, help='days of messages to clean')
    def mban(self, event, args):
        members = []; cannot = []
        users = list(set(args.users))
        for user_id in users:
            if self.can_act_on(event, user_id, throw=False):
                member = None if args.hide else event.guild.get_member(user_id)
                members.append(member if member else user_id)
            else:
                cannot.append(user_id)

        if not members:
            raise CommandFail('invalid user{}'.format('s' if len(users)>1 else ''))

        nope = ''
        if cannot:
            nope = '\n*Ignoring {} user{} who cannot be banned.*'.format(len(cannot), 's' if len(cannot)>1 else '')
        msg = event.msg.reply(u'Ok, ban {} user{} for `{}`?{}'.format(
            len(members), 's' if len(members)>1 else '', args.reason or 'no reason', nope
        ))
        msg.chain(False).add_reaction(GREEN_TICK_EMOJI).add_reaction(RED_TICK_EMOJI)

        try:
            mra_event = self.wait_for_event(
                'MessageReactionAdd',
                message_id=msg.id,
                conditional=lambda e: (
                    e.emoji.id in (GREEN_TICK_EMOJI_ID, RED_TICK_EMOJI_ID) and
                    e.user_id == event.author.id
                )).get(timeout=10)
        except gevent.Timeout:
            return
        finally:
            msg.delete()

        if mra_event.emoji.id != GREEN_TICK_EMOJI_ID:
            return

        failed = []
        succeeded = []
        for member in members:
            try:
                self.send_infraction_dm(event, member.id if hasattr(member, 'id') else member, 'ban', event.msg.guild.name, unicode(u'{}#{}'.format(event.author.username, event.author.discriminator)).encode('utf-8'), args.reason)
                Infraction.ban(self, event, member, args.reason, guild=event.guild)
                succeeded.append(member)
            except APIException:
                if not isinstance(member, (int, long)):
                    User.from_disco_user(member.user)
                    member = member.user.id
                failed.append(member)

        members = len(members)
        total = len(succeeded)
        if total == 0:
            raise CommandFail('could not ban any user')

        #self.perform_cleanup(succeeded, args.clean, event.guild.id)

        reply = 'banned {}/{} user{}'.format(total, members, 's' if members>1 else '')
        if failed:
            reply += '\nThe following ID{} could not be banned: `{}`'.format(
                's' if len(failed)>1 else '',
                '`, `'.join([str(id) for id in failed])
            )

        raise CommandSuccess(reply)

    @Plugin.command('softban', '<user:user|snowflake> [reason:str...]', level=CommandLevels.MOD)
    def softban(self, event, user, reason=None):
        """
        Ban then unban a user from the server (with an optional reason for the modlog)
        """
        event.action = 'kick'
        member = event.guild.get_member(user)
        if member:
            self.can_act_on(event, member.id)
            try:
                self.send_infraction_dm(event, member.id, 'kick', event.msg.guild.name, unicode(u'{}#{}'.format(event.author.username, event.author.discriminator)).encode('utf-8'), reason)
            except APIException:
                pass
            Infraction.softban(self, event, member, reason)
            if event.config.confirm_actions:
                event.msg.reply(maybe_string(
                    reason,
                    u':ok_hand: soft-banned {u} (`{o}`)',
                    u':ok_hand: soft-banned {u}',
                    u=member.user,
                ))
        else:
            raise CommandFail('invalid user')

    @Plugin.command('tempban', '<user:user|snowflake> <duration:str> [reason:str...]', level=CommandLevels.MOD)
    def tempban(self, event, duration, user, reason=None):
        event.action = 'ban'
        member = event.guild.get_member(user)
        if member:
            self.can_act_on(event, member.id)
            expires_dt = parse_duration(duration)
            try:
                self.send_infraction_dm(event, member.id, 'tempban', event.msg.guild.name, unicode(u'{}#{}'.format(event.author.username, event.author.discriminator)).encode('utf-8'), reason, expires_dt)
            except APIException:
                pass
            Infraction.tempban(self, event, member, reason, expires_dt)
            self.queue_infractions()
            if event.config.confirm_actions:
                event.msg.reply(maybe_string(
                    reason,
                    u':ok_hand: temp-banned {u} for {t} (`{o}`)',
                    u':ok_hand: temp-banned {u} for {t}',
                    u=member.user,
                    t=humanize_duration(expires_dt - datetime.utcnow()),
                ))
        else:
            raise CommandFail('invalid user')

    @Plugin.command('warn', '<user:user|snowflake> [reason:str...]', level=CommandLevels.MOD)
    def warn(self, event, user, reason=None):
        member = None

        member = event.guild.get_member(user)
        if member:
            self.can_act_on(event, member.id)
            try:
                self.send_infraction_dm(event, member.id, 'warn', event.msg.guild.name, unicode(u'{}#{}'.format(event.author.username, event.author.discriminator)).encode('utf-8'), reason)
            except APIException:
                pass
            Infraction.warn(self, event, member, reason, guild=event.guild)
        else:
            raise CommandFail('invalid user')

        if event.config.confirm_actions:
            event.msg.reply(maybe_string(
                reason,
                u':ok_hand: warned {u} (`{o}`)',
                u':ok_hand: warned {u}',
                u=member.user if member else user,
            ))

    @Plugin.command('here', '[size:int]', level=CommandLevels.MOD, context={'mode': 'all'}, group='archive')
    @Plugin.command('all', '[size:int]', level=CommandLevels.MOD, context={'mode': 'all'}, group='archive')
    @Plugin.command(
        'user',
        '<user:user|snowflake> [size:int]',
        level=CommandLevels.MOD,
        context={'mode': 'user'},
        group='archive')
    @Plugin.command(
        'channel',
        '<channel:channel|snowflake> [size:int]',
        level=CommandLevels.MOD,
        context={'mode': 'channel'},
        group='archive')
    def archive(self, event, size=50, mode=None, user=None, channel=None):
        if size < 1 or size > 15000:
            raise CommandFail('too many messages must be between 1-15000')

        q = Message.select(Message.id).join(User).order_by(Message.id.desc()).limit(size)

        if mode in ('all', 'channel'):
            cid = event.channel.id
            if channel:
                cid = channel if isinstance(channel, (int, long)) else channel.id
            channel = event.guild.channels.get(cid)
            if not channel:
                raise CommandFail('channel not found')
            perms = channel.get_permissions(event.author)
            if not (perms.administrator or perms.read_messages):
                raise CommandFail('invalid permissions')
            q = q.where(Message.channel_id == cid)
        else:
            user_id = user if isinstance(user, (int, long)) else user.id
            if event.author.id != user_id:
                self.can_act_on(event, user_id)
            q = q.where(
                (Message.author_id == user_id) &
                (Message.guild_id == event.guild.id)
            )

        archive = MessageArchive.create_from_message_ids([i.id for i in q])
        event.msg.reply('OK, archived {} messages at {}'.format(len(archive.message_ids), archive.url))

    @Plugin.command('extend', '<archive_id:str> <duration:str>', level=CommandLevels.MOD, group='archive')
    def archive_extend(self, event, archive_id, duration):
        try:
            archive = MessageArchive.get(archive_id=archive_id)
        except MessageArchive.DoesNotExist:
            raise CommandFail('invalid message archive id')

        archive.expires_at = parse_duration(duration)

        MessageArchive.update(
            expires_at=parse_duration(duration)
        ).where(
            (MessageArchive.archive_id == archive_id)
        ).execute()

        raise CommandSuccess('duration of archive {} has been extended (<{}>)'.format(
            archive_id,
            archive.url,
        ))

    @Plugin.command('clean cancel', level=CommandLevels.MOD)
    def clean_cacnel(self, event):
        if event.channel.id not in self.cleans:
            raise CommandFail('no clean is running in this channel')

        self.cleans[event.channel.id].kill()
        event.msg.reply('Ok, the running clean was cancelled')

    @Plugin.command('clean all', '[size:int]', level=CommandLevels.MOD, context={'mode': 'all'})
    @Plugin.command('clean bots', '[size:int]', level=CommandLevels.MOD, context={'mode': 'bots'})
    @Plugin.command('clean user', '<user:user> [size:int]', level=CommandLevels.MOD, context={'mode': 'user'})
    def clean(self, event, user=None, size=25, typ=None, mode='all'):
        """
        Removes messages
        """
        if size < 1 or size > 10000:
            raise CommandFail('too many messages must be between 1-10000')

        if event.channel.id in self.cleans:
            raise CommandFail('a clean is already running on this channel')

        query = Message.select(Message.id).where(
            (Message.deleted >> False) &
            (Message.channel_id == event.channel.id) &
            (Message.timestamp > (datetime.utcnow() - timedelta(days=13)))
        ).join(User).order_by(Message.timestamp.desc()).limit(size)

        if mode == 'bots':
            query = query.where((User.bot >> True))
        elif mode == 'user':
            query = query.where((User.user_id == user.id))

        messages = [i[0] for i in query.tuples()]

        if len(messages) == 1:
            return self.client.api.channels_messages_delete(event.channel.id, messages[0])

        if len(messages) > 100:
            msg = event.msg.reply('Woah there, that will delete a total of {} messages, please confirm.'.format(
                len(messages)
            ))

            msg.chain(False).\
                add_reaction(GREEN_TICK_EMOJI).\
                add_reaction(RED_TICK_EMOJI)

            try:
                mra_event = self.wait_for_event(
                    'MessageReactionAdd',
                    message_id=msg.id,
                    conditional=lambda e: (
                        e.emoji.id in (GREEN_TICK_EMOJI_ID, RED_TICK_EMOJI_ID) and
                        e.user_id == event.author.id
                    )).get(timeout=10)
            except gevent.Timeout:
                return
            finally:
                msg.delete()

            if mra_event.emoji.id != GREEN_TICK_EMOJI_ID:
                return

            event.msg.reply(':wastebasket: Ok please hold on while I delete those messages...').after(5).delete()

        def run_clean():
            for chunk in chunks(messages, 100):
                self.client.api.channels_messages_delete_bulk(event.channel.id, chunk)

        self.cleans[event.channel.id] = gevent.spawn(run_clean)
        self.cleans[event.channel.id].join()
        del self.cleans[event.channel.id]

    @Plugin.command(
        'add',
        '<user:user> <role:str> [reason:str...]',
        level=CommandLevels.MOD,
        context={'mode': 'add'},
        group='role')
    @Plugin.command(
        'rmv',
        '<user:user> <role:str> [reason:str...]',
        level=CommandLevels.MOD,
        context={'mode': 'remove'},
        group='role')
    @Plugin.command('remove',
        '<user:user> <role:str> [reason:str...]',
        level=CommandLevels.MOD,
        context={'mode': 'remove'},
        group='role')
    def role_add(self, event, user, role, reason=None, mode=None):
        role_obj = None

        if role.isdigit() and int(role) in event.guild.roles.keys():
            role_obj = event.guild.roles[int(role)]
        elif role.lower() in event.config.role_aliases:
            role_obj = event.guild.roles.get(event.config.role_aliases[role.lower()])
        else:
            # First try exact match
            exact_matches = [i for i in event.guild.roles.values() if i.name.lower().replace(' ', '') == role.lower()]
            if len(exact_matches) == 1:
                role_obj = exact_matches[0]
            else:
                # Otherwise we fuzz it up
                rated = sorted([
                    (fuzz.partial_ratio(role, r.name.replace(' ', '')), r) for r in event.guild.roles.values()
                ], key=lambda i: i[0], reverse=True)

                if rated[0][0] > 40:
                    if len(rated) == 1:
                        role_obj = rated[0][1]
                    elif rated[0][0] - rated[1][0] > 20:
                        role_obj = rated[0][1]

        if not role_obj:
            raise CommandFail('too many matches for that role, try something more exact or the role ID')

        author_member = event.guild.get_member(event.author)
        highest_role = sorted(
            [event.guild.roles.get(r) for r in author_member.roles],
            key=lambda i: i.position,
            reverse=True)
        if not author_member.owner and (not highest_role or highest_role[0].position <= role_obj.position):
            raise CommandFail('you can only {} roles that are ranked lower than your highest role'.format(mode))

        member = event.guild.get_member(user)
        if not member:
            raise CommandFail('invalid member')

        self.can_act_on(event, member.id)

        if mode == 'add' and role_obj.id in member.roles:
            raise CommandFail(u'{} already has the {} role'.format(member, role_obj.name))
        elif mode == 'remove' and role_obj.id not in member.roles:
            raise CommandFail(u'{} doesn\'t have the {} role'.format(member, role_obj.name))

        self.call(
            'ModLogPlugin.create_debounce',
            event,
            ['GuildMemberUpdate'],
            role_id=role_obj.id,
        )

        if mode == 'add':
            member.add_role(role_obj.id)
        else:
            member.remove_role(role_obj.id)

        self.call(
            'ModLogPlugin.log_action_ext',
            (Actions.MEMBER_ROLE_ADD if mode == 'add' else Actions.MEMBER_ROLE_REMOVE),
            event.guild.id,
            member=member,
            role=role_obj,
            actor=unicode(event.author),
            reason=reason or 'no reason',
        )

        event.msg.reply(u':ok_hand: {} role {} {} {}'.format(
            'added' if mode == 'add' else 'removed',
            role_obj.name,
            'to' if mode == 'add' else 'from',
            member
        ))

    @Plugin.command('stats', '<user:user>', level=CommandLevels.MOD)
    def msgstats(self, event, user):
        # Query for the basic aggregate message statistics
        message_stats = Message.select(
            fn.Count('*'),
            fn.Sum(fn.char_length(Message.content)),
            fn.Sum(fn.array_length(Message.emojis, 1)),
            fn.Sum(fn.array_length(Message.mentions, 1)),
            fn.Sum(fn.array_length(Message.attachments, 1)),
        ).where(
            (Message.author_id == user.id)
        ).tuples().async()

        reactions_given = Reaction.select(
            fn.Count('*'),
            Reaction.emoji_id,
            Reaction.emoji_name,
        ).join(
            Message,
            on=(Message.id == Reaction.message_id)
        ).where(
            (Reaction.user_id == user.id)
        ).group_by(
            Reaction.emoji_id, Reaction.emoji_name
        ).order_by(fn.Count('*').desc()).tuples().async()

        # Query for most used emoji
        emojis = Message.raw('''
            SELECT gm.emoji_id, gm.name, count(*)
            FROM (
                SELECT unnest(emojis) as id
                FROM messages
                WHERE author_id=%s
            ) q
            JOIN guild_emojis gm ON gm.emoji_id=q.id
            GROUP BY 1, 2
            ORDER BY 3 DESC
            LIMIT 1
        ''', (user.id, )).tuples().async()

        deleted = Message.select(
            fn.Count('*')
        ).where(
            (Message.author_id == user.id) &
            (Message.deleted == 1)
        ).tuples().async()

        wait_many(message_stats, reactions_given, emojis, deleted, timeout=10)

        # If we hit an exception executing the core query, throw an exception
        if message_stats.exception:
            message_stats.get()

        q = message_stats.value[0]
        embed = MessageEmbed()
        embed.fields.append(
            MessageEmbedField(name='Total Messages Sent', value=q[0] or '0', inline=True))
        embed.fields.append(
            MessageEmbedField(name='Total Characters Sent', value=q[1] or '0', inline=True))

        if deleted.value:
            embed.fields.append(
                MessageEmbedField(name='Total Deleted Messages', value=deleted.value[0][0], inline=True))
        embed.fields.append(
            MessageEmbedField(name='Total Custom Emojis', value=q[2] or '0', inline=True))
        embed.fields.append(
            MessageEmbedField(name='Total Mentions', value=q[3] or '0', inline=True))
        embed.fields.append(
            MessageEmbedField(name='Total Attachments', value=q[4] or '0', inline=True))

        if reactions_given.value:
            reactions_given = reactions_given.value

            embed.fields.append(
                MessageEmbedField(name='Total Reactions', value=sum(i[0] for i in reactions_given), inline=True))

            emoji = (
                reactions_given[0][2]
                if not reactions_given[0][1] else
                '<:{}:{}>'.format(reactions_given[0][2], reactions_given[0][1])
            )
            embed.fields.append(
                MessageEmbedField(name='Most Used Reaction', value=u'{} (used {} times)'.format(
                    emoji,
                    reactions_given[0][0],
                ), inline=True))

        if emojis.value:
            emojis = list(emojis.value)

            if emojis:
                embed.add_field(
                    name='Most Used Emoji',
                    value=u'<:{1}:{0}> (`{1}`, used {2} times)'.format(*emojis[0]))

        embed.thumbnail = MessageEmbedThumbnail(url=user.avatar_url)
        embed.color = get_dominant_colors_user(user)
        event.msg.reply('', embed=embed)

    @Plugin.command('emojistats', '<mode:str> <sort:str>', level=CommandLevels.MOD)
    def emojistats_custom(self, event, mode, sort):
        if mode not in ('server', 'global'):
            raise CommandFail('invalid emoji mode, must be `server` or `global`')

        if sort not in ('least', 'most'):
            raise CommandFail('invalid emoji sort, must be `least` or `most`')

        order = 'DESC' if sort == 'most' else 'ASC'

        if mode == 'server':
            q = CUSTOM_EMOJI_STATS_SERVER_SQL.format(order, guild=event.guild.id)
        else:
            q = CUSTOM_EMOJI_STATS_GLOBAL_SQL.format(order, guild=event.guild.id)

        q = list(GuildEmoji.raw(q).tuples())

        tbl = MessageTable()
        tbl.set_header('Count', 'Name', 'ID')
        for emoji_id, name, count in q:
            tbl.add(count, name, emoji_id)

        event.msg.reply(tbl.compile())

    @Plugin.command('prune', '[uses:int]', level=CommandLevels.ADMIN, group='invites')
    def invites_prune(self, event, uses=1):
        invites = [
            i for i in event.guild.get_invites()
            if i.uses <= uses and i.created_at < (datetime.utcnow() - timedelta(hours=1))
        ]

        if not invites:
            return event.msg.reply('I didn\'t find any invites matching your criteria')

        msg = event.msg.reply(
            'Ok, a total of {} invites created by {} users with {} total uses would be pruned.'.format(
                len(invites),
                len({i.inviter.id for i in invites}),
                sum(i.uses for i in invites)
            ))

        msg.chain(False).\
            add_reaction(GREEN_TICK_EMOJI).\
            add_reaction(RED_TICK_EMOJI)

        try:
            mra_event = self.wait_for_event(
                'MessageReactionAdd',
                message_id=msg.id,
                conditional=lambda e: (
                    e.emoji.id in (GREEN_TICK_EMOJI_ID, RED_TICK_EMOJI_ID) and
                    e.user_id == event.author.id
                )).get(timeout=10)
        except gevent.Timeout:
            msg.reply('Not executing invite prune')
            msg.delete()
            return

        msg.delete()

        if mra_event.emoji.id == GREEN_TICK_EMOJI_ID:
            msg = msg.reply('Pruning invites...')
            for invite in invites:
                invite.delete()
            msg.edit('Ok, invite prune completed')
        else:
            msg = msg.reply('Not pruning invites')

    @Plugin.command(
        'clean',
        '<user:user|snowflake> [count:int] [emoji:str]',
        level=CommandLevels.MOD,
        group='reactions')
    def reactions_clean(self, event, user, count=10, emoji=None):
        if isinstance(user, DiscoUser):
            user = user.id

        if count > 50:
            raise CommandFail('cannot clean more than 50 reactions')

        lock = rdb.lock('clean-reactions-{}'.format(user))
        if not lock.acquire(blocking=False):
            raise CommandFail('already running a clean on user')

        query = [
            (Reaction.user_id == user),
            (Message.guild_id == event.guild.id),
            (Message.deleted == 0),
        ]

        if emoji:
            emoji_id = EMOJI_RE.findall(emoji)
            if emoji_id:
                query.append((Reaction.emoji_id == emoji_id[0]))
            else:
                # TODO: validation?
                query.append((Reaction.emoji_name == emoji))

        try:
            reactions = list(Reaction.select(
                Reaction.message_id,
                Reaction.emoji_id,
                Reaction.emoji_name,
                Message.channel_id,
            ).join(
                Message,
                on=(Message.id == Reaction.message_id),
            ).where(
                reduce(operator.and_, query)
            ).order_by(Reaction.message_id.desc()).limit(count).tuples())

            if not reactions:
                raise CommandFail('no reactions to purge')

            msg = event.msg.reply('Hold on while I clean {} reactions'.format(
                len(reactions)
            ))

            for message_id, emoji_id, emoji_name, channel_id in reactions:
                if emoji_id:
                    emoji = '{}:{}'.format(emoji_name, emoji_id)
                else:
                    emoji = emoji_name

                self.client.api.channels_messages_reactions_delete(
                    channel_id,
                    message_id,
                    emoji,
                    user)

            msg.edit('Ok, I cleaned {} reactions'.format(
                len(reactions),
            ))
        finally:
            lock.release()

    @Plugin.command('log', '<user:user|snowflake>', group='voice', level=CommandLevels.MOD)
    def voice_log(self, event, user):
        if isinstance(user, DiscoUser):
            user = user.id

        sessions = GuildVoiceSession.select(
            GuildVoiceSession.user_id,
            GuildVoiceSession.channel_id,
            GuildVoiceSession.started_at,
            GuildVoiceSession.ended_at
        ).where(
            (GuildVoiceSession.user_id == user) &
            (GuildVoiceSession.guild_id == event.guild.id)
        ).order_by(GuildVoiceSession.started_at.desc()).limit(10)

        tbl = MessageTable()
        tbl.set_header('Channel', 'Joined At', 'Duration')

        for session in sessions:
            tbl.add(
                unicode(self.state.channels.get(session.channel_id) or 'UNKNOWN'),
                '{} ({} ago)'.format(
                    session.started_at.isoformat(),
                    humanize.naturaldelta(datetime.utcnow() - session.started_at)),
                humanize.naturaldelta(session.ended_at - session.started_at) if session.ended_at else 'Active')

        event.msg.reply(tbl.compile())

    @Plugin.command('kick', '<user:user|snowflake>', group='voice', level=CommandLevels.MOD)
    @Plugin.command('voicekick', '<user:user|snowflake>', aliases=['vkick'], level=CommandLevels.MOD)
    def voice_kick(self, event, user):
        member = event.guild.get_member(user)
        if member:
            if not member.get_voice_state():
                raise CommandFail('member is not in a voice channel')

            member.disconnect()
            event.msg.reply(u':ok_hand: kicked {} from voice channel'.format(member.user))
        else:
            raise CommandFail('invalid user')

    @Plugin.command('join', '<name:str...>', aliases=['add', 'give'])
    def join_role(self, event, name):
        if not event.config.group_roles:
            return

        role = event.guild.roles.get(event.config.group_roles.get(name.lower()))
        if not role:
            raise CommandFail('invalid or unknown group')

        has_any_admin_perms = any(role.permissions.can(i) for i in (
            Permissions.KICK_MEMBERS,
            Permissions.BAN_MEMBERS,
            Permissions.ADMINISTRATOR,
            Permissions.MANAGE_CHANNELS,
            Permissions.MANAGE_GUILD,
            Permissions.MANAGE_MESSAGES,
            Permissions.MENTION_EVERYONE,
            Permissions.MUTE_MEMBERS,
            Permissions.MOVE_MEMBERS,
            Permissions.MANAGE_NICKNAMES,
            Permissions.MANAGE_ROLES,
            Permissions.MANAGE_WEBHOOKS,
            Permissions.MANAGE_EMOJIS,
        ))

        # Sanity check
        if has_any_admin_perms:
            raise CommandFail('cannot join group with admin permissions')

        member = event.guild.get_member(event.author)
        if role.id in member.roles:
            raise CommandFail('you are already a member of that group')

        member.add_role(role)
        if event.config.group_confirm_reactions:
            event.msg.add_reaction(GREEN_TICK_EMOJI)
            return
        raise CommandSuccess(u'you have joined the {} group'.format(name))

    @Plugin.command('leave', '<name:snowflake|str...>', aliases=['remove', 'take'])
    def leave_role(self, event, name):
        if not event.config.group_roles:
            return

        if name and isinstance(name, list) and isinstance(name[0], (int, long)):
          name = name[0]
        elif name:
          name = u' '.join(map(unicode, name)).lower()

        role_id = event.config.group_roles.get(name)
        if not role_id and name not in event.guild.roles:
            raise CommandFail('invalid or unknown group')

        member = event.guild.get_member(event.author)
        if role_id not in member.roles:
            raise CommandFail('you are not a member of that group')

        member.remove_role(role_id)
        if event.config.group_confirm_reactions:
            event.msg.add_reaction(GREEN_TICK_EMOJI)
            return
        raise CommandSuccess(u'you have left the {} group'.format(name))

    @Plugin.command('unlock', '<role_id:snowflake>', group='role', level=CommandLevels.ADMIN)
    def unlock_role(self, event, role_id):
        if role_id not in event.config.locked_roles:
            raise CommandFail('role %s is not locked' % role_id)

        if role_id in self.unlocked_roles and self.unlocked_roles[role_id] > time.time():
            raise CommandFail('role %s is already unlocked' % role_id)

        self.unlocked_roles[role_id] = time.time() + 300
        raise CommandSuccess('role is unlocked for 5 minutes')

    @Plugin.command('slowmode', '<interval:int> [channel:channel|snowflake]', level=CommandLevels.MOD)
    def slowmode(self, event, interval=0, channel=None):
        if interval < 0 or interval > 21600:
            raise CommandFail('rate limit interval must be between 0-21600')
        
        if isinstance(channel, DiscoChannel):
            channel = channel.id
        
        channel_id = channel or event.channel.id
        self.bot.client.api.channels_modify(
            channel_id,
            rate_limit_per_user=interval,
            reason=u'{} by {} ({})'.format('Enabled' if interval > 0 else 'Disabled', event.msg.author, event.msg.author.id)
        )

        if interval > 0:
            raise CommandSuccess('slowmode enabled')
        elif interval == 0:
            raise CommandSuccess('slowmode disabled')

    @Plugin.command('pong', level=CommandLevels.MOD)
    def ping(self, event):
        before = time.time()
        message = event.msg.reply("Ping...")

        ping = (time.time() - before) * 1000
        message.edit("Pong! `{}ms`".format(int(ping)))


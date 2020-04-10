# -*- coding: utf-8 -*-
import random
import requests
import humanize
import operator
import gevent
import math

from six import BytesIO
from PIL import Image
from peewee import fn
from gevent.pool import Pool
from datetime import datetime
from collections import defaultdict
from holster.enum import Enum

from disco.types.user import GameType, Status, User as DiscoUser
from disco.types.message import MessageEmbed
from disco.types.channel import ChannelType
from disco.util.snowflake import to_datetime
from disco.util.sanitize import S
from disco.api.http import Routes, APIException

from rowboat.plugins import RowboatPlugin as Plugin, CommandFail
from rowboat.util.input import humanize_duration
from rowboat.util.gevent import wait_many
from rowboat.util.stats import statsd, to_tags
from rowboat.types.plugin import PluginConfig
from rowboat.models.guild import GuildVoiceSession
from rowboat.models.user import User, Infraction
from rowboat.models.message import Message
from rowboat.util.images import get_dominant_colors_user, get_dominant_colors_guild
from rowboat.constants import (
    STATUS_EMOJI, SNOOZE_EMOJI, GREEN_TICK_EMOJI, GREEN_TICK_EMOJI_ID, RED_TICK_EMOJI, RED_TICK_EMOJI_ID,
    EMOJI_RE, USER_MENTION_RE, CDN_URL,
    CHANNEL_CATEGORY_EMOJI, TEXT_CHANNEL_EMOJI, VOICE_CHANNEL_EMOJI, ROLE_EMOJI, EMOJI_EMOJI, PREMIUM_GUILD_TIER_EMOJI, PREMIUM_GUILD_ICON_EMOJI,
)


def get_status_emoji(presence):
    if presence.game and presence.game.type == GameType.STREAMING:
        return STATUS_EMOJI[GameType.STREAMING], 'Streaming'
    elif presence.status == Status.ONLINE:
        return STATUS_EMOJI[Status.ONLINE], 'Online'
    elif presence.status == Status.IDLE:
        return STATUS_EMOJI[Status.IDLE], 'Idle',
    elif presence.status == Status.DND:
        return STATUS_EMOJI[Status.DND], 'DND'
    elif presence.status in (Status.OFFLINE, Status.INVISIBLE):
        return STATUS_EMOJI[Status.OFFLINE], 'Offline'


def get_emoji_url(emoji):
    return CDN_URL.format('-'.join(
        char.encode("unicode_escape").decode("utf-8")[2:].lstrip("0")
        for char in emoji))


class UtilitiesConfig(PluginConfig):
    pass


@Plugin.with_config(UtilitiesConfig)
class UtilitiesPlugin(Plugin):
    @Plugin.command('coin', group='random', global_=True)
    def coin(self, event):
        """
        Flip a coin
        """
        event.msg.reply(random.choice(['heads', 'tails']))

    @Plugin.command('number', '[end:int] [start:int]', group='random', global_=True)
    def random_number(self, event, end=10, start=0):
        """
        Returns a random number
        """

        # Because someone will be an idiot
        if end > 9223372036854775807:
            return event.msg.reply(':warning: ending number too big!')

        if end <= start:
            return event.msg.reply(':warning: ending number must be larger than starting number!')

        event.msg.reply(str(random.randint(start, end)))

    @Plugin.command('cat', global_=True)
    def cat(self, event):
        try:
            r = requests.get('https://api.thecatapi.com/v1/images/search?format=src')
            r.raise_for_status()
            ext = r.headers['content-type'].split('/')[-1].split(';')[0]
            event.msg.reply('', attachments=[('cat.{}'.format(ext), r.content)])
        except:
            return event.msg.reply('404 cat not found :(')

    @Plugin.command('dog', global_=True)
    def dog(self, event):
        try:
            r = requests.get('https://api.thedogapi.com/v1/images/search?format=src')
            r.raise_for_status()
            ext = r.headers['content-type'].split('/')[-1].split(';')[0]
            event.msg.reply('', attachments=[('dog.{}'.format(ext), r.content)])
        except:
            return event.msg.reply('404 dog not found :(')

    @Plugin.command('urban', '<term:str...>', global_=True)
    def urban(self, event, term):
        r = requests.get('http://api.urbandictionary.com/v0/define', params={
            'term': term,
        })
        r.raise_for_status()
        data = r.json()

        if not len(data['list']):
            return event.msg.reply(':warning: no matches')

        event.msg.reply(u'{} - {}'.format(
            S(data['list'][0]['word']),
            S(data['list'][0]['definition']),
        ))

    @Plugin.command('pwnd', '<email:str>', global_=True)
    def pwnd(self, event, email):
        r = requests.get('https://haveibeenpwned.com/api/v2/breachedaccount/{}'.format(
            email
        ))

        if r.status_code == 404:
            return event.msg.reply(":white_check_mark: you haven't been pwnd yet, awesome!")

        r.raise_for_status()
        data = r.json()

        sites = []

        for idx, site in enumerate(data):
            sites.append(u'{} - {} ({})'.format(
                site['BreachDate'],
                site['Title'],
                site['Domain'],
            ))

        return event.msg.reply(u":warning: You've been pwnd on {} sites:\n{}".format(
            len(sites),
            '\n'.join(sites),
        ))

    @Plugin.command('geoip', '<ip:str>', global_=True)
    def geoip(self, event, ip):
        r = requests.get('http://json.geoiplookup.io/{}'.format(ip))
        r.raise_for_status()
        data = r.json()

        event.msg.reply(u'{} - {}, {} ({}) | {}, {}'.format(
            data['isp'],
            data['city'],
            data['region'],
            data['country_code'],
            data['latitude'],
            data['longitude'],
        ))

    @Plugin.command('emoji', '<emoji:str>', global_=True)
    def emoji(self, event, emoji):
        if not EMOJI_RE.match(emoji):
            return event.msg.reply(u'Unknown emoji: `{}`'.format(S(emoji)))

        fields = []

        name, eid = EMOJI_RE.findall(emoji)[0]
        fields.append('**ID:** {}'.format(eid))
        fields.append('**Name:** {}'.format(S(name)))

        guild = self.state.guilds.find_one(lambda v: eid in v.emojis)
        if guild:
            fields.append('**Guild:** {} ({})'.format(S(guild.name), guild.id))

        anim = emoji.startswith('<a:')
        fields.append('**Animated:** {}'.format('Yes' if anim else 'No'))

        ext = 'gif' if anim else 'png'
        url = 'https://discordapp.com/api/emojis/{}.{}'.format(eid, ext)
        r = requests.get(url)
        r.raise_for_status()
        return event.msg.reply('\n'.join(fields), attachments=[('emoji.'+ext, r.content)])

    # Full credit goes to: Xenthys
    def get_emoji_url(self, emoji):
        name = '-'.join(char.encode("unicode_escape").decode("utf-8")[2:].lstrip("0") for char in emoji)
        return 'https://cdn.oceanlord.me/emoji/{}.png'.format(name) if name.find('--') == -1 else None

    @Plugin.command('jumbo', '<emojis:str...>', global_=True)
    def jumbo(self, event, emojis):
        emojis = emojis.split(' ')
        if len(emojis) == 1:
            url = ext = ''
            emoji = emojis[0]
            if EMOJI_RE.match(emoji):
                _, eid = EMOJI_RE.findall(emoji)[0]
                ext = 'gif' if emoji.startswith('<a:') else 'png'
                url = 'https://cdn.discordapp.com/emojis/{}.{}?v=1'.format(eid, ext)
            else:
                ext = 'png'
                url = self.get_emoji_url(emoji)

            if not url:
                raise CommandFail('provided emoji is invalid')

            r = requests.get(url)
            try:
                r.raise_for_status()
            except requests.HTTPError:
                raise CommandFail('provided emoji is invalid')
            return event.msg.reply('', attachments=[('emoji.'+ext, r.content)])

        else:
            urls = []
            for emoji in emojis[:5]:
                if EMOJI_RE.match(emoji):
                    _, eid = EMOJI_RE.findall(emoji)[0]
                    urls.append('https://cdn.discordapp.com/emojis/{}.png?v=1'.format(eid))
                else:
                    url = self.get_emoji_url(emoji)
                    urls.append(url) if url else None

            width, height, images = 0, 0, []

            for r in Pool(6).imap(requests.get, urls):
                try:
                    r.raise_for_status()
                except requests.HTTPError:
                    continue

                img = Image.open(BytesIO(r.content))
                height = img.height if img.height > height else height
                width += img.width + 10
                images.append(img)

            if not images:
                raise CommandFail('provided emojis are invalid')

            image = Image.new('RGBA', (width, height))
            width_offset = 0
            for img in images:
                image.paste(img, (width_offset, 0))
                width_offset += img.width + 10

            combined = BytesIO()
            image.save(combined, 'png', quality=55)
            combined.seek(0)
            return event.msg.reply('', attachments=[('emoji.png', combined)])

    @Plugin.command('seen', '<user:user>', global_=True)
    def seen(self, event, user):
        try:
            msg = Message.select(Message.timestamp).where(
                Message.author_id == user.id
            ).order_by(Message.timestamp.desc()).limit(1).get()
        except Message.DoesNotExist:
            return event.msg.reply(u"I've never seen {}".format(user))

        event.msg.reply(u'I last saw {} {} ago (at {})'.format(
            user,
            humanize_duration(datetime.utcnow() - msg.timestamp),
            msg.timestamp
        ))

    @Plugin.command('search', '<query:str...>', global_=True)
    def search(self, event, query):
        queries = []

        if query.isdigit():
            queries.append((User.user_id == query))

        q = USER_MENTION_RE.findall(query)
        if len(q) and q[0].isdigit():
            queries.append((User.user_id == q[0]))
        else:
            queries.append((User.username ** u'%{}%'.format(query.replace('%', ''))))

        if '#' in query:
            username, discrim = query.rsplit('#', 1)
            if discrim.isdigit():
                queries.append((
                    (User.username == username) &
                    (User.discriminator == int(discrim))))

        users = User.select().where(reduce(operator.or_, queries))
        if len(users) == 0:
            return event.msg.reply(u'No users found for query `{}`'.format(S(query, escape_codeblocks=True)))

        if len(users) == 1:
            if users[0].user_id in self.state.users:
                return self.info(event, self.state.users.get(users[0].user_id))

        return event.msg.reply(u'Found the following users for your query: ```{}```'.format(
            u'\n'.join(map(lambda i: u'{} ({})'.format(unicode(i), i.user_id), users[:25]))
        ))

    def get_max_emoji_slots(self, guild):
        emoji_max_slots = 50
        emoji_max_slots_more = 200
        PremiumGuildLimits = Enum(
            NONE=50,
            TIER_1=100,
            TIER_2=150,
            TIER_3=250,
        )
        return max(emoji_max_slots_more if 'MORE_EMOJI' in guild.features else emoji_max_slots, PremiumGuildLimits[guild.premium_tier.name].value)

    @Plugin.command('server', '[guild_id:snowflake]', global_=True)
    def server(self, event, guild_id=None):
        guild = self.state.guilds.get(guild_id) if guild_id else event.guild
        if not guild:
            raise CommandFail('invalid server')

        self.client.api.channels_typing(event.channel.id)

        embed = MessageEmbed()

        # Server Information
        content_server = []

        created_at = to_datetime(guild.id)
        content_server.append(u'**Created:** {} ago ({})'.format(
            humanize.naturaldelta(datetime.utcnow() - created_at),
            created_at.isoformat(),
        ))
        content_server.append(u'**Members:** {:,}'.format(guild.member_count))
        content_server.append(u'**Features:** {}'.format(', '.join(guild.features) or 'none'))
        content_server.append(u'**Voice region:** {}'.format(guild.region))

        if not bool(guild.max_members):
            self.state.guilds[guild.id].inplace_update(self.client.api.guilds_get(guild.id), ignored=[
                'channels',
                'members',
                'voice_states',
                'presences',
            ])

        content_server.append(u'**Max presences:** {:,}'.format(self.state.guilds[guild.id].max_presences))
        content_server.append(u'**Max members:** {:,}'.format(self.state.guilds[guild.id].max_members))

        embed.add_field(name=u'\u276F Server Information', value='\n'.join(content_server), inline=False)

        # Counts
        content_counts = []
        count = {}
        for c in guild.channels.values():
            if not c.type:
                continue
            ctype = c.type.name.split('_')[1]
            count[ctype] = count.get(ctype, 0) + 1
        content_counts.append(u'<{}> {} channel categories'.format(CHANNEL_CATEGORY_EMOJI, count.get('category', 0)))
        content_counts.append(u'<{}> {} text channels'.format(TEXT_CHANNEL_EMOJI, count.get('text', 0)))
        content_counts.append(u'<{}> {} voice channels'.format(VOICE_CHANNEL_EMOJI, count.get('voice', 0)))
        embed.add_field(name=u'\u276F Counts', value='\n'.join(content_counts), inline=True)

        content_counts2 = []
        content_counts2.append(u'<{}> {} roles'.format(ROLE_EMOJI, len(guild.roles)))
        static_emojis = len(filter(lambda e: not guild.emojis.get(e).animated, guild.emojis))
        animated_emojis = len(filter(lambda e: guild.emojis.get(e).animated, guild.emojis))
        content_counts2.append(u'<{}> {}/{total} static emojis'.format(
            EMOJI_EMOJI,
            static_emojis,
            total=self.get_max_emoji_slots(guild))
        )
        content_counts2.append(u'<{}> {}/{total} animated emojis'.format(
            EMOJI_EMOJI,
            animated_emojis,
            total=self.get_max_emoji_slots(guild))
        )
        embed.add_field(name=u'\u200B', value='\n'.join(content_counts2), inline=True)

        # Members
        content_members = []
        status_counts = defaultdict(int)
        for member in guild.members.values():
            if not member.user.presence:
                status = Status.OFFLINE
            else:
                status = member.user.presence.status
            status_counts[status] += 1

        for status, count in sorted(status_counts.items(), key=lambda i: Status[i[0]]):
            content_members.append(u'<{}> - {}'.format(
                STATUS_EMOJI[status], count
            ))

        embed.add_field(name=u'\u276F Members', value='\n'.join(content_members), inline=True)

        # Boosts
        content_boosts = []
        content_boosts.append(u'<{}> Level {}'.format(PREMIUM_GUILD_TIER_EMOJI[guild.premium_tier], int(guild.premium_tier)))
        real_boost_count = len(filter(lambda y: guild.members.get(y).premium_since, guild.members))
        content_boosts.append(u'<{}> {} boosts {}'.format(
            PREMIUM_GUILD_ICON_EMOJI,
            guild.premium_subscription_count,
            '({})'.format(real_boost_count) if real_boost_count < guild.premium_subscription_count else ''
        ))
        embed.add_field(name=u'\u276F Server Boost', value='\n'.join(content_boosts), inline=True)

        if guild.icon:
            embed.set_thumbnail(url=guild.icon_url)
            embed.color = get_dominant_colors_guild(guild, guild.get_icon_url('png'))
        event.msg.reply('', embed=embed)

    @Plugin.command('info', '[user:user|snowflake]')
    def info(self, event, user=None):
        if user is None:
            user = event.author

        user_id = 0
        if isinstance(user, (int, long)):
            user_id = user
            user = self.state.users.get(user)

        if user and not user_id:
            user = self.state.users.get(user.id)

        if not user:
            if user_id:
                try:
                    user = self.client.api.users_get(user_id)
                except APIException:
                    raise CommandFail('unknown user')
                User.from_disco_user(user)
            else:
                raise CommandFail('unknown user')

        self.client.api.channels_typing(event.channel.id)

        content = []
        content.append(u'**\u276F User Information**')
        content.append(u'**ID:** {}'.format(user.id))
        content.append(u'**Profile:** <@{}>'.format(user.id))

        if user.presence:
            emoji, status = get_status_emoji(user.presence)
            content.append('**Status:** {} <{}>'.format(status, emoji))

            game = user.presence.game
            if game and game.name:
                activity = ['Playing', 'Stream', 'Listening to', 'Watching', 'Custom Status'][int(game.type or 0)]
                if not game.type:
                    activity = None
                if activity:
                    game_name = game.state if game.type == GameType.CUSTOM_STATUS else game.name
                    content.append(u'**{}:** {}'.format(activity,
                        u'[{}]({})'.format(game_name, game.url) if game.url else game_name
                    ))

        created_dt = to_datetime(user.id)
        content.append('**Created:** {} ago ({})'.format(
            humanize.naturaldelta(datetime.utcnow() - created_dt),
            created_dt.isoformat()
        ))

        member = event.guild.get_member(user.id) if event.guild else None
        if member:
            content.append(u'\n**\u276F Member Information**')

            if member.nick:
                content.append(u'**Nickname:** {}'.format(member.nick))

            content.append('**Joined:** {} ago ({})'.format(
                humanize.naturaldelta(datetime.utcnow() - member.joined_at),
                member.joined_at.isoformat(),
            ))


            if member.roles:
                content.append(u'**Roles:** {}'.format(
                    ', '.join((member.guild.roles.get(r).mention for r in sorted(member.roles, key=lambda r: member.guild.roles.get(r).position, reverse=True)))
                ))

            # "is not None" does not work with Unset types for some rason
            if bool(member.premium_since):
                content.append('**Boosting since:** {} ago ({})'.format(
                    humanize.naturaldelta(datetime.utcnow() - member.premium_since),
                    member.premium_since.isoformat(),
                ))

        # Execute a bunch of queries async
        newest_msg = Message.select(Message.timestamp).where(
            (Message.author_id == user.id) &
            (Message.guild_id == event.guild.id)
        ).limit(1).order_by(Message.timestamp.desc()).async()

        oldest_msg = Message.select(Message.timestamp).where(
            (Message.author_id == user.id) &
            (Message.guild_id == event.guild.id)
        ).limit(1).order_by(Message.timestamp.asc()).async()

        infractions = Infraction.select(
            Infraction.guild_id,
            fn.COUNT('*')
        ).where(
            (Infraction.user_id == user.id)
        ).group_by(Infraction.guild_id).tuples().async()

        voice = GuildVoiceSession.select(
            GuildVoiceSession.user_id,
            fn.COUNT('*'),
            fn.SUM(GuildVoiceSession.ended_at - GuildVoiceSession.started_at)
        ).where(
            (GuildVoiceSession.user_id == user.id) &
            (~(GuildVoiceSession.ended_at >> None))
        ).group_by(GuildVoiceSession.user_id).tuples().async()

        # Wait for them all to complete (we're still going to be as slow as the
        #  slowest query, so no need to be smart about this.)
        wait_many(newest_msg, oldest_msg, infractions, voice, timeout=10)
        tags = to_tags(guild_id=event.msg.guild.id)

        if newest_msg.value and oldest_msg.value:
            statsd.timing('sql.duration.newest_msg', newest_msg.value._query_time, tags=tags)
            statsd.timing('sql.duration.oldest_msg', oldest_msg.value._query_time, tags=tags)
            newest_msg = newest_msg.value.get()
            oldest_msg = oldest_msg.value.get()

            content.append(u'\n **\u276F Activity**')
            content.append('**Last Message:** {} ago ({})'.format(
                humanize.naturaldelta(datetime.utcnow() - newest_msg.timestamp),
                newest_msg.timestamp.isoformat(),
            ))
            content.append('**First Message:** {} ago ({})'.format(
                humanize.naturaldelta(datetime.utcnow() - oldest_msg.timestamp),
                oldest_msg.timestamp.isoformat(),
            ))

        if infractions.value:
            statsd.timing('sql.duration.infractions', infractions.value._query_time, tags=tags)
            infractions = list(infractions.value)
            total = sum(i[1] for i in infractions)
            content.append(u'\n**\u276F Infractions**')
            content.append('**Total Infractions:** {:,}'.format(total))
            content.append('**Unique Servers:** {}'.format(len(infractions)))

        if voice.value:
            statsd.timing('plugin.utilities.info.sql.voice', voice.value._query_time, tags=tags)
            voice = list(voice.value)
            content.append(u'\n**\u276F Voice**')
            content.append(u'**Sessions:** {:,}'.format(voice[0][1]))
            content.append(u'**Time:** {}'.format(humanize.naturaldelta(
                voice[0][2]
            )))

        embed = MessageEmbed()

        avatar = user.avatar
        if avatar:
            avatar = user.avatar_url
        else:
            avatar = u'https://cdn.discordapp.com/embed/avatars/{}.png'.format(
                int(user.discriminator) % 5
            )

        embed.set_author(name=u'{}#{}'.format(
            user.username,
            user.discriminator,
        ), icon_url=avatar)

        embed.set_thumbnail(url=user.avatar_url if user.avatar else avatar)

        embed.description = '\n'.join(content)
        embed.color = get_dominant_colors_user(user, user.get_avatar_url('png') if user.avatar else avatar)
        event.msg.reply('', embed=embed)

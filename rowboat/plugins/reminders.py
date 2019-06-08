# -*- coding: utf-8 -*-
import humanize
import gevent

from datetime import datetime, timedelta

from disco.bot import CommandLevels
from disco.util.sanitize import S
from disco.types.message import MessageEmbed
from disco.types.channel import ChannelType

from rowboat.plugins import RowboatPlugin as Plugin, CommandFail, CommandSuccess
from rowboat.types.plugin import PluginConfig
from rowboat.util.timing import Eventual
from rowboat.util.input import parse_duration, humanize_duration
from rowboat.models.user import User
from rowboat.models.message import Message, Reminder
from rowboat.util.images import get_dominant_colors_user, get_dominant_colors_guild
from rowboat.constants import (
    STATUS_EMOJI, SNOOZE_EMOJI, GREEN_TICK_EMOJI, GREEN_TICK_EMOJI_ID, RED_TICK_EMOJI, RED_TICK_EMOJI_ID, YEAR_IN_SEC
)


class RemindersConfig(PluginConfig):
    pass


@Plugin.with_config(RemindersConfig)
class RemindersPlugin(Plugin):
    def load(self, ctx):
        super(RemindersPlugin, self).load(ctx)
        self.reminder_task = Eventual(self.trigger_reminders)
        self.spawn_later(10, self.queue_reminders)

    def queue_reminders(self):
        try:
            next_reminder = Reminder.select().order_by(
                Reminder.remind_at.asc()
            ).limit(1).get()
        except Reminder.DoesNotExist:
            return

        self.reminder_task.set_next_schedule(next_reminder.remind_at)

    def trigger_reminders(self):
        reminders = Reminder.with_message_join().where(
            (Reminder.remind_at < (datetime.utcnow() + timedelta(seconds=1)))
        )

        waitables = []
        for reminder in reminders:
            waitables.append(self.spawn(self.trigger_reminder, reminder))

        for waitable in waitables:
            waitable.join()

        self.queue_reminders()

    def trigger_reminder(self, reminder):
        message = reminder.message_id
        channel = self.state.channels.get(message.channel_id)
        if not channel:
            self.log.warning('Not triggering reminder, channel %s was not found!',
                message.channel_id)
            reminder.delete_instance()
            return

        msg = channel.send_message(u'<@{}> you asked me at {} ({} ago) to remind you about: {}'.format(
            message.author_id,
            reminder.created_at,
            humanize_duration(reminder.created_at - datetime.utcnow()),
            S(reminder.content)
        ))

        # Add the emoji options
        msg.add_reaction(SNOOZE_EMOJI)
        msg.add_reaction(GREEN_TICK_EMOJI)

        try:
            mra_event = self.wait_for_event(
                'MessageReactionAdd',
                message_id=msg.id,
                conditional=lambda e: (
                    (e.emoji.name == SNOOZE_EMOJI or e.emoji.id == GREEN_TICK_EMOJI_ID) and
                    e.user_id == message.author_id
                )
            ).get(timeout=30)
        except gevent.Timeout:
            reminder.delete_instance()
            return
        finally:
            # Cleanup
            msg.delete_reaction(SNOOZE_EMOJI)
            msg.delete_reaction(GREEN_TICK_EMOJI)

        if mra_event.emoji.name == SNOOZE_EMOJI:
            reminder.remind_at = datetime.utcnow() + timedelta(minutes=20)
            reminder.save()
            msg.edit(u'Ok, I\'ve snoozed that reminder for 20 minutes.')
            return

        reminder.delete_instance()

    @Plugin.command('delete global', '[reminder:str]', group='reminder', aliases=['remove global global', 'clean global', 'clear global'], context={'mode': 'global'}, global_=True)
    @Plugin.command('delete global', '[reminder:str]', group='r', aliases=['remove global', 'clean', 'clear global'], context={'mode': 'global'}, global_=True)
    @Plugin.command('delete', '[reminder:str]', group='reminder', aliases=['remove', 'clean', 'clear'], context={'mode': 'server'}, global_=True)
    @Plugin.command('delete', '[reminder:str]', group='r', aliases=['remove', 'clean', 'clear'], context={'mode': 'server'}, global_=True)
    def cmd_remind_clear(self, event, reminder='all', mode='server'):
        if reminder == 'all':
            count = Reminder.count_for_user(event.author.id, event.guild.id) if mode == 'server' else Reminder.count_for_user(event.author.id)

            if Reminder.count_for_user(event.author.id) == 0:
                return event.msg.reply('<:{}> cannot clear reminders when you don\'t have any'.format(RED_TICK_EMOJI))
            
            msg = event.msg.reply('Ok, clear {} reminders?'.format(count))
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

            count = Reminder.delete_all_for_user(event.author.id, event.guild.id) if mode == 'server' else Reminder.delete_all_for_user(event.author.id)
            return event.msg.reply(':ok_hand: I cleared {} reminders for you'.format(count))
        else:
            try:
                # stupid catch because python sucks
                try:
                    reminder = int(reminder)
                except:
                    return event.msg.reply('cannot convert `{}` to `int`'.format(S(reminder)))
                
                r = Reminder.select(Reminder).where(
                    (Reminder.message_id << Reminder.with_message_join((Message.id, )).where(
                        Message.author_id == event.author.id
                    )) & (Reminder.id == reminder)
                ).get()
            except Reminder.DoesNotExist:
                return event.msg.reply('<:{}> cannot find reminder #{}'.format(RED_TICK_EMOJI, reminder))
            
            msg = event.msg.reply('Ok, clear reminder #{}?'.format(reminder))
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
            
            Reminder.delete_for_user(event.author.id, r.id)
            return event.msg.reply(':ok_hand: I cleared reminder #{} for you'.format(r.id))

    @Plugin.command('add', '<duration:str> <content:str...>', group='r', global_=True)
    @Plugin.command('remind', '<duration:str> <content:str...>', global_=True)
    def cmd_remind(self, event, duration, content):
        if Reminder.count_for_user(event.author.id) > 30:
            return event.msg.reply(':warning: you can only have 15 reminders going at once!')

        remind_at = parse_duration(duration)
        if remind_at > (datetime.utcnow() + timedelta(seconds=5 * YEAR_IN_SEC)):
            return event.msg.reply(':warning: thats too far in the future, I\'ll forget!')

        r = Reminder.create(
            message_id=event.msg.id,
            remind_at=remind_at,
            content=content
        )
        self.reminder_task.set_next_schedule(r.remind_at)
        event.msg.reply(':ok_hand: I\'ll remind you at {} ({}) #{}'.format(
            r.remind_at.isoformat(),
            humanize_duration(r.remind_at - datetime.utcnow()),
            r.id
        ))

    @Plugin.command('list global', '[limit:int]', context={'mode': 'global'}, group='r', global_=True)
    @Plugin.command('list global', '[limit:int]', context={'mode': 'global'}, group='remind', global_=True)
    @Plugin.command('reminders global', '[limit:int]', context={'mode': 'global'}, global_=True)
    @Plugin.command('list', '[limit:int]', context={'mode': 'server'}, group='r', global_=True)
    @Plugin.command('list', '[limit:int]', context={'mode': 'server'}, group='remind', global_=True)
    @Plugin.command('reminders', '[limit:int]', context={'mode': 'server'}, global_=True)
    def cmd_remind_list(self, event, limit=None, mode='server'):
        user = event.msg.author
        count = Reminder.count_for_user(user.id, event.guild.id)
        total_count = Reminder.count_for_user(user.id)

        embed = MessageEmbed()
        embed.title = '{} reminder{} ({} total)'.format(count if mode == 'server' else total_count, '' if count == 1 else 's', total_count)

        embed.set_author(name=u'{}#{}'.format(
            user.username,
            user.discriminator,
        ), icon_url=user.avatar_url)
        embed.color = get_dominant_colors_user(user, user.get_avatar_url('png'))
        embed.set_footer(text='You can cancel reminders with !r clear [ID]')

        if (count == 0 and mode == 'server') or total_count == 0:
            embed.description = 'You have no upcoming reminders{}.'.format(' in this server. Use `!r list global` to list all your upcoming reminders' if total_count > 0 else '')
        else:
            query = Reminder.select(Reminder).where(
                (Reminder.message_id << Reminder.with_message_join((Message.id, )).where(
                    (Message.author_id == event.author.id) & (Message.guild_id == event.guild.id if mode == 'server' else True)
                )) & (Reminder.remind_at > (datetime.utcnow() + timedelta(seconds=1)))
            ).order_by(Reminder.remind_at).limit(limit)

            for reminder in query:
                time = humanize_duration(reminder.remind_at - datetime.utcnow())
                channel = Message.select().where(Message.id == reminder.message_id).get().channel_id
                channel = self.state.channels.get(channel)

                embed.add_field(
                    name=u'#{} in {}'.format(
                        reminder.id,
                        time
                    ),
                    value=u'[`#{}`](https://discordapp.com/channels/{}/{}/{}) {}'.format(
                        channel.name if channel.type != ChannelType.DM else 'Jetski',
                        channel.guild_id if channel.type != ChannelType.DM else '@me',
                        channel.id,
                        reminder.message_id,
                        S(reminder.content)
                    )
                )

        return event.msg.reply(embed=embed)

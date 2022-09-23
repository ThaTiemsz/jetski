import re
import json
import urllib.parse

from holster.enum import Enum
from unidecode import unidecode
from disco.types.base import cached_property
from disco.types.channel import ChannelType
from disco.util.sanitize import S
from disco.api.http import APIException
from disco.util.emitter import Priority

from rowboat.redis import rdb
from rowboat.util.zalgo import ZALGO_RE
from rowboat.plugins import RowboatPlugin as Plugin
from rowboat.types import SlottedModel, Field, ListField, DictField, ChannelField, snowflake, lower
from rowboat.types.plugin import PluginConfig
from rowboat.models.message import Message
from rowboat.plugins.modlog import Actions
from rowboat.constants import INVITE_LINK_RE, URL_RE

CensorReason = Enum(
    'INVITE',
    'DOMAIN',
    'WORD',
    'ZALGO',
)


class CensorSubConfig(SlottedModel):
    filter_zalgo = Field(bool, default=True)

    filter_invites = Field(bool, default=True)
    invites_guild_whitelist = ListField(snowflake, default=[])
    invites_whitelist = ListField(lower, default=[])
    invites_blacklist = ListField(lower, default=[])

    filter_domains = Field(bool, default=True)
    domains_whitelist = ListField(lower, default=[])
    domains_blacklist = ListField(lower, default=[])

    blocked_words = ListField(lower, default=[])
    blocked_tokens = ListField(lower, default=[])
    unidecode_tokens = Field(bool, default=False)

    channel = Field(snowflake, default=None)
    bypass_channel = Field(snowflake, default=None)

    @cached_property
    def blocked_re(self):
        return re.compile('({})'.format('|'.join(
            list(map(re.escape, self.blocked_tokens)) +
            list(map(lambda k: '\\b{}\\b'.format(re.escape(k)), self.blocked_words))
        )), re.I)


class CensorConfig(PluginConfig):
    levels = DictField(int, CensorSubConfig)
    channels = DictField(ChannelField, CensorSubConfig)


# It's bad kids!
class Censorship(Exception):
    def __init__(self, reason, event, ctx):
        self.reason = reason
        self.event = event
        self.ctx = ctx
        self.content = S(event.content, escape_codeblocks=True)

    @property
    def details(self):
        if self.reason is CensorReason.INVITE:
            if self.ctx['guild']:
                return'invite `{}` to {}'.format(
                    self.ctx['invite'],
                    S(self.ctx['guild']['name'], escape_codeblocks=True)
                )
            else:
                return'invite `{}`'.format(self.ctx['invite'])
        elif self.reason is CensorReason.DOMAIN:
            if self.ctx['hit'] == 'whitelist':
                return'domain `{}` is not in whitelist'.format(S(self.ctx['domain'], escape_codeblocks=True))
            else:
                return'domain `{}` is in blacklist'.format(S(self.ctx['domain'], escape_codeblocks=True))
        elif self.reason is CensorReason.WORD:
            return'found blacklisted words `{}`'.format(
               ', '.join([S(i, escape_codeblocks=True) for i in self.ctx['words']]))
        elif self.reason is CensorReason.ZALGO:
            return'found zalgo at position `{}` in text'.format(
                self.ctx['position']
            )


@Plugin.with_config(CensorConfig)
class CensorPlugin(Plugin):
    def compute_relevant_configs(self, event, author):
        if event.channel_id in event.config.channels:
            yield event.config.channels[event.channel.id]

        if event.config.levels:
            user_level = int(self.bot.plugins.get('CorePlugin').get_level(event.guild, author))

            for level, config in event.config.levels.items():
                if user_level <= level:
                    yield config

    def get_invite_info(self, code):
        if rdb.exists('inv:{}'.format(code)):
            return json.loads(rdb.get('inv:{}'.format(code)))

        try:
            obj = self.client.api.invites_get(code)
        except:
            return

        if obj.channel and obj.channel.type == ChannelType.GROUP_DM:
            obj = {
                'id': obj.channel.id,
                'name': obj.channel.name
            }
        else:
            obj = {
                'id': obj.guild.id,
                'name': obj.guild.name,
                'icon': obj.guild.icon
            }

        # Cache for 12 hours
        rdb.setex('inv:{}'.format(code), 43200, json.dumps(obj))
        return obj

    @Plugin.listen('MessageUpdate')
    def on_message_update(self, event):
        try:
            msg = Message.get(id=event.id)
        except Message.DoesNotExist:
            self.log.warning('Not censoring MessageUpdate for id %s, %s, no stored message', event.channel_id, event.id)
            return

        if not event.content:
            return

        return self.on_message_create(
            event,
            author=event.guild.get_member(msg.author_id))

    @Plugin.listen('MessageCreate', priority=Priority.AFTER)
    def on_message_create(self, event, author=None):
        author = author or event.author

        if author.id == self.bot.client.state.me.id:
            return

        if event.webhook_id:
            return

        configs = list(self.compute_relevant_configs(event, author))
        if not configs:
            return

        try:
            for config in configs:
                if config.channel:
                    if event.channel_id != config.channel:
                        continue
                if config.bypass_channel:
                    for byc in config.bypass_channel:
                        if event.channel_id == byc:
                            return

                if config.filter_invites:
                    self.filter_invites(event, config)

                if config.filter_domains:
                    self.filter_domains(event, config)

                if config.blocked_words or config.blocked_tokens or config.filter_domains:
                    self.filter_blocked_words(event, config)

        except Censorship as c:
            self.call('ModLogPlugin.create_debounce', event, ['MessageDelete'], message_id=event.message.id)

            try:
                event.delete()
                self.call('ModLogPlugin.log_action_ext', Actions.CENSORED, event.guild.id, e=event, c=c)
            except APIException:
                self.log.warning('Failed to delete censored message: ')

    def filter_zalgo(self, event, config):
        s = ZALGO_RE.search(event.content)
        if s:
            raise Censorship(CensorReason.ZALGO, event, ctx={
                'position': s.start()
            })

    def filter_invites(self, event, config):
        invites = INVITE_LINK_RE.findall(event.content)

        for _, invite in invites:
            invite_info = self.get_invite_info(invite)

            need_whitelist = (
                config.invites_guild_whitelist or
                (config.invites_whitelist or not config.invites_blacklist)
            )
            whitelisted = False

            if invite_info and invite_info.get('id') in config.invites_guild_whitelist:
                whitelisted = True

            if invite.lower() in config.invites_whitelist:
                whitelisted = True

            if need_whitelist and not whitelisted:
                raise Censorship(CensorReason.INVITE, event, ctx={
                    'hit': 'whitelist',
                    'invite': invite,
                    'guild': invite_info,
                })
            elif config.invites_blacklist and invite.lower() in config.invites_blacklist:
                raise Censorship(CensorReason.INVITE, event, ctx={
                    'hit': 'blacklist',
                    'invite': invite,
                    'guild': invite_info,
                })

    def filter_domains(self, event, config):
        urls = URL_RE.findall(INVITE_LINK_RE.sub('', event.content))

        for url in urls:
            try:
                parsed = urllib.parse.urlparse(url)
            except:
                continue

            if (config.domains_whitelist or not config.domains_blacklist)\
                    and parsed.netloc.lower() not in config.domains_whitelist:
                raise Censorship(CensorReason.DOMAIN, event, ctx={
                    'hit': 'whitelist',
                    'url': url,
                    'domain': parsed.netloc,
                })
            elif config.domains_blacklist and parsed.netloc.lower() in config.domains_blacklist:
                raise Censorship(CensorReason.DOMAIN, event, ctx={
                    'hit': 'blacklist',
                    'url': url,
                    'domain': parsed.netloc
                })

    def filter_blocked_words(self, event, config):
        content = event.content
        if config.unidecode_tokens:
            content = unidecode(content)
        blocked_words = config.blocked_re.findall(content)

        if blocked_words:
            raise Censorship(CensorReason.WORD, event, ctx={
                'words': blocked_words,
            })

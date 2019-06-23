# -*- coding: utf-8 -*-
# Full credit to Xenthys for coding this
import re
import requests
from time import time
from random import randint
from string import Formatter
from datetime import datetime

from disco.bot import CommandLevels
from disco.util.sanitize import S
from disco.types.message import MessageEmbed

from rowboat.plugins import RowboatPlugin as Plugin, CommandFail, CommandSuccess
from rowboat.types import Field
from rowboat.types.plugin import PluginConfig
from rowboat.models.tags import Tag
from rowboat.models.user import User

def clamp(string, size):
    if len(string) > size:
        return string[:size-1] + u'…'
    return string

class TagsConfig(PluginConfig):
    max_tag_length = Field(int)
    min_level_remove_others = Field(int, default=int(CommandLevels.MOD))

@Plugin.with_config(TagsConfig)
class TagsPlugin(Plugin):
    def load(self, ctx):
        super(TagsPlugin, self).load(ctx)

        self.remote_url = 'https://raw.githubusercontent.com/ThaTiemsz/RawgoatTags/master/tags/{}.md'
        self.import_parser = re.compile(r'##\sCode\n\n\s*(.+)\s*\n\n##\sExample', re.S)

        self.input_re = re.compile(r'{input(?::([0-9]+)?(\|(-)?([0-9]+)?)?)?}', re.I)

        self.match_re = re.compile(r'{match:([^|{}]*)\|([^|{}]*)(?:\|([^|{}]*))?}', re.I)
        self.if_re = re.compile(r'{if:([^|{}]*)\|([^|{}]*)(?:\|([^|{}]*))?}', re.I)
        self.math_re = re.compile(r'{math:([0-9]*)([+*%/-]?)([0-9]*)}', re.I)
        self.and_re = re.compile(r'{and:([^|{}]*)\|([^|{}]*)}', re.I)
        self.or_re = re.compile(r'{or:([^|{}]*)\|([^|{}]*)}', re.I)

        self.choose_re = re.compile(r'{choose:((?:[^|{}]*)(?:\|[^|{}]*)+)}', re.I)
        self.repeat_re = re.compile(r'{repeat:([0-9]+)?\|([^|{}]+)?}', re.I)
        self.random_re = re.compile(r'{random:([0-9]+)?\|([0-9]+)?}', re.I)

        self.get_re = re.compile(r'{get:([^|{}]*)(?:\|([0-9]))?}', re.I)
        self.set_re = re.compile(r'{set:([^|{}]*)\|([^{}]*)}', re.I)

        self.isnumber_re = re.compile(r'{isnumber:([^|{}]*)}', re.I)
        self.mention_re = re.compile(r'{mention:([^|{}]*)}', re.I)

        self.source_re = re.compile(r'{source:([a-z]+)}', re.I)

    def replace_variables(self, content, data):
        keys = data.keys()
        p = re.compile('{{({})}}'.format('|'.join(keys)))
        return p.sub(lambda m: data[m.group()[1:-1]], content)

    def fetch_tag(self, name, guild_id):
        try:
            tag = Tag.select(Tag).where(
                (Tag.name == S(name)) &
                (Tag.guild_id == guild_id)
            ).get()
        except Tag.DoesNotExist:
            return
        return tag

    def S(self, text, restore=False):
        if not text:
            return ''
        chars = [('{', '['), ('}', ']'), ('|', '&')]
        for t in chars:
            a, b = t[0], t[1]
            if not restore:
                text = text.replace(a, '%{}%'.format(b))
                continue
            text = text.replace('%{}%'.format(b), a)
            text = text.replace('%{}%'.format(a), b)
        return S(text, False, not restore)

    def tag_match(self, m):
        word = m.group(1).lower()
        base = m.group(2).lower()
        mode = (m.group(3) or 'full').lower()

        if not word or not base:
            return ''

        if mode == 'begin' or mode == 'start':
            return word if word.startswith(base) else ''

        if mode == 'end':
            return word if word.endswith(base) else ''

        if mode == 'contain':
            return word if base in word else ''

        return word if word == base else ''

    def tag_if(self, m):
        test = m.group(1)
        valid = m.group(2)
        invalid = m.group(3)

        if not test:
            return invalid

        comp = re.match(r'([0-9]+)([<=>])([0-9]+)', test)
        if comp:
            a = int(comp.group(1))
            cond = comp.group(2)
            b = int(comp.group(3))
            if cond == '=':
                test = a == b
            elif cond == '<':
                test = a < b
            elif cond == '>':
                test = a > b

        return valid if test else invalid

    def tag_math(self, m):
        a = m.group(1)
        op = m.group(2)
        b = m.group(3)

        if not op:
            return '0'

        a = a if a else '0'
        b = b if b else '0'

        try:
            return str(eval(a+op+b))
        except:
            return '0'

    def tag_and(self, m):
        return m.group(1) if m.group(1) and m.group(2) else ''

    def tag_or(self, m):
        return m.group(1) or m.group(2) or ''

    def tag_choose(self, m):
        opts = m.group(1).split('|')
        opts = [x for x in opts if x]
        if not opts:
            return ''
        return opts[randint(0, len(opts)-1)]

    def tag_repeat(self, m):
        mul = m.group(1)
        text = m.group(2)

        if not mul or not text:
            return ''

        mul = int(mul)
        if mul > 2000:
            mul = 2000

        return (mul * text)[:2000]

    def tag_random(self, m):
        a, b = m.group(1), m.group(2)

        if not a or not b:
            return ''

        a, b = int(a), int(b)
        if (a > b):
            a, b = b, a

        return str(randint(a, b))

    def tag_isnumber(self, m):
        n = m.group(1)

        if not n:
            return ''

        if re.match(r'[0-9]+', n):
            return n

        return ''

    def tag_mention(self, m):
        t = m.group(1)

        if not t:
            return ''

        if re.match(r'<@[&!]?[0-9]{17,19}>', t):
            return t

        return ''

    def compile_tag(self, event, content, text, debug=False):
        args = text
        text = self.S(text).split(' ')

        def tag_input(m):
            if not text:
                return ''

            size = len(text)
            first = m.group(1)
            sep = m.group(2)
            minus = m.group(3)
            last = m.group(4)

            if first:
                first = int(first)-1
                if not sep:
                    if first >= size:
                        return ''
                    return text[first]
                if not last:
                    return ' '.join(text[:first])

                last = int(last)
                if minus:
                    return ' '.join(text[first+1:-last])
                return ' '.join(text[first:last])

            if not sep:
                return ' '.join(text)

            last = -int(last)
            if minus:
                return ' '.join(text[:last])
            return ' '.join(text[last:])

        guild = event.guild
        member = event.member
        channel = event.channel

        user = member.user
        disc = user.discriminator

        avatar = user.avatar
        if avatar:
            avatar = u'https://cdn.discordapp.com/avatars/{}/{}.{}'.format(
                user.id, avatar, u'gif' if avatar.startswith('a_') else u'png'
            )
        else:
            avatar = u'https://cdn.discordapp.com/embed/avatars/{}.png'.format(int(disc)%5)

        bot = guild.members.select_one(id=self.state.me.id)

        now = datetime.utcnow()

        data = {
            'user': user.mention,
            'avatar_url': avatar,
            'discriminator': disc,
            'username': member.name,
            'user_id': str(user.id),
            'user_tag': u'{}'.format(user),
            'nickname': self.S(member.nick) or self.S(member.name),
            'channel': channel.mention,
            'channel_id': str(channel.id),
            'channel_name': u'{}'.format(channel),
            'bot_nickname': self.S(bot.nick) or self.S(bot.name),
            'server_name': event.guild.name,
            'year': now.strftime('%Y'),
            'month': now.strftime('%m'),
            'day': now.strftime('%d')
        }

        storage = {}
        def storage_set(m):
            k, v = m.group(1), m.group(2)
            if not k or not v:
                return ''
            storage[k] = v
            return ''

        def storage_get(m):
            k = m.group(1)
            w = m.group(2)
            if w and w != '0':
                w = int(w)
                if w <= 1:
                    return u'{{get:{}}}'.format(k)
                return u'{{get:{}|{}}}'.format(k, w-1)

            if not k:
                return ''

            return storage.get(k, '')

        if debug:
            start = time()
            debug = u'Initialization\nContent: {}\nInput: {}\n\n'.format(content, args or '(none)')
        content = self.source_re.sub('', content)
        for i in range(10):
            old = content
            content = self.replace_variables(content, data)
            content = self.input_re.sub(tag_input, content)
            content = self.set_re.sub(storage_set, content)
            content = self.get_re.sub(storage_get, content)
            content = self.isnumber_re.sub(self.tag_isnumber, content)
            content = self.mention_re.sub(self.tag_mention, content)
            content = self.random_re.sub(self.tag_random, content)
            content = self.choose_re.sub(self.tag_choose, content)
            content = self.repeat_re.sub(self.tag_repeat, content)
            content = self.match_re.sub(self.tag_match, content)
            content = self.and_re.sub(self.tag_and, content)
            content = self.or_re.sub(self.tag_or, content)
            content = self.if_re.sub(self.tag_if, content)
            if content == old:
                break
            if debug:
                debug += u'Step #{}\nContent: {}\nStorage: {}\n\n'.format(
                    i+1,
                    content,
                    u'; '.join(map(
                        lambda x: u'[{}] "{}"'.format(x[0], x[1]),
                        storage.iteritems()
                    )) or '(empty)'
                )

        content = self.S(content, True)

        perms = event.member.permissions
        if not (perms.administrator or perms.mention_everyone):
            content = content.\
                replace('@here', u'@\u200Bhere').\
                replace('@everyone', u'@\u200Beveryone')

        if debug:
            debug += u'End result: {}'.format(content)
            parsing = '_Parsing took {}ms_'.format(
                format((time() - start) * 1000, '.3f')
            )
            if len(debug) < 1970:
                return event.msg.reply(u'```\n{}\n```{}'.format(debug, parsing))
            return event.msg.reply(parsing, attachments=[(
                'tag_debug_{}.txt'.format(event.msg.id), debug
            )])

        return content


    @Plugin.command('create', '<name:str> <content:str...>', group='tags', aliases=['add'], level=CommandLevels.TRUSTED)
    def on_tags_create(self, event, name, content):
        if re.search(r'<a?:\S+:[0-9]+>', name):
            raise CommandFail('tag names cannot contain emotes')

        name = S(name)

        import_tag = re.match(r'^import:([a-z]+)$', content, re.I)
        if import_tag:
            remote = import_tag.group(1).lower()
            r = requests.get(self.remote_url.format(remote))
            try:
                r.raise_for_status()
            except requests.HTTPError:
                raise CommandFail('{}not found'.format(remote))

            content = self.import_parser.search(r.content)
            if not content:
                raise CommandFail('remote tag `{}` is malformed - please tell Rawgoat staff'.format(remote))

            content = content.group(1).decode('utf8').strip('`\n')
            if not self.source_re.search(content):
                content = u'{{source:{}}}{}'.format(remote, content)
        else:
            content = self.source_re.sub('', content)

        data = {
            'here': '@here',
            'everyone': '@everyone'
        }

        content = self.replace_variables(content, data)

        if len(content) > event.config.max_tag_length:
            raise CommandFail('tag content is too long (max {} characters)'.format(event.config.max_tag_length))

        if self.fetch_tag(name, event.guild.id):
            raise CommandFail('a tag by that name already exists')

        _, created = Tag.get_or_create(
            guild_id=event.guild.id,
            author_id=event.author.id,
            name=name,
            content=content
        )

        raise CommandSuccess(u'ok, your tag named `{}` has been {}'.format(
            name, 'imported' if import_tag else 'created'
        ))

    @Plugin.command('tags', '<name:str> [text:str...]', aliases=['tag', 't'], level=CommandLevels.TRUSTED)
    @Plugin.command('show', '<name:str> [text:str...]', group='tags', level=CommandLevels.TRUSTED)
    @Plugin.command('debug', '<name:str> [text:str...]', group='tags', level=CommandLevels.TRUSTED, context={'debug': True})
    def on_tags(self, event, name, text='', debug=False):
        tag = self.fetch_tag(name, event.guild.id)

        if not tag:
            raise CommandFail('no tag exists by that name')

        # Track the usage of the tag
        Tag.update(
            times_used=Tag.times_used+1
        ).where(
            (Tag.name == tag.name) &
            (Tag.guild_id == tag.guild_id)
        ).execute()

        content = self.compile_tag(event, tag.content, text, debug)

        if not debug:
            event.msg.reply(clamp(u':information_source: {}'.format(content), 2000))

    @Plugin.command('eval', parser=True, group='tags', level=CommandLevels.TRUSTED)
    @Plugin.parser.add_argument('content', nargs='+')
    @Plugin.parser.add_argument('-i', '--input', default='', help='tag input')
    @Plugin.parser.add_argument('-d', '--debug', action='store_true')
    def on_tags_eval(self, event, args):
        content = self.compile_tag(
            event,
            u' '.join(args.content),
            args.input,
            args.debug
        )

        if not args.debug:
            event.msg.reply(clamp(u':information_source: {}'.format(content), 2000))

    @Plugin.command('remove', '<name:str>', group='tags', aliases=['delete', 'del', 'rm'], level=CommandLevels.TRUSTED)
    def on_tags_remove(self, event, name):
        try:
            tag = Tag.select(Tag, User).join(
                User, on=(User.user_id == Tag.author_id)
            ).where(
                (Tag.name == S(name)) &
                (Tag.guild_id == event.guild.id)
            ).get()
        except Tag.DoesNotExist:
            raise CommandFail('no tag exists by that name')

        if tag.author_id != event.author.id:
            if event.user_level < event.config.min_level_remove_others:
                raise CommandFail('you do not have the required permissions to remove other users tags')

        tag.delete_instance()
        raise CommandSuccess(u'ok, deleted tag `{}`'.format(tag.name))

    @Plugin.command('info', '<name:str>', group='tags', level=CommandLevels.TRUSTED)
    def on_tags_info(self, event, name):
        try:
            tag = Tag.select(Tag, User).join(
                User, on=(User.user_id == Tag.author_id).alias('author')
            ).where(
                (Tag.name == S(name)) &
                (Tag.guild_id == event.guild.id)
            ).get()
        except Tag.DoesNotExist:
            raise CommandFail('no tag exists by that name')

        content = tag.content
        source = self.source_re.search(content)
        if source:
            source = source.group(1).lower()
            url = self.remote_url.format(source)
            r = requests.get(url)
            r = self.import_parser.search(r.content)
            r = r.group(1).decode('utf8').strip('`\n') if r else ''
            data = {'here': '@here', 'everyone': '@everyone'}
            r = self.replace_variables(r, data)
            if not (r and content == r):
                source = None
                content = self.source_re.sub('', content)
                Tag.update(content=content).where(
                    (Tag.name == tag.name) &
                    (Tag.guild_id == tag.guild_id)
                ).execute()

        embed = MessageEmbed()
        embed.title = tag.name
        embed.description = clamp(content, 2048)
        embed.add_field(name='Author', value=unicode(tag.author), inline=True)
        embed.add_field(name='Times Used', value=str(tag.times_used), inline=True)
        embed.add_field(name='Imported', inline=True, value='No' if not source else ('Yes: [{source}]'
            '(https://github.com/ThaTiemsz/RawgoatTags/blob/master/tags/{source}.md)').format(source=source))
        embed.timestamp = tag.created_at.isoformat()
        event.msg.reply(embed=embed)

    @Plugin.command('raw', '<name:str>', group='tags', level=CommandLevels.TRUSTED)
    def on_tags_raw(self, event, name):
        tag = self.fetch_tag(name, event.guild.id)

        if not tag:
            raise CommandFail('no tag exists by that name')

        content = tag.content

        source = self.source_re.search(content)
        if source:
            source = source.group(1).lower()
            url = self.remote_url.format(source)
            r = requests.get(url)
            r = self.import_parser.search(r.content)
            r = r.group(1).decode('utf8').strip('`\n') if r else ''
            data = {'here': '@here', 'everyone': '@everyone'}
            r = self.replace_variables(r, data)
            if r and content == r:
                return event.msg.reply(
                    ('This tag was imported from `{source}`: <https://github.com/ThaTiemsz'
                    '/RawgoatTags/blob/master/tags/{source}.md>').format(source=source)
                )
            content = self.source_re.sub('', content)
            Tag.update(content=content).where(
                (Tag.name == tag.name) &
                (Tag.guild_id == tag.guild_id)
            ).execute()

        if len(S(content, False, True)) > 1990:
            return event.msg.reply(
                'This tag is too long. See attached file for the source.',
                attachments=[('tag_raw_{}.txt'.format(event.msg.id), content)]
            )

        event.msg.reply(u'```\n{}\n```'.format(S(content, False, True)))

    @Plugin.command('list', '[pattern:str]', group='tags', level=CommandLevels.TRUSTED)
    def on_tags_list(self, event, pattern=None):
        buff = u'Available tags: '
        query = Tag.select(Tag.name).where(Tag.guild_id == event.guild.id)
        tags = sorted([i[0] for i in query.tuples()])
        if not tags:
            return event.msg.reply('No tags found for this server.')
        found = 0
        for tag in tags:
            if pattern and tag.lower().find(pattern.lower()) == -1: continue
            tag = u'`{}`, '.format(S(tag, escape_codeblocks=True))
            if len(tag) + len(buff) > 1980:
                event.msg.reply(buff[:-2])
                buff = u''
            buff += tag
            found += 1

        if not found:
            return event.msg.reply('No tags found for this server.')
        return event.msg.reply(u'{} (total: {})'.format(buff[:-2], found))
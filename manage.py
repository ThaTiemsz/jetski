#!/usr/bin/env python3.8
from gevent import monkey; monkey.patch_all()

import click
import copy
import gevent
import logging
import os
import signal
import subprocess

from gevent import pywsgi
from werkzeug.serving import run_with_reloader
from yaml import safe_load

from disco.util.logging import LOG_FORMAT

from rowboat.sql import init_db
from rowboat.web import rowboat


class BotSupervisor(object):
    def __init__(self, env={}):
        self.proc = None
        self.env = env
        self.bind_signals()
        self.start()

    def bind_signals(self):
        signal.signal(signal.SIGINT, self.handle_sigint)
        signal.signal(signal.SIGUSR1, self.handle_sigusr1)

    def handle_sigusr1(self, signum, frame):
        print('SIGUSR1 - RESTARTING')
        gevent.spawn(self.restart)

    def handle_sigint(self, signum, frame):
        print('SIGINT - SHUTTING DOWN')
        gevent.spawn(self.stop)

    def start(self):
        env = copy.deepcopy(os.environ)
        env.update(self.env)
        self.proc = subprocess.Popen(['python3.8', '-m', 'disco.cli', '--config', 'config.yaml'], env=env)

    def stop(self):
        self.proc.terminate()

    def restart(self):
        try:
            self.stop()
            self.start()
        except:
            print('ERROR: Could not restart')

    def run_forever(self):
        while True:
            self.proc.wait()
            gevent.sleep(3)
            self.restart()


@click.group()
def cli():
    logging.getLogger().setLevel(logging.INFO)


@cli.command()
@click.option('--reloader/--no-reloader', '-r', default=False)
def serve(reloader):
    def run():
        pywsgi.WSGIServer(('127.0.0.1', 8686), rowboat.app).serve_forever()

    if reloader:
        run_with_reloader(run)
    else:
        run()


@cli.command()
@click.option('--env', '-e', default='local')
def bot(env):
    with open('config.yaml', 'r') as f:
        config = safe_load(f)

    supervisor = BotSupervisor(env={
        'ENV': env,
        'DSN': config['DSN'],
    })
    supervisor.run_forever()


@cli.command()
@click.option('--worker-id', '-w', default=0)
def workers(worker_id):
    from rowboat.tasks import TaskWorker

    # Log things to file
    file_handler = logging.FileHandler('worker-{}.log'.format(worker_id))
    log = logging.getLogger()
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    log.addHandler(file_handler)

    for logname in ['peewee', 'requests']:
        logging.getLogger(logname).setLevel(logging.INFO)

    init_db()
    TaskWorker().run()


@cli.command('add-global-admin')
@click.argument('user-id')
def add_global_admin(user_id):
    from rowboat.redis import rdb
    from rowboat.models.user import User
    init_db()
    rdb.sadd('global_admins', user_id)
    User.update(admin=True).where(User.user_id == user_id).execute()
    print('Ok, added {} as a global admin'.format(user_id))


@cli.command('wh-add')
@click.argument('guild-id')
@click.argument('flag')
def add_whitelist(guild_id, flag):
    from rowboat.models.guild import Guild
    init_db()

    flag = Guild.WhitelistFlags.get(flag)
    if not flag:
        print('Invalid flag')
        return

    try:
        guild = Guild.get(guild_id=guild_id)
    except Guild.DoesNotExist:
        print('No guild exists with that id')
        return

    if guild.is_whitelisted(flag):
        print('This guild already has this flag')

    guild.whitelist.append(int(flag))
    guild.save()
    guild.emit('GUILD_UPDATE')
    print('Added flag')


@cli.command('wh-rmv')
@click.argument('guild-id')
@click.argument('flag')
def rmv_whitelist(guild_id, flag):
    from rowboat.models.guild import Guild
    init_db()

    flag = Guild.WhitelistFlags.get(flag)
    if not flag:
        print('Invalid flag')
        return

    try:
        guild = Guild.get(guild_id=guild_id)
    except Guild.DoesNotExist:
        print('No guild exists with that id')
        return

    if not guild.is_whitelisted(flag):
        print('This guild doesn\'t have this flag')

    guild.whitelist.remove(int(flag))
    guild.save()
    guild.emit('GUILD_UPDATE')
    print('Removed flag')


if __name__ == '__main__':
    cli()

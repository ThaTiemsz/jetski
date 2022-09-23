import logging
import os
import subprocess

from sentry_sdk import init
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.excepthook import ExcepthookIntegration

from disco.util.logging import LOG_FORMAT

ENV = os.getenv('ENV', 'local')
DSN = os.getenv('DSN')
REV = subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip()

VERSION = '1.3.0'

sentry_client = init(
    DSN,
    release=VERSION,
    environment=ENV,
    integrations=[FlaskIntegration(), RedisIntegration(), ExcepthookIntegration(always_run=True)]
)

# Log things to file
file_handler = logging.FileHandler('rowboat.log')
log = logging.getLogger()
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
log.addHandler(file_handler)

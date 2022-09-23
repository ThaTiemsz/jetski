import psycogreen.gevent; psycogreen.gevent.patch_psycopg()
import yaml

from peewee import Proxy, OP, Model, Expression
from playhouse.postgres_ext import PostgresqlExtDatabase

REGISTERED_MODELS = []
OP['IREGEXP'] = 'iregexp'

# Create a database proxy we can setup post-init
database = Proxy()

with open('config.yaml', 'r') as config:
    cfg = yaml.safe_load(config)


def pg_regex_i(lhs, rhs):
    return Expression(lhs, OP.IREGEXP, rhs)


class BaseModel(Model):
    class Meta:
        database = database

    @staticmethod
    def register(cls):
        REGISTERED_MODELS.append(cls)
        return cls


def init_db():
    database.initialize(PostgresqlExtDatabase(
        'rowboat',
        host=cfg['db_host'],
        user=cfg['db_user'],
        password=cfg['db_password'],
        port=cfg['db_port'],
        autorollback=True,
        autoconnect=True,
        register_hstore=True,
        operations={OP.IREGEXP: '~*'})),

    for model in REGISTERED_MODELS:
        model.create_table(True)

        if hasattr(model, 'SQL'):
            database.execute_sql(model.SQL)


def reset_db():
    init_db()

    for model in REGISTERED_MODELS:
        model.drop_table(True)
        model.create_table(True)

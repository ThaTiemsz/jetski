from datetime import datetime
from peewee import BigIntegerField, TextField, DateTimeField, CompositeKey, IntegerField

from rowboat.sql import BaseModel


@BaseModel.register
class Tag(BaseModel):
    guild_id = BigIntegerField()
    author_id = BigIntegerField()

    name = TextField()
    content = TextField()
    times_used = IntegerField(default=0)

    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = 'tags'
        primary_key = CompositeKey('guild_id', 'name')

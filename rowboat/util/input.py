from datetime import datetime, timedelta
from disco.bot.command import CommandError


UNITS = {
    's': lambda v: v,
    'm': lambda v: v * 60,
    'h': lambda v: v * 60 * 60,
    'd': lambda v: v * 60 * 60 * 24,
    'w': lambda v: v * 60 * 60 * 24 * 7,
}


def parse_duration(raw, source=None, negative=False, safe=False):
    if not raw:
        if safe:
            return None
        raise CommandError('Invalid duration')

    value = 0
    digits = ''

    for char in raw:
        if char.isdigit():
            digits += char
            continue

        if char not in UNITS or not digits:
            if safe:
                return None
            raise CommandError('Invalid duration')

        value += UNITS[char](int(digits))
        digits = ''

    if negative:
        value = value * -1

    return (source or datetime.utcnow()) + timedelta(seconds=value + 1)

def humanize_duration(duration, format='full'):
    now = datetime.utcnow()
    if isinstance(duration, timedelta):
        duration = datetime.utcnow() - timedelta(seconds=duration.total_seconds())
    diff_delta = duration - now
    diff = int(diff_delta.total_seconds())

    minutes, seconds = divmod(diff, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    weeks, days = divmod(days, 7)
    units = [weeks, days, hours, minutes, seconds]

    if format == 'full':
        unit_strs = ['week', 'day', 'hour', 'minute', 'second']
    elif format == 'short':
        unit_strs = ['w', 'd', 'h', 'm', 's']

    expires = []
    for x in range(0, 5):
        if units[x] == 0:
            continue
        else:
            if format == 'short':
                expires.append('{}{}'.format(units[x], unit_strs[x]))
            elif units[x] > 1:
                expires.append('{} {}s'.format(units[x], unit_strs[x]))
            else:
                expires.append('{} {}'.format(units[x], unit_strs[x]))
    
    return ', '.join(expires)

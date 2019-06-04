import re

transformations = {
    re.escape(c): '\\' + c for c in ('*', '`', '_', '~~', '\\', '||')
}

def replace(obj):
    return transformations.get(re.escape(obj.group(0)), '')

def E(text):
    pattern = re.compile('|'.join(transformations.keys()))
    text = pattern.sub(replace, text)

    return text

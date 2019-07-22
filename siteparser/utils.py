import hashlib
import re
from jinja2 import Environment, Template


class ParserUtils(object):
    @classmethod
    def regex_replace(s, find, replace):
        return re.sub(find, replace, s)

    jinja = Environment()
    jinja.filters['regex_replace'] = regex_replace

    def __init__(self):
        pass

    @classmethod
    def flatten(cls, root, collected=None):
        if collected is None:
            collected = dict()
        content = []

        for element in root.iter():
            if element.tag in ['script']:
                continue

            if element.tag in ['img', 'iframe', 'a']:
                if element.tag not in collected:
                    collected[element.tag] = []
                collected[element.tag].append(element.get('src') or element.get('href'))
                continue

            text = ''
            if element.text is not None and element.text.strip() != '':
                text = element.text.strip()
            if element.tail is not None and element.tail.strip() != '':
                text = text + (' ' if text != '' else '') + element.tail.strip()
            if text != '':
                content.append(text)
        return u'\n'.join(content)

    @classmethod
    def md5(cls, raw):
        h = hashlib.md5()
        h.update(raw)
        return h.hexdigest()


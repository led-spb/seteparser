import json
import logging
import time
import re
import requests
import cookielib
import hashlib
import humanfriendly
from jinja2 import Environment, Template


def regex_replace(s, find, replace):
    return re.sub(find, replace, s)


class Context(object):
    jinja = Environment()


Context.jinja.filters['regex_replace'] = regex_replace


class Map(dict):
    @classmethod
    def from_dict(cls, dict_object):
        obj = Map()
        for key, value in dict_object.items():
            if type(value) is dict:
                value = Map.from_dict(value)
            obj[key] = value
        return obj

    def __getattr__(self, attr):
        return self.__getitem__(attr)

    def __setattr__(self, attr, value):
        self[attr] = value


class Item(object):
    _attributes = ['id', 'title', 'body', 'src', 'category', 'attachment', 'lifetime', 'data']

    def __init__(self, **kwargs):
        self.__data__ = kwargs
        # default item lifetime 7 days
        if self.lifetime is None:
            self.__data__['lifetime'] = 7 * 24 * 60 * 60

        if self.data is None or type(self.data) is not dict:
            self.__data__['data'] = {}

    def __getattr__(self, name):
        return self.__data__[name] if name in self._attributes and name in self.__data__ else None

    def __str__(self):
        return json.dumps(self.__data__)

    @property
    def hash(self):
        h = hashlib.sha1()
        data = {key: value for key, value in self.__data__.iteritems() if key != 'data'}
        h.update(json.dumps(data, sort_keys=True, skipkeys=True))
        return h.hexdigest()


class SelfConstruct(object):
    @classmethod
    def subclass(cls, name):
        for sub_cls in cls.__subclasses__():
            if hasattr(sub_cls, 'name') and sub_cls.name == name:
                return sub_cls
        return None


class Configurable(object):
    def __init__(self, params=None):
        self.params = Map.from_dict(params or {})

    def param(self, key, default=None):
        return self.params[key] if key in self.params else default

    def has_param(self, key):
        return key in self.params


class Schedule(Configurable):
    def __init__(self, params=None):
        Configurable.__init__(self, params)
        self.period = 0
        if 'period' in self.params:
            self.period = humanfriendly.parse_timespan(self.params.period)
        pass

    def is_trigger(self, timestamp, parser):
        if (timestamp - parser.last_timestamp) >= self.period:
            return True
        return False
     


class SiteParser(Configurable, SelfConstruct):
    def __init__(self, params=None):
        Configurable.__init__(self, params)
        self.session = requests.Session()
        self.session.cookies = cookielib.CookieJar()
        self.last_timestamp = 0
        self.items = []

    def make_request(self, url=None, data=None, headers=None):
        url = url or self.param('url')
        data = data or self.param('data')

        charset = self.param('encoding', 'utf-8')
        req_headers = {'Accept-Charset': charset}
        req_headers.update(headers or self.param('headers') or {})

        if data is not None:
            response = self.session.post(url, headers=req_headers, data=data)
        else:
            response = self.session.get(url, headers=req_headers)
        logging.debug(response.text)
        return response

    def add(self, **kwargs):
        kwargs.update({'category': self.param('instance')})
        self.items.append(Item(**kwargs))

    def parse(self):
        self.items = []
        return self.items

    def md5(self, raw):
        h = hashlib.md5()
        h.update(raw)
        return h.hexdigest()


class ItemFilter(Configurable, SelfConstruct):
    def filter(self, value):
        return True


class AllFilter(ItemFilter):
    name = "all"
    pass


class RegexpFilter(ItemFilter):
    name = "regexp"

    def __init__(self, params=None):
        ItemFilter.__init__(self, params)
        self.filters = [re.compile(expr, re.I + re.M + re.U) for expr in self.param('matches', [])]
        pass

    def filter(self, item):
        for f in self.filters:
            if f.search(item.body) or f.search(item.title):
                return True
        return False


class KeyStorage(object):
    def __init__(self, filename):
        self.storage = {}
        self.filename = filename
        self.load()

    def load(self):
        try:
            self.storage = json.load(open(self.filename, "rt"))
            if type(self.storage) is not dict:
               self.storage = {}
        except StandardError:
            pass

    def save(self):    
        try:
            json.dump(self.storage, open(self.filename, "wt"), indent=2)
        except StandardError:
            pass

    def get(self, attr):
        return self.storage.get(attr)

    def put(self, attr, value):
        self.storage[attr] = value


class ItemCache(object):
    def __init__(self, storage):
        self.storage = storage
        self.cached = {}
        self.load()
        pass

    def load(self):
        self.cached = {}
        try:
            for x in (self.storage.get('items') or []):
                item = Item(**x)
                logging.debug(str(item))
                self.add(item, True)
        except StandardError:
            pass
        pass

    def save(self):
        try:
            now = time.time()
            for idx in self.cached.keys():
                if self.cached[idx].lifetime is not None and self.cached[idx].lifetime > 0 \
                        and (now - self.cached[idx].data['updated']) > self.cached[idx].lifetime:
                    del self.cached[idx]
            self.storage.put('items', [x.__data__ for x in self.cached.itervalues()])
            #json.dump([x.__data__ for x in self.cached.itervalues()], open(self.cache_file, "wt"), indent=2)
        except StandardError:
            # logging.exception('on store cache')
            pass
        pass

    def check(self, item):
        idx = str(item.category) + '_' + str(item.id)
        if idx in self.cached.keys():
            cached_item = self.cached[idx]
            if cached_item.hash == item.hash:
                item.data.update(cached_item.data)
                return True
        return False

    def add(self, item, skip_update=False):
        idx = str(item.category) + '_' + str(item.id)
        if not skip_update:
            item.data['updated'] = time.time()
        self.cached[idx] = item

    def remove(self, item):
        idx = str(item.category) + '_' + str(item.id)
        if idx in self.cached.keys():
            del self.cached[idx]
        return


class OutputProcessor(Configurable, SelfConstruct):
    default_template = \
"""Category: {{item.category}}
Title: {{item.title}}
Body: {{item.body}}
Link: {{item.src}}"""

    def __init__(self, cache, params=None):
        Configurable.__init__(self, params)
        self.cache = cache
        self.template = Context.jinja.from_string(self.param("template", self.default_template))
        self.timeout = int(self.param('timeout', -1))
        self.once = self.param('once', False)

    def process(self, item):
        try:
            if not self.once or not self.cache.check(item):
                self.output(item)
        except StandardError:
            logging.exception("output exception")
            return False
        self.cache.add(item)
        return True

    def format_item(self, item):
        return self.template.render(item=item, output=self)

    def output(self, item):
        pass


class BufferOutput(OutputProcessor):
    name = "console"

    def output(self, item):
        msg = self.format_item(item)
        message = msg
        logging.info("\n"+message)

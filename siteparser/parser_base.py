import json
import logging
import time
import re
import requests
import cookielib
import hashlib
from jinja2 import Environment, Template

def regex_replace(s, find, replace):
    return re.sub(find, replace, s)

class Context(object):
    jinja = Environment()

Context.jinja.filters['regex_replace'] = regex_replace

class Item(object):
    _attributes = ['id', 'title', 'body', 'src', 'category', 'attachment', 'lifetime', 'data']

    def __init__(self, **kwargs):
        self.__data__ = kwargs
        # default item lifetime 7 days
        if self.lifetime == None:
           self.__data__['lifetime'] = 7*24*60*60

        if self.data == None or type(self.data) is not dict:
           self.__data__['data'] = {}

    def __getattr__(self, name):
        return self.__data__[name] if name in self._attributes and name in self.__data__ else None

    def __str__(self):
        return json.dumps( self.__data__ )

    @property
    def hash(self):
        h = hashlib.sha1()
        data = { key:value for key, value in self.__data__.iteritems() if key != 'data' }
        h.update(json.dumps(data, sort_keys=True, skipkeys=True))
        return h.hexdigest()

class SelfConstruct(object):
    @classmethod
    def subclass(cls, name):
        for sub_cls in cls.__subclasses__():
           if hasattr(sub_cls,'name') and sub_cls.name==name:
              return sub_cls
        return None


class Configurable(object):
    def __init__(self, params={}):
        self.params = params or {}
    def param(self, key, default=None):
        return self.params[key] if key in self.params else default
    def has_param(self, key):
        return key in self.params


class SiteParser(Configurable, SelfConstruct):
    def __init__(self, params={}):
        Configurable.__init__(self, params)
        self.session = requests.Session()
        self.session.cookies = cookielib.CookieJar()

    def make_request(self, url=None, data=None, headers=None):
        url = url or self.param('url')
        data = data or self.param('data')

        charset = self.param('encoding', 'utf-8')
        req_headers = {'Accept-Charset': charset}
        req_headers.update(headers or self.param('headers') or {})

        if data is not None:
            req = self.session.post(url, headers=req_headers, data=data)
        else:
            req = self.session.get(url, headers=req_headers)
        logging.debug(req.text)
        return req

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
    def filterValue(self,value):
       return True

class AllFilter(ItemFilter):
    name = "all"
    pass

class RegexpFilter(ItemFilter):
    name = "regexp"

    def __init__(self, params={}):
       ItemFilter.__init__(self, params)
       self.filters = [ re.compile(expr, re.I+re.M+re.U) for expr in self.param('matches',[]) ]
       pass

    def filterValue(self, item):
       for f in self.filters:
         if f.search(item.body) or f.search(item.title):
            return True
       return False


class ItemCache(object):
    def __init__(self, cache_file):
        self.cache_file = cache_file
        self.load()
        pass

    def load(self):
        self.cached = {}
        try:
            for x in json.load( open( self.cache_file, "rt" ) ):
                item = Item(**x)
                logging.debug(str(item))
                self.add( item, True )
        except:
           #logging.exception('on load cache')
           pass
        pass

    def save(self):
        try:
           now = time.time()
           for idx in self.cached.keys():
               if self.cached[idx].lifetime != None and self.cached[idx].lifetime>0 and (now-self.cached[idx].data['updated'])>self.cached[idx].lifetime:
                   del self.cached[idx]
           json.dump( [x.__data__ for x in self.cached.itervalues()], open(self.cache_file, "wt"), indent=2 )
        except:
           #logging.exception('on store cache')
           pass
        pass

    def check(self, item):
        idx = str(item.category)+'_'+str(item.id)
        if idx in self.cached.keys():
            cached_item = self.cached[idx]
            if cached_item.hash == item.hash:
                item.data.update( cached_item.data )
                return True
        return False

    def add(self, item, skip_update=False):
        idx = str(item.category)+'_'+str(item.id)
        if not skip_update:
           item.data['updated'] = time.time()
        self.cached[idx] = item

    def remove(self, item):
        idx = str(item.category)+'_'+str(item.id)
        if idx in self.cached.keys():
           del self.cached[idx]
        return


class OutputProcessor(Configurable, SelfConstruct):
    default_template = """Category: {{item.category}}
  Title: {{item.title}}
  Body: {{item.body}}
  Link: {{item.src}}"""

    def __init__(self, cache, params={}):
       Configurable.__init__(self, params)
       self.cache    = cache
       self.template = Context.jinja.from_string( self.param("template", self.default_template ) )
       self.timeout  = int( self.param('timeout', -1 ) )
       self.once     = self.has_param('once')

    def process(self, item):
        try:
            if not self.once or not self.cache.check(item):
               self.output( item )
        except Exception,e:
            logging.exception("output exception")
            return False
        self.cache.add( item )
        return True

    def format_item(self, item):
        return self.template.render(item=item, output=self)

    def output(self, item):
        pass


class BufferOutput(OutputProcessor):
    name = "console"

    def output(self, item):
        msg = self.format_item(item)
        message = msg.encode('utf-8')
        print message

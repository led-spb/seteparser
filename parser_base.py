import sys
import json, os
import logging
import time
import re
import requests
import hashlib
from jinja2 import Environment, Template

def regex_replace(s, find, replace):
    return re.sub(find, replace, s)

class Context(object):
  jinja = Environment()

Context.jinja.filters['regex_replace'] = regex_replace

def md5(val):
    h = hashlib.md5()
    h.update(val)
    return h.hexdigest()


class Item(object):
  _attributes = ['id', 'title', 'body', 'src', 'category', 'attachment', 'lifetime']

  def __init__(self, **kwargs):
      self.__data__ = kwargs
      # default item lifetime 7 days
      if self.lifetime == None:
         self.__data__['lifetime'] = 7*24*60*60

  def __getattr__(self, name):
      return self.__data__[name] if name in self._attributes and name in self.__data__ else None

  def __str__(self):
     return json.dumps( self.__data__ )


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
  def make_request(self, url=None, data=None, headers=None):
      url  = url or self.param('url')
      data = data or self.param('data')

      charset = self.param('encoding', 'utf-8')
      req_headers = {'Accept-Charset': charset}
      req_headers.update( headers or self.param('headers') or {} )

      if data!=None:
        req = requests.post( url, headers=req_headers, data=data )
      else:
        req = requests.get( url, headers=req_headers )
      return req

  def add(self, **kwargs):
      kwargs.update( {'category': self.param('instance')} )
      self.items.append( Item(**kwargs) )

  def parse(self):
      self.items = []
      return self.items

  def md5(self, arg):
      return md5(repr(arg))


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


class ItemExpirePolicy(object):
  def __init__(self, cache_file):
      self.cache_file = cache_file
      self.load()
      pass

  def load(self):
      self.cached = {}
      try:
          self.cached = json.load( open( self.cache_file, "rt" ) )
      except:
          pass
      pass

  def save(self):
      try:
         now = time.time()
         for idx in self.cached.keys():
             if self.cached[idx]['lifetime']!=None and self.cached[idx]['lifetime']>0 and (now-self.cached[idx]['updated'])>self.cached[idx]['lifetime']:
                 del self.cached[idx]
         json.dump( self.cached, open( self.cache_file, "wt" ) )
      except Exception, e:
         pass
      pass

  def expired(self, item, timeout=-1):
      now = time.time()
      idx = str(item.category)+'_'+str(item.id)
      if idx not in self.cached.keys() or (timeout>0 and (now-self.cached[idx]['updated']) > timeout):
         self.cached[idx] = {'lifetime': item.lifetime, 'updated': time.time()}
         return False

      self.cached[idx] = {'lifetime': item.lifetime, 'updated': time.time()}
      return True


class OutputProcessor(Configurable, SelfConstruct):
  default_template = """Category: {{item.category}}
Title: {{item.title}}
Body: {{item.body}}
Link: {{item.src}}"""

  def __init__(self, params={}):
     Configurable.__init__(self, params)
     self.template = Context.jinja.from_string( self.param("template", self.default_template ) )
     self.timeout  = int( self.param('timeout', -1 ) )
     self.once     = self.has_param('once')

  def process(self, item):
      try:
        self.output( item )
      except Exception,e:
        logging.exception("output exception")
        pass
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
      print

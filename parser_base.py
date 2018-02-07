import sys
import json, os
import logging
import time
import re
from jinja2 import Environment, Template

def regex_replace(s, find, replace):
    return re.sub(find, replace, s)

class Context(object):
  jinja = Environment()

Context.jinja.filters['regex_replace'] = regex_replace



class Item(object):
  _attributes = ['id','title','body','src','category','added', 'attachment']

  def __init__(self, **kwargs):
      self.__data__ = kwargs

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
  def parse(self):
      return []

class ItemFilter(Configurable, SelfConstruct):
  def filterValue(self,value):
     return True

class AllFilter(ItemFilter):
  name = "all"
  pass

class RegexpFilter(ItemFilter):
  name = "regexp"

  def _init_filters(self):
     if hasattr(self, 'filters'):
        return
     self.filters = [ re.comile(expr, re.I+re.M+re.U) for expr in self.param('matches',[]) ]
     pass

  def filterValue(self,value):
     self._init_filters()

     for f in self.filters:
       if f.search(item.body) or f.search(item.title):
          return True
     return False


class OutputProcessor(Configurable, SelfConstruct):
  default_template = """Category: {{item.category}}
Title: {{item.title}}
Body: {{item.body}}
Link: {{item.src}}"""

  def __init__(self, params=[]):
     Configurable.__init__(self,params)
     self.cached = {}

     self.cache_file = '.'+os.path.splitext( os.path.basename(sys.argv[0]) )[0]
     self.template = Context.jinja.from_string( self.param("template", self.default_template ) )
     self.timeout = int( self.param('timeout', -1 ) )
     self.once  = self.has_param('once')
     try:
       self.cached = json.load( open( self.cache_file, "rt" ) )
     except:
       pass

  def process(self, item):
      now = time.time()
      if self.once:
         h = str(item.id)
         if h in self.cached and ( self.timeout==-1 or (now-self.cached[h]) < self.timeout ):
            return False
      try:
        self.output( item )
        if self.once:
           self.cached[h] = time.time()
      except Exception,e:
        logging.exception("output exception")
        pass
      return True

  def format_item(self, item):
      return self.template.render(item=item, output=self)

  def output(self, item):
      pass

  def finish(self):
      if self.once:
         try:
           json.dump( self.cached, open( self.cache_file, "wt" ) )
         except Exception, e:
           pass
      return


class BufferOutput(OutputProcessor):
  name = "console"

  def output(self, item):
      msg = self.format_item(item)
      message = msg.encode('utf-8')
      print message
      print

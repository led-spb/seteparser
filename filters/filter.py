import re

class ItemFilter(object):
  def __init__(self, params):
     self.params = params
     pass
  def filterValue(self,value):
     return True

class NoneFilter(ItemFilter):
  name = "all"
  pass


class RegexpFilter(ItemFilter):
  name = "regexp"
  def __init__(self,params):
    self.filters = []
    if params==None:
       return
    for text in params:
       self.filters.append( re.compile( unicode(text,'utf-8'), re.I+re.U ) )

  def filterValue(self,value):
    for f in self.filters:
      if f.search(value):
         return True
    return False

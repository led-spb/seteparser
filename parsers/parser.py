class SiteParser(object):
  def __init__(self, params):
      self.parser_params = [] if params==None else params

  def get_param(self, key, default=None):
    try:
       return self.parser_params[ self.parser_params.index(key)+1 ]
    except:
       return default

  def parse(self):
      return []

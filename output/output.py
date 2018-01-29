import hashlib
md5 = hashlib.md5
import json
import sys, os.path, time, logging


class OutputProcessor(object):
  def __init__(self, params):
     self.cached = {}
     self.cache_file = '.'+os.path.splitext( os.path.basename(sys.argv[0]) )[0]
     self.params = params if params!=None else []

     self.timeout = int( self.get_param(params, 'timeout', -1 ) )
     self.once  = 'once' in self.params

     try:
       self.cached = json.load( open( self.cache_file, "rt" ) )
     except:
       pass


  def get_param(self, params, key, default=None):
      try:
         return unicode(params[ params.index(key)+1 ], 'utf-8')
      except:
         return default


  def process(self, value, parser_name):
      now = time.time()
      if self.once:
         hash = md5()
         hash.update( parser_name )
         hash.update( value.encode("utf-8") )
         h = hash.hexdigest()

         if h in self.cached and ( self.timeout==-1 or (now-self.cached[h]) < self.timeout ):
            return False

      try:
        self.output( value, parser_name )

        if self.once:
           self.cached[h] = time.time()
      except Exception,e:
        logging.exception("output exception")
        pass

      return True


  def output(self, value, parser_name):
      print value


  def finish(self):
      try:
        json.dump( self.cached, open( self.cache_file, "wt" ) )
      except Exception, e:
        pass
      return


class BufferOutput(OutputProcessor):
  name = "console"

  def output(self, value, parser_name):
      print value.encode('utf-8')
      print

#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests

import logging
import os.path, sys
import argparse

sys.path.insert(0, os.path.dirname(sys.argv[0]) )

from parsers import *
from filters import *
from output  import *


class Application():
   def __init__(self):
      self.parse_arguments()

      logging.getLogger("requests").setLevel(logging.ERROR)
      logging.getLogger("urllib3").setLevel(logging.ERROR)

      #logging.captureWarnings(True)
      logging.basicConfig( format = u'%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s', level = logging.DEBUG if self.params.debug else logging.INFO )
      logging.getLogger("requests").setLevel( level = logging.DEBUG if self.params.debug else logging.WARNING  )
      return

   def parse_arguments(self):
       parser = argparse.ArgumentParser()

       parser.add_argument( "-v", action="store_const", default=0, const=1, dest="debug" )

       parser.add_argument( "-p",  "--parser",  required=True, choices= [c.name for c in SiteParser.__subclasses__()] )
       parser.add_argument( "-pp", "--parser-param",  dest="parser_params", nargs="*" )

       parser.add_argument( "-f",  "--filter",  required=False, choices = [c.name for c in ItemFilter.__subclasses__()], default='all' )
       parser.add_argument( "-ff", "--filter-param",  dest="filter_params", nargs="*" )

       parser.add_argument( "-o",  "--output", required=False, choices= [c.name for c in OutputProcessor.__subclasses__()], default='console' )
       parser.add_argument( "-oo", "--output-param", dest="output_params", nargs="*" )

       self.params = parser.parse_args()
       pass


   def find_class(self,classes, name):
       for c in classes:
          if c.name == name:
             return c
       return None


   def main(self):

       # create site parser
       parser = self.find_class(SiteParser.__subclasses__(),  self.params.parser )( self.params.parser_params  )
       # filter 
       filter = self.find_class(ItemFilter.__subclasses__(),  self.params.filter )( self.params.filter_params )
       # output
       output = self.find_class(OutputProcessor.__subclasses__(), self.params.output )( self.params.output_params )

       # parse data
       items = parser.parse()
       for item in items:
          if filter.filterValue(item):
             output.process(item, parser.__class__.__name__)
       output.finish()
       exit()
       pass


################################
################################
################################

app = Application()
app.main()

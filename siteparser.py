#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import os.path
import argparse
import json
from parser_base import *
import parsers
import outputs

import yaml

class Loader(yaml.Loader):
    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        self._secrets = None
        super(Loader, self).__init__(stream)

    def _load_secret_yaml(self, fname):
        try:
           with open(fname, 'r') as conf_file:
              return yaml.load(conf_file)
        except:
           logging.exception("Unable to load secrets.yaml")
        return {}
    
    def include(self, node):
        filename = os.path.join(self._root, self.construct_scalar(node))
        with open(filename, 'r') as f:
            return yaml.load(f, Loader)

    def secret(self, node):
        if self._secrets == None:
           self._secrets = self._load_secret_yaml( os.path.join( self._root, 'secrets.yaml' ) )
        if node.value in self._secrets:
           return self._secrets[node.value]
        return None

Loader.add_constructor('!secret',  Loader.secret)
Loader.add_constructor('!include', Loader.include)


class Application():
   def __init__(self):
      self.parse_arguments()

      logging.captureWarnings(True)
      logging.basicConfig( format = u'%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s', level = logging.DEBUG if self.config['debug'] else logging.INFO )
      logging.getLogger("requests").setLevel( level = logging.DEBUG if self.config['debug'] else logging.WARNING  )

      logging.debug( "Loaded configuration: %s", json.dumps( self.config, indent=2) )
      return

   def parse_arguments(self):
       parser = argparse.ArgumentParser()

       parser.add_argument( "-v", action="store_const", const=1, dest="debug" )
       parser.add_argument( "-c", "--config", type=file, default="siteparser.yaml" )
       args = parser.parse_args()

       self.config = {'debug': False, 'feeds': [] }
       self.config.update( yaml.load( args.config, Loader ) )
       if args.debug != None:
          self.config['debug'] = True
       pass

   def main(self):
       for data in self.config['feeds']:
           logging.info("Processing feed \"%s\"", data['name'] )
           items = []
           try:
              parser = SiteParser.subclass( data['parser']['type'] )( data['parser'] )
              items = parser.parse()

              if 'filter' in data:
                 filter_item = FilterItem.subclasss( data['filter']['type'] )( data['filter'] )
                 items = [ item for item in items if filter_item.filterValue(item) ]

              if 'output' in data:
                 output = OutputProcessor.subclass( data['output']['type'] )( data['output'] )
              else:
                 output = OutputProcessor.subclass( 'console' )()

              for item in items:
                  output.process(item)
              output.finish()
           except:
              logging.exception('Error while processing feed "%s"', data['name'])
       pass


################################
################################
################################
app = Application()
app.main()

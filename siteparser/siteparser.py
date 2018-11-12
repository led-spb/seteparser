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
        file_list = self.construct_scalar(node).split(' ')
        result = None

        for fn in file_list:
          filename = os.path.join(self._root, fn)

          with open(filename, 'r') as f:
             item = yaml.load(f, Loader)
             if result==None:
                result = item
             elif type(item)==list:
                result+=item
             else:
                result.append( item )
        return result

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
      logging.basicConfig(
          format = u'%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s',
          level = logging.DEBUG if self.config['debug'] else logging.INFO,
          filename = self.config['logfile']
      )
      logging.getLogger("requests").setLevel( level = logging.DEBUG if self.config['debug'] else logging.WARNING )
      logging.getLogger("chardet.charsetprober").setLevel( logging.CRITICAL )

      logging.debug( "Loaded configuration: %s", json.dumps( self.config, indent=2) )
      return

   def parse_arguments(self):
       parser = argparse.ArgumentParser()

       parser.add_argument( "-v", action="store_const", const=1, dest="debug" )
       parser.add_argument( "-c", "--config", type=file, default="siteparser.yaml" )
       args = parser.parse_args()

       self.config = {'debug': False, 'feeds': [], 'logfile': None}
       self.config.update( yaml.load( args.config, Loader ) )
       if args.debug != None:
          self.config['debug'] = True
       pass

   def main(self):
       expire_policy = ItemExpirePolicy( cache_file='.'+os.path.splitext(os.path.basename(sys.argv[0]))[0] )

       for data in self.config['feeds']:
           if 'enabled' in data and data['enabled']!=True:
               continue
           logging.info("Processing feed \"%s\"", data['name'] )
           items = []
           try:
              data['parser'].update({'instance': data['name']})

              parser = SiteParser.subclass( data['parser']['type'] )( data['parser'] )
              items = parser.parse()

              if 'filter' in data:
                 filter_item = ItemFilter.subclass( data['filter']['type'] )( data['filter'] )
                 items = [ item for item in items if filter_item.filterValue(item) ]

              outputs = []
              if 'output' in data:
                 if type(data['output']) != list:
                     data['output'] = [data['output']]

                 for item in data['output']:
                     output = OutputProcessor.subclass( item['type'] )( item )
                     outputs.append( output )
              else:
                 output = OutputProcessor.subclass( 'console' )()
                 outputs.append( output )

              for output in outputs:
                  for item in items:
                      if not output.once or not expire_policy.expired(item, output.timeout):
                          if not output.process(item):
                              expire_policy.remove(item)
                      pass
           except:
              logging.exception('Error while processing feed "%s"', data['name'])

       expire_policy.save()
       pass


def main():
    app = Application()
    app.main()


if __name__ == "__main__":
    main()
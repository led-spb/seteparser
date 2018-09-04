from parser_base import SiteParser, Item
import requests
import lxml.cssselect
import lxml.etree
import lxml.html

import hashlib
md5 = hashlib.md5


class SimpleParser(SiteParser):
   name = "simple"

   def parse(self):
       self.items=[]
       req = self.make_request()
       eval_string = self.param('eval')
       if eval_string==None:
          raise Exception('eval string is None')

       exec( eval_string, {"request": req, "self": self} )
       return self.items


class CssPaser(SiteParser):
   name = "css"

   def parse(self):
       self.items = []
       eval_string = self.param('eval')

       if eval_string==None:
          raise Exception('eval string is None')

       req = self.make_request()
       req.encoding = 'utf-8'
       tree = lxml.html.fromstring( req.text )

       exec( eval_string, {"request": req, "tree": tree, "self": self} )
       return self.items

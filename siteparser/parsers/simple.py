from siteparser.parser_base import SiteParser, Item
import requests
import lxml.cssselect
import lxml.etree
import lxml.html


class SimpleParser(SiteParser):
   name = "simple"

   def etree(self, string):
       return lxml.html.fromstring( string )

   def parse(self):
       self.items=[]

       eval_string = self.param('eval')
       if eval_string==None:
           raise Exception('eval string is None')

       req = self.make_request()
       tree = None
       try:
           req.encoding = 'utf-8'
           tree = self.etree( req.text )
       except:
           pass

       exec( eval_string, {"self": self, "request": req, "tree": tree} )
       return self.items


class CssPaser(SimpleParser):
   name = "css"

   def parse(self):
       self.items = []
       eval_string = self.param('eval')

       if eval_string==None:
           raise Exception('eval string is None')

       req = self.make_request()
       req.encoding = 'utf-8'
       tree = self.etree( req.text )

       exec( eval_string, {"request": req, "tree": tree, "self": self} )
       return self.items

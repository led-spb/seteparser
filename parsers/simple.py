from parser_base import SiteParser, Item
import requests
import lxml.cssselect
import lxml.etree
import lxml.html

class CssPaser(SiteParser):
   name = "css"

   def parse(self):
       items = []

       url  = self.param('url')
       data = self.param('post')

       charset = self.param('encoding', 'utf-8')
       css     = self.param("query")

       eval_string = self.param('eval')
       if data!=None:
         req = requests.post( url, headers={'Accept-Charset': charset}, data=data )
       else:
         req = requests.get( url, headers={'Accept-Charset': charset} )

       req.encoding='utf-8'
       html = req.text

       tree = lxml.html.fromstring( html )
       sel = lxml.cssselect.CSSSelector( css )
       
       items = []
       for element in sel(tree):
          exec( eval_string, {"items":items, "Item": Item, "element": element} )
       return items
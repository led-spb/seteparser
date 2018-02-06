from parser_base import SiteParser, Item, Context
import re
import requests


class SimpleParser(SiteParser):
  name = "simple"

  def get_param(self, key, default=None):
    try:
       return unicode(self.parser_params[ self.parser_params.index(key)+1 ], 'utf-8')
    except:
       return default

  def parse(self):
      items = []

      url  = self.get_param('url')
      post_data = self.get_param('post')
      charset = self.get_param('charset', 'utf-8')

      p = re.compile( self.get_param('item',''), re.I + re.U + re.M+ re.S )

      req = requests.get( url, headers={'Accept-Charset': charset} )
      html = req.text if charset==None else req.content.decode( charset )

      items = []
      for m in p.finditer(html):
         item = m.group(1)
         items.append( item )
      return items


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
       
       #items = [ unicode(template.render(item = e)) for e in sel(tree) ]
       items = []
       for element in sel(tree):
          exec( eval_string, {"items":items, "Item": Item, "element": element} )
       return items
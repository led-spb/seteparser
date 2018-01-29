import re
import parser
import requests


class SimpleParser(parser.SiteParser):
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

from jinja2 import Environment, Template

# Custom filter method
def regex_replace(s, find, replace):
    """A non-optimal implementation of a regex filter"""
    return re.sub(find, replace, s)

jinja_environment = Environment()
jinja_environment.filters['regex_replace'] = regex_replace


class CssPaser(parser.SiteParser):
   name = "css"

   def parse(self):
       items = []

       url  = self.get_param('url')
       data = self.get_param('post')

       charset = self.get_param('encoding', 'utf-8')
       css     = self.get_param("css")

       template = jinja_environment.from_string(self.get_param("template", "{{ item.text_content() }}" ) )

       if data!=None:
         req = requests.post( url, headers={'Accept-Charset': charset}, data=data )
       else:
         req = requests.get( url, headers={'Accept-Charset': charset} )

       html = req.text if charset==None else req.content.decode( charset )

       tree = lxml.html.fromstring( html )
       sel = lxml.cssselect.CSSSelector( css )

       items = [ unicode(template.render(item = e)) for e in sel(tree) ]
       return items
       
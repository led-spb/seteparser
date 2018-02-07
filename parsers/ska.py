import re, json
from parser_base import SiteParser, Item
import requests

class SkaParser(SiteParser):
   name = "ska"

   def parse(self):
       self.sess = requests.Session()

       req = self.sess.get('https://tickets.ska.ru/')

       filter_text = re.compile(u'<div class="ticket__date">(.*?)</div>.*?<span class="ticket__team-name">(.*?)</span>.*?<span class="ticket__team-name">(.*?)</span>.*?<a\\s+href="(.*?)".*?class="ticket__buy"', re.I+re.U+re.M )

       items = []
       for m in filter_text.finditer( req.text ):
          seats = ""#self.parse_seats( m.group(4) )
          item = m.group(1)+" "+m.group(2)+"-"+m.group(3)+"\n"+seats
          items.append( unicode(item,'utf-8') )
       return items
   
   def parse_seats(self, url):
       s = ""
       data = []
       req = self.sess.get( 'https://tickets.ska.ru'+url )

       filter_text = re.compile(u'var ZONES = (\[.*?\]);', re.M )
       m = filter_text.search( req.rext )
       if m!=None:
          data = json.loads( m.group(1) )

       for zone in data:
           prices = zone['price']
           price_min = min(prices)
           price_max = max(prices)     
              
           if int(zone['quant'])>0:
              s = s +"%s: %d-%d - %d\n" % (zone['name'], price_min, price_max, int(zone['quant']) )
       return s
   
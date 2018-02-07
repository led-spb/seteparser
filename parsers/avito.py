# -*- coding: utf-8 -*-
import re, urllib2
from parser_base import SiteParser, Item
from pyquery import PyQuery

class AvitoParser(SiteParser):
   name = "avito"

   def parse(self):
       items = []
       url = self.param('url')
       base_path = url

       d = PyQuery(url)
       for data in d('.item_table').items():
           descr = data.find(".description") 

           title = descr.find(".title").text()
           price = descr.find(".about").text()
           url   = descr.find("a").attr("href")
           if re.search('^http(s?)://', url)==None:
              url = "https://www.avito.ru" + url
           item = Item( id=url, title=title, body=price, src=url, category='avito' )
           items.append( item )
       return items

if __name__=='__main__':
   parser = AvitoParser(
         {'url': 'https://www.avito.ru/sankt-peterburg/sport_i_otdyh?user=1&bt=1&i=1&q=%D1%85%D0%BE%D0%BA%D0%BA%D0%B5%D0%B9' } 
   )
   items = parser.parse()
   for item in items:
      print str(item)
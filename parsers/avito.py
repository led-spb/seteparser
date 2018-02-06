import re, urllib2
import parser
from pyquery import PyQuery

class AvitoParser(parser.SiteParser):
   name = "avito"

   def parse(self):
       items = []
       city  = self.get_param('city', 'sankt-peterburg')

       base_path = 'https://www.avito.ru'
       url = "%s/%s/%s??bt=1&i=1&user=1" %  (base_path, city, self.get_param('category') ) #,'/sankt-peterburg/tovary_dlya_detey_i_igrushki/detskie_kolyaski?bt=1&i=1&user=1'

       d = PyQuery(url)
       for data in d('.item_table').items():
           descr = data.find(".description") 

           title = descr.find(".title").text().encode("utf-8")
           price = descr.find(".about").text().encode("utf-8")
           url   = descr.find("a").attr("href")

           items.append("<a href=\"%s%s\">%s: %s</a>" % (base_path,url, title,price) )
       return items

if __name__=='__main__':
   parser = AvitoParser(['city', 'sankt-peterburg',  'category','tovary_dlya_detey_i_igrushki/detskie_kolyaski' ])
   print parser.parse()
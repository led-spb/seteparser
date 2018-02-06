import requests
from parser_base import SiteParser, Item


class NhlParser(SiteParser):
   name = "nhl"

   def parse(self):
       self.sess = requests.Session()
       req = self.sess.get('https://search-api.svc.nhl.com/svc/search/v2/nhl_nr_en/tag/content/gameRecap?page=1&sort=new&type=video')
       items = []
       for doc in req.json()['docs']:
          item = Item( id=doc['asset_id'], title=doc['title'], body=doc['bigBlurb'], src=doc['url'], category=self.name )
          items.append( item )
       req.close()
       return items

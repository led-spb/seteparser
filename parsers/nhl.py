import parser, requests

class NhlParser(parser.SiteParser):
   name = "nhl"

   def parse(self):
       self.sess = requests.Session()
       req = self.sess.get('https://search-api.svc.nhl.com/svc/search/v2/nhl_nr_en/tag/content/gameRecap?page=1&sort=new&type=video')
       items = []
       for item in req.json()['docs']:
          items.append( item['url'] )
       return items

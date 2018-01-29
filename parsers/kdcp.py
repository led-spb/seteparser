# -*- coding: utf-8 -*-
import parser
import re
import requests


class KdcpParser(parser.SiteParser):
  name = "kdc"

  def parse(self):
      # start session
      if int( self.get_param('dms',0)) !=0 :
         dms = 1
      else:
         dms = 0

      self.sess = requests.Session()
      self.sess.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36'}
      self.sess.get( 'http://kdcd.spb.ru/samozapis/index.php' )

      req = self.sess.post( 'http://kdcd.spb.ru/samozapis/save_mode.php',  data = {'mode':1, 'dms': dms}, headers={ 'Referer': 'http://kdcd.spb.ru/samozapis/index.php'}  )
      req = self.sess.get( 'http://kdcd.spb.ru/samozapis/speciality.php?flag=1' )

      p = re.compile( u'<div class="yellow_button">(.*?)</div>', re.M+re.DOTALL)
      p1 = re.compile( u'<input(.*?)>', re.I+re.M+re.DOTALL )

      html = req.text

      items = []
      for m in p.finditer( html ):
          data = m.group(1)
          spec = {}

          for m1 in p1.finditer( data ):
              data = m1.group(1)
              name  = re.search( 'name\\s*=\\s*"(.*?)"', data).group(1)
              value = re.search( 'value\\s*=\\s*"(.*?)"', data).group(1)
              spec[ name ] = value
          #
          doctors = self.parse_spec(spec)
          for doc in doctors:
              items.append( u"%s/%s" % (spec['specname'], doc) )
      req.close()
      return items


  def parse_spec(self, spec):
      req  = self.sess.post( 'http://kdcd.spb.ru/samozapis/doctors_lpu.php', data = spec )
      html = req.text

      p = re.compile('<div class="yellow_button"[^>]*>\s*<span>([^<]*)</span>', re.I+re.M+re.U)
      items = []
      for m in p.finditer( html):
         item = m.group(1)
         items.append( item )
      req.close()
      return items
      
if __name__=='__main__':
   import sys, logging
   logging.basicConfig( format = u'%(asctime)s\t%(process)d\t%(levelname)s\t%(message)s', level = logging.DEBUG )

   parser = KdcpParser( sys.argv )
   print parser.parse()

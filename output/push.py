import requests
from output import OutputProcessor


class PushOutput(OutputProcessor):
  name = "push"

  def notify(self, token, title, body, priority=0):
      pass

  def __init__(self,params):
     OutputProcessor.__init__(self, params)
     self.token = self.get_param(params,'token','')
     self.title = self.get_param(params,'title','Site parser')


  def output(self,value, parser_name):
      requests.post(
             'https://api.pushbullet.com/v2/pushes',
             params  = {'type':'note',  'title': self.title.encode('utf-8'), 'body': value.encode('utf-8') },
             headers = {'Authorization':'Basic '+self.token.encode('base64').rstrip() }
      )
      return True



class NotifyOutput(OutputProcessor):
   name = "notify"

   def output(self, value, parser_name ):
       requests.post( "http://localhost:1978/message", data=value.encode("utf-8") )
       pass
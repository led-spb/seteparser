import requests
from output import OutputProcessor

class TelegramOutput(OutputProcessor):
  name = "telegram"

  def __init__(self,params):
     OutputProcessor.__init__(self, params)
     self.token  = self.get_param(params,'token','')
     self.target = self.get_param(params,'target','')

  def output(self,value, parser_name):
      message = {
        'chat_id': self.target,
        'parse_mode': 'HTML',
        'text': value
      }
      req = requests.post(
             'https://api.telegram.org/bot%s/sendMessage' % self.token,
             params = message
      )
      return True

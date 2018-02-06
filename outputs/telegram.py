import requests
from parser_base import OutputProcessor, Item

class TelegramOutput(OutputProcessor):
  name = "telegram"

  def output(self, item):
      message_text =  self.format_item(item)
      message = {
        'chat_id':    self.param('chat_id'),
        'parse_mode': 'HTML',
        'text':       message_text
      }
      req = requests.post(
             'https://api.telegram.org/bot%s/sendMessage' % self.param('token'),
             params = message
      )
      req.raise_for_status()
      return True

import requests
import json
import base
from cStringIO import StringIO


class TelegramOutput(base.OutputProcessor):
    name = "telegram"

    def __init__(self, cache, params=None):
        super(TelegramOutput, self).__init__(cache, params)
        self.session = requests.Session()
        self.session.proxies = self.param('proxy', None)
        self.extra_options = self.param('options', {})

    def build_message(self, message):
        message.update(self.extra_options)
        return message

    def output(self, item):
        # send message body
        chat_id = self.param('chat_id')
        message_text = self.format_item(item)

        message = self.build_message({
            'chat_id': chat_id,
            'parse_mode': 'HTML',
            'text': message_text[:4096]
        })
        req = self.session.post(
            'https://api.telegram.org/bot%s/sendMessage' % (self.param('token')), json=message
        )
        req.raise_for_status()

        # send attachments
        media_group = []
        files = {}
        for attach in item.attachments or []:
            if attach.endswith('.jpg') or attach.endswith('.png') or attach.endswith('.gif'):
                # Collect all photos - they will be send via media group
                image_content = self.session.get(attach)
                file_id = "media_%03d" % (len(media_group) + 1)
                media_group.append({
                    'type': 'photo',
                    'media': 'attach://%s' % file_id
                })
                files[file_id] = StringIO(image_content.content)
            else:
                # All others attachments send via direct link
                message = self.build_message({
                    'chat_id': self.param('chat_id'),
                    'parse_mode': 'HTML',
                    'disable_notification': True,
                    'text': attach
                })
                self.session.post(
                    'https://api.telegram.org/bot%s/sendMessage' % (self.param('token')), json=message
                )
            pass

        if len(media_group) > 0:
            message = self.build_message({
                    'chat_id': self.param('chat_id'),
                    'disable_notification': True,
                    'media': json.dumps(media_group)
            })
            self.session.post(
                'https://api.telegram.org/bot%s/sendMediaGroup' % (self.param('token')),
                data=message,
                files=files
            )
        return True

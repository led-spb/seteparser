import requests
import base
from cStringIO import StringIO
try:
    import youtube_dl
except ImportError:
    pass


class TelegramOutput(base.OutputProcessor):
    name = "telegram"

    def output(self, item):
        download_video = self.param('download_video', False) \
                         and item.src is not None \
                         and self.download_supported(item.src)

        self.session = requests.Session()
        self.session.proxies = self.param('proxy', None)

        # send message body
        if not download_video or not self.param('only_video', False):
            chat_id = self.param('chat_id')

            message_text = self.format_item(item)
            for step in range(2):
                message = {
                    'chat_id': chat_id,
                    'parse_mode': 'HTML',
                    'text': message_text
                }
                method = 'sendMessage'
                if step == 0 and self.param('edit_messages', False) and \
                        'message_id' in item.data and item.data['chat_id'] == chat_id:
                    message['message_id'] = item.data
                    method = 'editMessageText'

                req = self.session.post(
                    'https://api.telegram.org/bot%s/%s' % (self.param('token'), method),
                    json=message
                )
                if method == 'editMessageText' and req.status_code != 200:
                    continue

                req.raise_for_status()
                result = req.json()['result']

                chat_id = result['chat']['id']
                message_id = result['message_id']

                item.data['chat_id'] = chat_id
                item.data['message_id'] = message_id
                break

        # send attachments
        for attach in item.attachments or []:
            if attach.endswith('.jpg') or attach.endswith('.png') or attach.endswith('.gif'):
                image = self.session.get(attach)
                self.session.post(
                    'https://api.telegram.org/bot%s/sendPhoto' % (self.param('token')),
                    data={
                        'chat_id': self.param('chat_id'),
                        'disable_notification': True
                    },
                    files={'photo': StringIO(image.content)}
                )
            else:
                message = {
                    'chat_id': self.param('chat_id'),
                    'parse_mode': 'HTML',
                    'disable_notification': True,
                    'text': attach
                }
                self.session.post(
                    'https://api.telegram.org/bot%s/sendMessage' % (self.param('token')),
                    json=message
                )
            pass
        return True

    def download_supported(self, url):
        for ie in youtube_dl.extractor.gen_extractors():
            if ie.suitable(url) and ie.IE_NAME != 'generic':
                return True
        return False

    def download_video(self, url):
        ydl_opts = {}
        ydl_opts.update(self.param('ydl_opts', {}))

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(url)
            return ydl.prepare_filename(res)

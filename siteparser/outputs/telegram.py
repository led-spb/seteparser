import requests
import os
from siteparser.parser_base import OutputProcessor, Item
try:
    import youtube_dl
except:
    pass


class TelegramOutput(OutputProcessor):
    name = "telegram"

    def output(self, item):
        download_video = self.param('download_video',False) and item.src!=None and self.download_supported(item.src)

        self.session = requests.Session()
        self.session.proxies = self.param('proxy', None)

        # send message body
        if not download_video or not self.param('only_video',False):
            targets = self.param('chat_id')
            if type(targets)!=list:
                targets=[targets]

            for chat_id in targets:
                message_text =  self.format_item(item)
                message = {
                  'chat_id':    chat_id,
                  'parse_mode': 'HTML',
                  'text':       message_text
                }
                req = self.session.post(
                      'https://api.telegram.org/bot%s/sendMessage' % self.param('token'),
                      json = message
                )
                req.raise_for_status()

        # send video
        if download_video and 'youtube_dl' in dir():
           filename = self.download_video(item.src)
           video = {
             'chat_id': self.param('chat_id'),
             'caption': item.title
           }
           req = self.session.post(
                  'https://api.telegram.org/bot%s/sendVideo' % self.param('token'),
                  params = video,
                  files = { 'video': (filename, open(filename,'rb'), 'video/mp4') }
           )
           req.raise_for_status()
           os.remove( filename )
        return True

    def download_supported(self, url):
        for ie in youtube_dl.extractor.gen_extractors():
            if ie.suitable(url) and ie.IE_NAME != 'generic':
                return True
        return False

    def download_video(self, url):
        ydl_opts = {}
        ydl_opts.update( self.param('ydl_opts',{}) )

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info( url )
            return ydl.prepare_filename( res )

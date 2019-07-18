#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os.path
import argparse
import yaml
import logging
import json
import time
import base
from parsers import CssParser, SimpleParser
from outputs import TelegramOutput
from _version import __version__

class Loader(yaml.Loader):
    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        self._secrets = None
        super(Loader, self).__init__(stream)

    @staticmethod
    def _load_secret_yaml(fname):
        try:
            with open(fname, 'r') as conf_file:
                return yaml.load(conf_file)
        except StandardError:
            logging.exception("Unable to load secrets.yaml")
        return {}

    def include(self, node):
        file_list = self.construct_scalar(node).split(' ')
        result = None

        for fn in file_list:
            with open(os.path.join(self._root, fn), 'r') as f:
                item = yaml.load(f, Loader)
                if result is None:
                    result = item
                elif isinstance(item, list):
                    result += item
                else:
                    result.append(item)
        return result

    def secret(self, node):
        if self._secrets is None:
            self._secrets = self._load_secret_yaml(os.path.join(self._root, 'secrets.yaml'))
        current_value = self._secrets
        for element in node.value.split('.'):
            if element in current_value:
                current_value = current_value[element]
            else:
                return None
        return current_value


Loader.add_constructor('!secret', Loader.secret)
Loader.add_constructor('!include', Loader.include)


class Application(object):
    def __init__(self):
        self.config = {}
        self.parse_arguments()

        logging.captureWarnings(True)
        logging.basicConfig(
            format=u'%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s',
            level=logging.DEBUG if self.config['debug'] else logging.INFO,
            filename=self.config['logfile']
        )
        logging.getLogger("requests").setLevel(level=logging.DEBUG if self.config['debug'] else logging.WARNING)
        logging.getLogger("chardet.charsetprober").setLevel(logging.CRITICAL)

        logging.debug("Loaded configuration: %s", json.dumps(self.config, indent=2))
        return

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description='%(prog)s: '+ __version__)

        parser.add_argument("--version", action='version', version='%(prog)s '+ __version__)
        parser.add_argument("-v", action="store_const", const=1, dest="debug")
        parser.add_argument("-c", "--config", type=file, default="siteparser.yaml")
        args = parser.parse_args()

        self.config = {'debug': False, 'feeds': [], 'logfile': None}
        self.config.update(yaml.load(args.config, Loader))
        if args.debug is not None:
            self.config['debug'] = True
        pass

    def main(self):
        now = time.time()
        storage = base.KeyStorage(filename='.' + os.path.splitext(os.path.basename(sys.argv[0]))[0])
        cache = base.ItemCache(storage)
        parsers = []

        default_output = self.config['output'] if 'output' in self.config else {'type': 'console'}
        schedules = {}
        default_scheduler = base.Schedule()
        if 'schedule' in self.config:
            for name, params in self.config['schedule'].items():
                schedules[name] = base.Schedule(params)

        for data in self.config['feeds']:
            if 'enabled' in data and not data['enabled']:
                continue
            try:
                data['parser'].update({'instance': data['name']})

                parser = base.SiteParser.subclass(data['parser']['type'])(storage, data['parser'])
                parsers.append(parser)
                schedule = default_scheduler
                if 'schedule' in data:
                    if type(data['schedule']) is dict:
                        schedule = base.Schedule(data['schedule'])
                    elif data['schedule'] in schedules:
                        schedule = schedules[data['schedule']]

                if not schedule.is_trigger(now, parser):
                    logging.debug("Skipping feed \"%s\"", data['name'])
                    continue

                logging.info("Processing feed \"%s\"", data['name'])
                items = parser.parse()

                if 'filter' in data:
                    filter_item = base.ItemFilter.subclass(data['filter']['type'])(data['filter'])
                    items = [item for item in items if filter_item.filter(item)]

                output_params = default_output.copy()
                if 'output' in data:
                    output_params.update(data['output'])

                output = base.OutputProcessor.subclass(output_params['type'])(cache, output_params)
                logging.debug('Using %s output processor', output.__class__.__name__)
                for item in items:
                    output.process(item)
                    pass

                parser.last_timestamp = now
            except StandardError:
                logging.exception('Error while processing feed "%s"', data['name'])

        storage.put('timestamps', {x.instance_name: x.last_timestamp for x in parsers})
        cache.save()
        storage.save()
        pass


def main():
    app = Application()
    app.main()


if __name__ == "__main__":
    main()

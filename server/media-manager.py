#!/usr/bin/env python

import sys
import os
import argparse
import requests
import json


if __name__ == '__main__':
    bp_ = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    if bp_ not in [os.path.abspath(x) for x in sys.path]:
        sys.path.insert(0, bp_)

import utilities as utils
LOG = utils.ColorLog(name='media-manager', debug=False)


class GenericCommand:
    def __init__(self):
        self.__active=False

    def activate(self):
        self.__active=True

    def isActive(self):
        return self.__active

    def isCompleted(self):
        if not self.__active:
            raise AttributeError('Command is NOT active!')

    def execute(self, url):
        raise Exception('execute method is NOT implemented!')

class List(GenericCommand):
    def execute(self, url):
        LOG.info('get list of files action')
        try:
            r_ = requests.get(url=url + 'catalog')
            if r_.status_code != requests.codes.ok:
                LOG.warning('Not found any MultiMedia object!')

            else:
                LOG.debug("Response=%s" % r_.text)
                self.show(r_.json()['catalog'])

        except requests.exceptions.RequestException as exc:
            LOG.critical(str(exc))

    def show(self, catalog):
        print '\n'
        idx_ = 0
        for i in catalog:
            print '[' + str(idx_) + ']\t' + i['title']
            idx_ += 1
        print '\n'

    def helpMsg(self):
        return 'list' + '\tGet a list of all stored music files'


commands = {'list': List(),}

class CmdManager:
    def __init__(self):
        self.url_ = None

    def analyze(self, key):
        commands[key].isCompleted()

    def execute(self, key):
        commands[key].execute(self.url_)

    def connect(self, address, port):
        self.url_ = 'http://' + address + ':' + str(port) + '/'

    @staticmethod
    def find(key):
        if not key in commands:
            return False
        return True

    @staticmethod
    def activate(key):
        commands[key].activate()

    @staticmethod
    def helpMessage():
        print 'Usage:\n'
        for (_, value) in commands.items():
            print value.helpMsg(), '\n'


class CmdConsume(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values == '?':
            CmdManager.helpMessage()
            sys.exit(0)

        if not CmdManager.find(values):
            LOG.error('UNMANAGED command ' + values)
            sys.exit(False)

        CmdManager.activate(values)
        setattr(namespace, self.dest, values)


def main(argv=None):
    if not argv: argv = sys.argv

    try:
        bug_reporter_ = '<r.monno@nextworks.it>'
        parser_ = argparse.ArgumentParser(description='Media Manager',
                    epilog='Please, report bugs to ' + bug_reporter_,
                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        parser_.add_argument('-d', '--debug',
                             default=False,
                             action='store_true',
                             help='set logging level to DEBUG')

        parser_.add_argument('-a', '--address',
                             default='localhost',
                             help='set the server address')

        parser_.add_argument('-p', '--port',
                             default=9998,
                             help='set the server port')

        parser_.add_argument('command',
                             action=CmdConsume,
                             help='?=describe how to use every single command')

        args_ = parser_.parse_args()

    except Exception as ex:
        print 'Got an Exception parsing flags/options:', ex
        return False

    if args_.debug == True:
        LOG.set_debug()

    LOG.debug("%s" % (args_,))
    comMng = CmdManager()
    
    try:
        comMng.analyze(args_.command)

    except AttributeError as ex:
        LOG.error('MALFORMED command %s' % (args_.command,))
        LOG.error('what: ' + str(ex))
        return False

    comMng.connect(args_.address, args_.port)
    comMng.execute(args_.command)

    LOG.info("Bye Bye...")
    return True


if __name__ == '__main__':
    sys.exit(main())

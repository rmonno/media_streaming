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

class FileCommand(GenericCommand):
    def __init__(self):
        GenericCommand.__init__(self)
        self.fpath = None
        self.repo = os.path.dirname(os.path.abspath(sys.argv[0])) + '/media_repository'

    def addFile(self, fpath):
        self.fpath = fpath

    def isCompleted(self):
        GenericCommand.isCompleted(self)

        if self.fpath is None:
            raise AttributeError('missing file parameter!')

        if not os.path.isdir(self.repo):
            raise AttributeError('%s is not a directory!' % self.repo)

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
        return 'list' + '\n\tGet a list of all stored music files'

class Upload(FileCommand):
    def execute(self, url):
        if not os.path.isfile(self.fpath):
            raise AttributeError('The path does not exist or isn\'t a regular file!')

        cmd_ = "cp \"%s\" \"%s\"" % (self.fpath, self.repo)
        LOG.debug(cmd_)
        os.system(cmd_)

        LOG.info('successfully uploaded file!')

    def helpMsg(self):
        return 'upload -f <file>' + '\n\tUpload a file into the repository (absolute path)'

class Remove(FileCommand):
    def execute(self, url):
        file_ = self.repo + '/' + self.fpath
        if not os.path.isfile(file_):
            raise AttributeError('The %s path does not exist!' % file_)

        LOG.info('Remove a file from a repository')

        cmd_ = "rm \"%s\"" % (file_)
        LOG.debug(cmd_)
        os.system(cmd_)

        LOG.info('successfully removed file!')

    def helpMsg(self):
        return 'remove -f <file>' + '\n\tRemove a file from the repository (file name)'

class Append2Play(GenericCommand):
    def execute(self, url):
        LOG.critical('Not implemented, yet!')

    def helpMsg(self):
        return 'append2play -f <file>' + '\n\tSchedule a file to be played (file name)'


commands = {'list': List(),
            'upload': Upload(),
            'remove': Remove(),
            'append2play': Append2Play()}

class CmdManager:
    def __init__(self):
        self.url_ = None

    def analyze(self, key):
        commands[key].isCompleted()

    def execute(self, key):
        commands[key].execute(self.url_)

    def connect(self, address, port):
        self.url_ = 'http://' + address + ':' + str(port) + '/'

    def updateFile(self, key, fpath):
        commands[key].addFile(fpath)

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
            print value.helpMsg() + '\n'


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

        parser_.add_argument('-f', '--file',
                             help='absolute path to a MP3 file')

        args_ = parser_.parse_args()

    except Exception as ex:
        print 'Got an Exception parsing flags/options:', ex
        return False

    if args_.debug == True:
        LOG.set_debug()

    LOG.debug("%s" % (args_,))
    comMng = CmdManager()
    
    try:
        if args_.file is not None:
            comMng.updateFile(args_.command, args_.file)

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

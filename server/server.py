#!/usr/bin/env python

import sys
import os
import argparse
import bottle
import threading
import Queue
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import *
import json


if __name__ == '__main__':
    bp_ = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    if bp_ not in [os.path.abspath(x) for x in sys.path]:
        sys.path.insert(0, bp_)

import utilities as utils
LOG = utils.ColorLog(name='media_server', debug=False)

CATALOG_APPEND = None
CATALOG_REMOVE = None
CATALOG_GET = None

QUEUE = Queue.Queue(maxsize=5)


@bottle.get('/catalog')
def catalog():
    LOG.debug("Enter http get catalog")
    catalog_ = CATALOG_GET()

    if not len(catalog_):
        bottle.abort(500, "Empty Catalog!")

    info_ = {'catalog':[]}
    for c_ in catalog_:
        info_['catalog'].append({'title': c_,
                                 'index': catalog_.index(c_)})

    return json.dumps(info_, sort_keys=True, indent=4, separators=(',', ': '))


@bottle.get('/title')
def title():
    LOG.debug("Enter http get title")
    if bottle.request.headers['content-type'] != 'application/json':
        bottle.abort(500, 'Application Type must be json!')

    index_ = int(bottle.request.json['index'])
    LOG.info("Index=%d" % index_)

    catalog_ = CATALOG_GET()
    if index_ >= len(catalog_):
        bottle.abort(500, 'Index out of range!')

    info_ = {'title': catalog_[index_]}
    return json.dumps(info_, sort_keys=True, indent=4, separators=(',', ': '))


@bottle.get('/queue-size')
def queue_size():
    LOG.debug("Enter http get queue-size")
    info_ = {'queue-size': QUEUE.qsize()}
    return json.dumps(info_, sort_keys=True, indent=4, separators=(',', ': '))


@bottle.post('/append2play')
def append2play():
    LOG.debug("Enter http post append2play")
    if bottle.request.headers['content-type'] != 'application/json':
        bottle.abort(500, 'Application Type must be json!')

    index_ = int(bottle.request.json['index'])
    LOG.info("Index=%d" % index_)

    catalog_ = CATALOG_GET()
    if index_ >= len(catalog_):
        bottle.abort(500, 'Index out of range!')

    title_ = catalog_[index_]
    LOG.info("Title=%s" % title_)

    try:
        QUEUE.put(item=title_, timeout=1)

    except Queue.Full:
        bottle.abort(500, 'Sorry, the queue is full...')

    return bottle.HTTPResponse(body='success', status=201)


class QueueMediaPlayer(threading.Thread):
    def __init__(self, address, port, catalog_dir):
        threading.Thread.__init__(self)
        self.daemon = True

        self.__address = address
        self.__port = port
        self.__dir = catalog_dir

        self.__check_cmd_exists('cvlc')
        LOG.debug("Configured QueueMediaPlayer: addr=%s, port=%s, dir=%s",
                  address, port, catalog_dir)

    def __check_cmd_exists(self, cmd):
        subprocess.check_call([cmd, '--version'])

    def __play_mp3(self, fname):
        f_ = self.__dir + '/' + fname
        if not os.path.exists(f_):
            LOG.error("The path (%s) doesn't exist!" % f_)

        else:
            cmd_ = "cvlc -vvv --play-and-exit \"" + f_ + "\" " +\
                   "--sout '#standard{access=%s,mux=%s,dst=%s:%s}'" %\
                   ('http', 'ogg', self.__address, self.__port)
            LOG.debug(cmd_)
            os.system(cmd_)

    def __play_mp4(self, fname):
        f_ = self.__dir + '/' + fname
        if not os.path.exists(f_):
            LOG.error("The path (%s) doesn't exist!" % f_)

        else:
            cmd_ = "cvlc -vvv --play-and-exit \"" + f_ + "\" " +\
                   "--sout '#transcode{vcodec=%s,acodec=%s,vb=%s,ab=%s}:standard{access=%s,mux=%s,dst=%s:%s}'" %\
                   ('mp4v', 'mpga', '800', '128', 'http', 'ogg', self.__address, self.__port)
            LOG.debug(cmd_)
            os.system(cmd_)

    def run(self):
        LOG.debug("QueueMediaPlayer started...")
        while True:
            if not QUEUE.empty():
                item_ = QUEUE.get(timeout=1)
                if item_.endswith('.mp3'):
                    self.__play_mp3(item_)

                elif item_.endswith('.mp4'):
                    self.__play_mp4(item_)

                else:
                    LOG.error("Un-managed file type (%s)" % item_)

            else:
                time.sleep(1)

        LOG.error("QueueMediaPlayer ended (?)...")


class ChangeHandler(PatternMatchingEventHandler):
    def __init__(self):
        PatternMatchingEventHandler.__init__(self, patterns=['*.mp3', '*.mp4'])

    def on_any_event(self, event):
        pass

    def on_created(self, event):
        LOG.debug("on_created event: %s", str(event))
        (dir_, file_) = os.path.split(event.src_path)
        CATALOG_APPEND(file_)

    def on_deleted(self, event):
        LOG.debug("on_deleted event: %s", str(event))
        (dir_, file_) = os.path.split(event.src_path)
        CATALOG_REMOVE(file_)

    def on_modified(self, event):
        pass

    def on_moved(self, event):
        pass


class MediaObserver:
    def __init__(self, directory):
        global CATALOG_APPEND
        global CATALOG_REMOVE
        global CATALOG_GET

        self.__mutex = threading.Lock()
        self.__obs = Observer(timeout=10)
        self.__obs.schedule(ChangeHandler(), path=directory, recursive=False)
        self.__dir = directory
        self.__catalog = [f for f in os.listdir(directory) if f.endswith(('.mp3', '.mp4'))]

        CATALOG_APPEND = self.append
        CATALOG_REMOVE = self.remove
        CATALOG_GET = self.get

        self.__obs.start()
        LOG.debug("Started MediaObserver: dir=%s, catalog=%s", directory, self.__catalog)

    def append(self, fname):
        try:
            self.__mutex.acquire()
            self.__catalog.append(fname)
            LOG.debug("Catalog=%s", self.__catalog)

        finally:
            self.__mutex.release()

    def remove(self, fname):
        try:
            self.__mutex.acquire()
            self.__catalog.remove(fname)
            LOG.debug("Catalog=%s", self.__catalog)

        finally:
            self.__mutex.release()

    def get(self):
        try:
            self.__mutex.acquire()
            return self.__catalog

        finally:
            self.__mutex.release()

    def stop(self):
        LOG.info("Stopping MediaObserver...")
        self.__obs.stop()

    def join(self):
        LOG.info("Joining MediaObserver...")
        self.__obs.join()


def main(argv=None):
    if not argv: argv = sys.argv

    try:
        bug_reporter_ = '<r.monno@nextworks.it>'
        parser_ = argparse.ArgumentParser(description='Media Server',
                    epilog='Please, report bugs to ' + bug_reporter_,
                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        parser_.add_argument('-d', '--debug',
                             default=False,
                             action='store_true',
                             help='set logging level to DEBUG')

        parser_.add_argument('-a', '--address',
                             default='localhost',
                             help='set the streaming server address')

        parser_.add_argument('-p', '--port',
                             default=9999,
                             help='set the streaming server port')

        parser_.add_argument('-l', '--listen_port',
                             default=9998,
                             help='set the server listen port')

        args_ = parser_.parse_args()

    except Exception as ex:
        print 'Got an Exception parsing flags/options:', ex
        return False

    if args_.debug == True:
        LOG.set_debug()

    LOG.debug("%s" % (args_,))
    
    repository_ = os.path.dirname(os.path.abspath(sys.argv[0])) + '/media_repository'
    observer_ = MediaObserver(repository_)

    qplay_ = QueueMediaPlayer(args_.address, args_.port, repository_)
    qplay_.start()

    try:
        LOG.info("Starting media server main cycle")
        bottle.run(host=args_.address, port=args_.listen_port, debug=args_.debug)

    except KeyboardInterrupt:
        LOG.warning("User interruption!")

    except Exception as ex:
        LOG.error("Exception: %s" % (ex,))
        return False

    observer_.stop()
    observer_.join()

    LOG.warning("Bye Bye...")
    return True


if __name__ == '__main__':
    sys.exit(main())

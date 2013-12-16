#!/usr/bin/env python

import sys
import os
import argparse
import time

if __name__ == '__main__':
    bp_ = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    if bp_ not in [os.path.abspath(x) for x in sys.path]:
        sys.path.insert(0, bp_)

import utilities as utils
LOG = None

def main(argv=None):
    if not argv: argv = sys.argv

    try:
        bug_reporter_ = '<r.monno@nextworks.it>'
        parser_ = argparse.ArgumentParser(description='Media Client',
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

        args_ = parser_.parse_args()

    except Exception as ex:
        print 'Got an Exception parsing flags/options:', ex
        return False

    LOG = utils.ColorLog(name='media_client', debug=args_.debug)
    LOG.debug("%s" % (args_,))

    try:
        cmd_ = "vlc http://%s:%s" % (args_.address, args_.port)
        LOG.info(cmd_)
        os.system(cmd_)

    except KeyboardInterrupt:
        LOG.warning("User interruption!")

    except Exception as ex:
        LOG.error("Exception: %s" % (ex,))
        return False

    return True


if __name__ == '__main__':
    sys.exit(main())

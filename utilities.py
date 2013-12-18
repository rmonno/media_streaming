from termcolor import colored
import logging


class ColorLog(object):
    colormap = dict(
        debug=dict(color='grey', attrs=['bold']),
        info=dict(color='green', attrs=['bold']),
        warning=dict(color='yellow', attrs=['bold']),
        error=dict(color='red', attrs=['bold']),
        critical=dict(color='magenta', attrs=['bold']),)

    def __init__(self, name, debug):
        self._logger = logging.getLogger(name)
        if debug:
            self._logger.setLevel(logging.DEBUG)
        else:
            self._logger.setLevel(logging.INFO)

        form = logging.Formatter('[%(asctime)-15s] [%(levelname)s] %(message)s')
        screen_hdlr = logging.StreamHandler()
        screen_hdlr.setFormatter(form)
        self._logger.addHandler(screen_hdlr)

    def __getattr__(self, name):
        if name in ['debug', 'info', 'warning', 'error', 'critical']:
            return lambda s, * args: getattr(self._logger, name)(
                colored(str(s), **self.colormap[name]), *args)

        return getattr(self._logger, name)

    def set_debug(self):
        self._logger.setLevel(logging.DEBUG)

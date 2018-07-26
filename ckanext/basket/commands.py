import logging
import json

import rdflib
import skos

import ckan.lib.cli as cli

log = logging.getLogger(__name__)


class BasketCommand(cli.CkanCommand):
    '''  A command for working with baskets

    Usage::

     # Initialising the database
     paster basket init

     # Remove the database tables
     paster basket cleanup
    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__

    def command(self):
        '''
        Parse command line arguments and call appropriate method.
        '''
        cmd = self.args[0]
        self._load_config()

        if cmd == 'init':
            self.init()
        elif cmd == 'cleanup':
            self.cleanup()
        else:
            print self.usage
            log.error('Command "%s" not recognized' % (cmd,))
            return

    def init(self):
        from ckanext.basket.models import init_tables
        init_tables()

    def cleanup(self):
        from ckanext.basket.models import remove_tables
        remove_tables()

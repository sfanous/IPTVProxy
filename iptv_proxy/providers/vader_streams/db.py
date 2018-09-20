import logging

from BTrees.IOBTree import IOBTree
from persistent.mapping import PersistentMapping

from ...db import IPTVProxyDB

logger = logging.getLogger(__name__)


class VaderStreamsDB(IPTVProxyDB):

    def __init__(self):
        IPTVProxyDB.__init__(self)

        if 'VaderStreams' not in self._root['IPTVProxy']:
            self._root['IPTVProxy']['VaderStreams'] = PersistentMapping()
        if 'epg' not in self._root['IPTVProxy']['VaderStreams']:
            self._root['IPTVProxy']['VaderStreams']['epg'] = IOBTree()

            self.commit()

    def has_keys(self, keys):
        if not keys:
            raise ValueError

        return IPTVProxyDB.has_keys(self, ['VaderStreams'] + keys)

    def persist(self, keys, value):
        if not keys:
            raise ValueError

        IPTVProxyDB.persist(self, ['VaderStreams'] + keys, value)

    def retrieve(self, keys):
        if not keys:
            raise ValueError

        return IPTVProxyDB.retrieve(self, ['VaderStreams'] + keys)

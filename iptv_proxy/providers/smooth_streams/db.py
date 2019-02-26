import logging

from BTrees.IOBTree import IOBTree
from persistent.mapping import PersistentMapping

from ...db import IPTVProxyDB

logger = logging.getLogger(__name__)


class SmoothStreamsDB(IPTVProxyDB):

    def __init__(self):
        IPTVProxyDB.__init__(self)

        if 'SmoothStreams' not in self._root['IPTVProxy']:
            self._root['IPTVProxy']['SmoothStreams'] = PersistentMapping()
        if 'epg' not in self._root['IPTVProxy']['SmoothStreams']:
            self._root['IPTVProxy']['SmoothStreams']['epg'] = IOBTree()

            self.commit()

    def has_keys(self, keys):
        if not keys:
            raise ValueError

        return IPTVProxyDB.has_keys(self, ['SmoothStreams'] + keys)

    def delete(self, keys):
        if not keys:
            raise ValueError

        IPTVProxyDB.delete(self, ['SmoothStreams'] + keys)

    def persist(self, keys, value):
        if not keys:
            raise ValueError

        IPTVProxyDB.persist(self, ['SmoothStreams'] + keys, value)

    def retrieve(self, keys):
        if not keys:
            raise ValueError

        return IPTVProxyDB.retrieve(self, ['SmoothStreams'] + keys)

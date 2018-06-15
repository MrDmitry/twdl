# Copyright (c) 2018 by Dmitry Odintsov
# This code is licensed under the MIT license (MIT)
# (http://opensource.org/licenses/MIT)

# Stream class module

from . import Utils

class Stream():
    """ Object containing information about active stream """

    def __init__(self, root, channel, meta):
        self.root = root
        self.channel = channel
        self.meta = meta

    def name(self):
        return ''.join(c if c in Utils.valid_chars else '_' for c in self.meta['title'])

    def __lt__(self, rhs):
        return self.meta['id'] < rhs.meta['id']

    def __eq__(self, rhs):
        return False if rhs is None else self.meta['id'] == rhs.meta['id']

    def __str__(self):
        return 'Stream {{ {channel}, {root} }}'.format(channel = self.channel, root = self.root)

# Copyright (c) 2018 by Dmitry Odintsov
# This code is licensed under the MIT license (MIT)
# (http://opensource.org/licenses/MIT)

# Stream class module

import os

from datetime import datetime

from . import Utils

class Stream():
    """ Object containing information about active stream """

    def __init__(self, root_dir, channel, meta, started_at):
        self.alive = True
        self.channel = channel
        self.meta = meta
        self.started_at = started_at if started_at is not None else datetime.strptime(meta['started_at'], '%Y-%m-%dT%H:%M:%SZ')
        self.root = os.path.join(root_dir, self.channel, '{started_at}'.format(started_at = self.started_at)) if root_dir is not None else None

        if self.root is not None:
            ts_path = os.path.join(self.root, Utils.TS_DIR)
            tc_path = os.path.join(self.root, Utils.TC_DIR)
            log_path = os.path.join(self.root, Utils.LOG_DIR)

            Utils.create_dir_if_needed(ts_path)
            Utils.create_dir_if_needed(tc_path)
            Utils.create_dir_if_needed(log_path)

    def name(self):
        return ''.join(c if c in Utils.valid_chars else '_' for c in self.meta['title']) if self.meta is not None else 'unknown'

    def __lt__(self, rhs):
        return rhs.started_at.timestamp() - self.started_at.timestamp() > 2

    def __eq__(self, rhs):
        return False if rhs is None else abs(self.started_at.timestamp() - rhs.started_at.timestamp()) < 2

    def __str__(self):
        return 'Stream {{ {channel}, {root}, {started_at} }}'.format(channel = self.channel, root = self.root, started_at = self.started_at)

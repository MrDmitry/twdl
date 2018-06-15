# Copyright (c) 2018 by Dmitry Odintsov
# This code is licensed under the MIT license (MIT)
# (http://opensource.org/licenses/MIT)

# Stream monitoring routine module

import json
import os
import random
import requests
import sys

from datetime import datetime

from . import Stream
from . import Utils

def WorkerStream(stopSignal, headers, root_dir, channel_name, stream_queue):
    """ Worker class for detecting active Streams
        If there is a live stream going, checks status every 7 seconds,
        otherwise checks every 2 seconds
    """
    STREAM_API = 'https://api.twitch.tv/helix/streams/?user_login={channel}&p={random}'

    def __log(*argv):
        print('[worker]', '[stream]', datetime.now(), *argv)

    __log('starting')

    timeout = 2

    streamLive = None
    meta_raw = None
    meta = None

    while not stopSignal.isSet():
        url = STREAM_API.format(channel = channel_name, random = random.randint(0,1E7))

        try:
            meta_raw = requests.get(url, headers = headers)
            meta = json.loads(meta_raw.text)
        except:
            e = sys.exc_info()[0]
            __log('exception caught:', e)
            continue

        if 'data' not in meta:
            __log(json.dumps(meta, indent = 4))
            continue

        if len(meta['data']) > 0:
            root = os.path.join(root_dir, channel_name, '{id}'.format(id = meta['data'][0]['id']))

            ts_path = os.path.join(root, Utils.TS_DIR)
            tc_path = os.path.join(root, Utils.TC_DIR)
            log_path = os.path.join(root, Utils.LOG_DIR)

            Utils.create_dir_if_needed(ts_path)
            Utils.create_dir_if_needed(tc_path)
            Utils.create_dir_if_needed(log_path)

            streamInfo = Stream(root, channel_name, meta['data'][0])

            stream_queue.put(streamInfo)

            if streamLive is not True:
                streamLive = True
                timeout = 7
                __log('stream is live:', streamInfo)
        else:
            if streamLive is not False:
                streamLive = False
                timeout = 2
                __log('stream is offline')

        stopSignal.wait(timeout)

    __log('exiting')

# Copyright (c) 2018 by Dmitry Odintsov
# This code is licensed under the MIT license (MIT)
# (http://opensource.org/licenses/MIT)

# Stream monitoring routine module

import json
import random
import requests
import sys

from datetime import datetime

from . import Stream
from . import Utils

def WorkerStream(stopSignal, headers, root_dir, online_tick, offline_tick, channel_name, stream_queue):
    """ Worker class for detecting active Streams """
    STREAM_API = 'https://api.twitch.tv/helix/streams/?user_login={channel}&p={random}'

    def __log(*argv):
        print('[worker]', '[stream]', datetime.now(), *argv)

    __log('starting')

    timeout = offline_tick

    streamLive = None
    meta_raw = None
    meta = None

    lastStream = None

    while not stopSignal.isSet():
        url = STREAM_API.format(channel = channel_name, random = random.randint(0,1E7))

        try:
            meta_raw = requests.get(url, headers = headers)
            meta = json.loads(meta_raw.text)
        except:
            e = sys.exc_info()[1]
            __log('exception caught:', repr(e))
            continue

        if 'data' not in meta:
            __log(json.dumps(meta, indent = 4))
            continue

        if len(meta['data']) > 0:
            streamInfo = Stream(root_dir, channel_name, meta['data'][0], None)

            if lastStream is not None:
                if streamInfo != lastStream:
                    lastStream.alive = False
                    stream_queue.put((lastStream, lastStream))

            lastStream = streamInfo
            stream_queue.put((streamInfo, streamInfo))

            if streamLive is not True:
                streamLive = True
                timeout = online_tick
                __log('stream is live:', streamInfo)
        else:
            if lastStream is not None:
                lastStream.alive = False
                stream_queue.put((lastStream, lastStream))
                lastStream = None

            if streamLive is not False:
                streamLive = False
                timeout = offline_tick
                __log('stream is offline')

        stopSignal.wait(timeout)

    __log('exiting')

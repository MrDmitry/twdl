# Copyright (c) 2018 by Dmitry Odintsov
# This code is licensed under the MIT license (MIT)
# (http://opensource.org/licenses/MIT)

# M3U8 processing routine module

import json
import m3u8
import random
import requests
import time
import sys

from datetime import datetime

from . import Segment
from . import Utils

def WorkerM3U8(headers, stream_queue, dl_queue):
    """ Worker class for processing m3u8 playlist for active stream
        Looks for m3u8 playlist of Source quality and reads TS segments from it
    """

    USHER_API = 'https://usher.ttvnw.net/api/channel/hls/{channel}.m3u8?player=twitchweb' + \
        '&token={token}&sig={sig}&$allow_audio_only=true&allow_source=true' + \
        '&type=any&p={random}'

    TOKEN_API = 'https://api.twitch.tv/api/channels/{channel}/access_token'

    def __log(*argv):
        print('[worker]', '[m3u8]', datetime.now(), *argv)

    def get_token_and_signature(channel):
        token = None
        sig = None
        retryCount = 10

        while retryCount != 0:
            try:
                url = TOKEN_API.format(channel = channel)
                r = requests.get(url, headers = headers)
                txt = r.text
                data = json.loads(txt)
                sig = data['sig']
                token = data['token']
                break
            except:
                e = sys.exc_info()[0]
                __log('[token-sig]', 'exception caught:', e)
                retryCount -= 1
                time.sleep(0.2)
                continue

        if retryCount == 0:
            __log('[token-sig]', 'retry count reached')

        return token, sig

    def get_playlists(channel):
        token, sig = get_token_and_signature(channel)
        m3u8_obj = None
        retryCount = 10

        while retryCount != 0:
            try:
                r = random.randint(0,1E7)
                url = USHER_API.format(channel = channel, sig = sig, token = token, random = r)
                r = requests.get(url, headers = headers)
                m3u8_obj = m3u8.loads(r.text)
                break
            except:
                e = sys.exc_info()[0]
                __log('[playlists]', 'exception caught:', e)
                retryCount -= 1
                time.sleep(0.2)
                continue

        if retryCount == 0:
            __log('[playlists]', 'retry count reached')

        return m3u8_obj

    __log('starting')

    segments = {}

    while True:
        stream = stream_queue.get()

        if stream is None:
            stream_queue.task_done()
            break

        if stream.root not in segments:
            segments = {}
            segments[stream.root] = -1

        m3u8_obj = get_playlists(stream.channel)
        if m3u8_obj:
            for p in m3u8_obj.playlists:
                if 'source' in p.media[0].name:
                    url = p.uri
                    r = requests.get(url, headers = headers)
                    m3u8_data = m3u8.loads(r.text)

                    i = m3u8_data.media_sequence
                    for s in m3u8_data.segments:
                        if i > segments[stream.root]:
                            ts = Segment(i, s.uri, stream)
                            dl_queue.put((ts, ts))
                            segments[stream.root] = i
                        i += 1
        else:
            __log('failed to get playlists')

        stream_queue.task_done()

    __log('exiting')

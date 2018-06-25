# Copyright (c) 2018 by Dmitry Odintsov
# This code is licensed under the MIT license (MIT)
# (http://opensource.org/licenses/MIT)

# M3U8 processing routine module

import json
import m3u8
import random
import re
import requests
import sys
import time

from datetime import datetime

from . import Segment
from . import Stream
from . import Utils

def WorkerM3U8(stopSignal, headers, root_dir, m3u8_tick, channel_name, dl_queue):
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
                e = sys.exc_info()[1]
                __log('[token-sig]', 'exception caught:', repr(e))
                retryCount -= 1
                time.sleep(0.2)
                continue

        if retryCount == 0:
            __log('[token-sig]', 'retry count reached')

        return token, sig

    def get_playlists(channel):
        token, sig = get_token_and_signature(channel)
        m3u8_obj = None
        twitch_info = None
        retryCount = 10

        while retryCount != 0:
            try:
                r = random.randint(0,1E7)
                url = USHER_API.format(channel = channel, sig = sig, token = token, random = r)
                r = requests.get(url, headers = headers)
                m3u8_obj = m3u8.loads(r.text)
                m3u8_twitch_info = re.search('#EXT-X-TWITCH-INFO:(.*)', r.text)
                if m3u8_twitch_info:
                    twitch_info = dict(re.findall(r'([^=]+)="([^"]+)",?', m3u8_twitch_info.group(1)))
                break
            except:
                e = sys.exc_info()[1]
                __log('[playlists]', 'exception caught:', repr(e))
                retryCount -= 1
                time.sleep(0.2)
                continue

        if retryCount == 0:
            __log('[playlists]', 'retry count reached')

        return m3u8_obj, twitch_info

    __log('starting')

    last_segment = 0
    last_started_at = None

    while not stopSignal.isSet():
        m3u8_obj, twitch_info = get_playlists(channel_name)
        r = None
        if m3u8_obj:
            for p in m3u8_obj.playlists:
                if 'source' in p.media[0].name:
                    server_time = float(twitch_info['SERVER-TIME'])
                    stream_time = float(twitch_info['STREAM-TIME'])
                    started_at = datetime.utcfromtimestamp(round(server_time - stream_time))
                    url = p.uri
                    try:
                        r = requests.get(url, headers = headers)
                    except:
                        e = sys.exc_info()[1]
                        __log('exception caught:', repr(e))
                        time.sleep(0.2)
                        break

                    if last_started_at is not None:
                        if (started_at - last_started_at).seconds > 2:
                            __log('stream changed from', last_started_at, 'to', started_at)
                            last_segment = 0
                            last_started_at = None
                    else:
                        last_started_at = started_at
                        __log('current stream', last_started_at)

                    m3u8_data = m3u8.loads(r.text)
                    i = m3u8_data.media_sequence
                    for s in m3u8_data.segments:
                        if i > last_segment:
                            last_segment = i
                            ts = Segment(i, s.uri, Stream(root_dir, channel_name, None, started_at))
                            dl_queue.put((ts, ts))
                        i += 1
        else:
            last_segment = 0

        stopSignal.wait(m3u8_tick)

    __log('exiting')

# Copyright (c) 2018 by Dmitry Odintsov
# This code is licensed under the MIT license (MIT)
# (http://opensource.org/licenses/MIT)

# Vod processing routine

import json
import m3u8
import os
import random
import requests
import subprocess
import time
import sys

from datetime import datetime

from . import Utils

def VodFfmpeg(root, headers, vodId, start, end, duration):
    """ Downloads a portion of vod identified by vodId """

    USHER_API = 'https://usher.ttvnw.net/vod/{vodId}.m3u8?player=twitchweb' + \
        '&nauthsig={sig}&nauth={token}&allow_audio_only=true&allow_source=true' + \
        '&type=any&p={random}'

    TOKEN_API = 'https://api.twitch.tv/api/vods/{vodId}/access_token'

    def __log(*argv):
        print('[vod]', '[ffmpeg]', datetime.now(), *argv)

    def get_token_and_signature(vodId):
        token = None
        sig = None
        retryCount = 10

        while retryCount != 0:
            try:
                url = TOKEN_API.format(vodId = vodId)
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

    def get_vod_stream(vodId):
        token, sig = get_token_and_signature(vodId)
        m3u8_obj = None
        retryCount = 10

        while retryCount != 0:
            try:
                r = random.randint(0,1E7)
                url = USHER_API.format(vodId = vodId, sig = sig, token = token, random = r)
                r = requests.get(url, headers = headers)
                m3u8_obj = m3u8.loads(r.text)
                break
            except:
                e = sys.exc_info()[1]
                __log('[stream]', 'exception caught:', repr(e))
                retryCount -= 1
                time.sleep(0.2)
                continue

        if retryCount == 0:
            __log('[stream]', 'retry count reached')

        return m3u8_obj

    __log('starting')

    m3u8_obj = get_vod_stream(vodId)

    if m3u8_obj:
        for p in m3u8_obj.playlists:
            if any(x in p.media[0].name for x in ['900p60', '1080p60']):
                elapsed = start

                if elapsed is None:
                    elapsed = '00:00:00'

                output_filename = Utils.vod_name.format(elapsed = elapsed.replace(':', '-'), vodId = vodId)
                output_path = os.path.join(root, output_filename)
                tw_path = os.path.join(root, 'vod_{}'.format(output_filename))

                dl_opts = ('ffmpeg', '-y')
                dl_opts += ('-i', p.uri,)

                if start is not None:
                    dl_opts += ('-ss', start,)

                if end is not None:
                    dl_opts += ('-to', end,)

                if duration is not None:
                    dl_opts += ('-t', duration,)

                dl_opts += Utils.copy_options
                dl_opts += (tw_path,)

                __log('download started:', dl_opts)

                with subprocess.Popen(dl_opts) as ffmpeg_dl:
                    ffmpeg_dl.wait()

                __log('download complete, transcoding')

                with subprocess.Popen(('ffmpeg', '-y', '-i', tw_path,) + (Utils.transcode_options if p.media[0].name is not '1080p60' else Utils.copy_options) + (output_path,)) as ffmpeg_transcode:
                    ffmpeg_transcode.wait()

                __log('transcode complete')

                Utils.remove_file(tw_path)
    else:
        __log('failed to get stream')

    __log('exiting')

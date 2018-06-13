# Copyright (c) 2018 by Dmitry Odintsov
# This code is licensed under the MIT license (MIT)
# (http://opensource.org/licenses/MIT)

# Vod processing routine

import os
import subprocess

from datetime import datetime

from . import Utils

def VodStreamlink(root, vodId, start, duration):
    """ Downloads a portion of vod identified by vodId """

    def __log(*argv):
        print('[vod]', '[ffmpeg]', datetime.now(), *argv)

    __log('starting')

    url = 'https://www.twitch.tv/videos/{}'.format(vodId)

    elapsed = start

    if elapsed is None:
        elapsed = '00:00:00'

    output_path = os.path.join(root, Utils.vod_name.format(elapsed = elapsed.replace(':', '-'), vodId = vodId))

    with subprocess.Popen(('streamlink', '--stdout', '--hls-start-offset', elapsed, '--hls-segment-threads=4', url, 'source,1080p60,1080p50,900p60,900p50,720p60,720p50,1080,900,720,best'), stdout=subprocess.PIPE, preexec_fn = Utils.ignore_sigint) as twitch_stream:
        input_opts = ('ffmpeg', '-i', '-',)

        if duration is not None:
            input_opts += ('-t', duration,)

        __log('downloading and transcoding')
        res = subprocess.check_output(input_opts + Utils.transcode_options + (output_path,), stdin = twitch_stream.stdout, preexec_fn = Utils.ignore_sigint)

        __log('transcode complete')

        twitch_stream.terminate()
        twitch_stream.wait()
        __log('download complete')

    __log('exiting')

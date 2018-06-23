# Copyright (c) 2018 by Dmitry Odintsov
# This code is licensed under the MIT license (MIT)
# (http://opensource.org/licenses/MIT)

# Segment transcoding routine module

import subprocess

from datetime import datetime

from . import Utils

def WorkerTranscode(tc_queue, concat_queue):
    """ Worker class for transcoding TS segments """

    def __log(*argv):
        print('[worker]', '[tc]', datetime.now(), *argv)

    __log('starting')

    shouldTranscode = None

    while True:
        ts = tc_queue.get()[1]

        if ts is None:
            tc_queue.task_done()
            break

        shouldTranscode = True

        with subprocess.Popen(('ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'program_stream=width,height', '-of', 'csv=s=x:p=0', ts.tsFilepath(),), stdout = subprocess.PIPE, stderr = subprocess.PIPE) as ffprobe:
            exit_code = ffprobe.wait()
            out, err = ffprobe.communicate()

            if exit_code is not 0:
                __log(ts.id, 'failed to detect resolution', err)
            else:
                resolution = str(out, 'utf-8').splitlines()[0]
                shouldTranscode = resolution != '1920x1080'
                __log(ts.id, 'resolution', resolution)

        __log(ts.id, 'transcode' if shouldTranscode else 'copy', 'started')

        ffmpeg_opts = ('ffmpeg', '-y', '-i', ts.tsFilepath(),) + (Utils.transcode_options if shouldTranscode else Utils.copy_options) + (ts.tcFilepath(),)
        with subprocess.Popen(ffmpeg_opts, stdout = subprocess.PIPE, stderr = subprocess.PIPE) as ffmpeg:
            ffmpeg.wait()
            ts.checkSubprocess(ffmpeg)

        Utils.remove_file(ts.tsFilepath())

        __log(ts.id, 'completed')

        concat_queue.put((ts, ts))
        tc_queue.task_done()

    __log('exiting')

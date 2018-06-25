# Copyright (c) 2018 by Dmitry Odintsov
# This code is licensed under the MIT license (MIT)
# (http://opensource.org/licenses/MIT)

# Stream segment transcode and concat routine module

import os
import subprocess
import time
import queue

from datetime import datetime

from . import Utils

def WorkerConcat(processing_queue, concat_queue, stream_queue):
    """ Worker class for concatenating downloaded TS segments """

    def __log(*argv):
        print('[worker]', '[cc]', datetime.now(), *argv)

    tmp0Name = 'tmp0.mp4'
    tmp1Name = 'tmp1.mp4'

    def finalize_stream(stream, last_tmp, start, end):
        if stream is not None and last_tmp is not None:
            __log('finalizing', stream)

            output_file = os.path.join(stream.root, Utils.stream_name.format(start = start, end = end, name = stream.name()))

            with subprocess.Popen(('ffmpeg', '-y', '-i', last_tmp,) + Utils.copy_options + (output_file,), stdout = subprocess.PIPE, stderr = subprocess.PIPE) as ffmpeg:
                exit_code = ffmpeg.wait()
                __log('finalization complete:', exit_code, stream)

                if exit_code is not 0:
                    out, err = ffmpeg.communicate()
                    with open(os.path.join(stream.root, stream.name()) + '_out.txt', 'a') as f:
                        f.write('========\n')
                        f.write(str(out, 'utf-8'))
                        f.write('========\n')

                    with open(os.path.join(stream.root, stream.name()) + '_err.txt', 'a') as f:
                        f.write('========\n')
                        f.write(str(err, 'utf-8'))
                        f.write('========\n')

            os.remove(last_tmp)

    def should_wait_for_more(queue, wait_start):
        """ Indicate if algorithm should wait for more segments
            Expected cutoff point is either 30 items in queue or
            non-empty queue waiting for at least 30 seconds since wait_start
        """
        return len(queue) < 100 and \
            (len(queue) < 1 or (datetime.now() - wait_start).seconds < 30)

    __log('starting')

    stream = None
    start = 0
    end = 0
    tmp_flag = False
    last_tmp = None
    last_item = None

    while True:
        ts_queue = []

        __log('concat loop')

        tmp_stream = stream_queue.get()[1]
        stream_queue.task_done()

        if tmp_stream is not None:
            stream = tmp_stream
        else:
            break

        wait_start = datetime.now()

        __log('concat routine for', stream)

        # check processing_queue
        while should_wait_for_more(ts_queue, wait_start):
            __log('waiting for next item to process')

            next_item = None

            # get next awaited item
            try:
                next_item = processing_queue.get(True, 30)[1]
                processing_queue.task_done()
            except queue.Empty:
                __log('failed to get anything from processing queue')

            # if it's None, exit
            if next_item is None:
                if len(ts_queue) == 0:
                    last_item = None
                    break
                else:
                    processing_queue.put((next_item, next_item))
                    break

            if stream != next_item.stream:
                __log('stream appears to have changed, putting segment back', stream, next_item.stream)
                processing_queue.put((next_item, next_item))
                last_item = None
                break

            # check if we had some progress so far
            if last_item is not None:
                # check if we jumped some segments
                if next_item.id - last_item.id > 1:
                    # if we did, put the item back, reset last_item and stop waiting for more segments
                    processing_queue.put((next_item, next_item))
                    last_item = None
                    break
            # if we had none, start a new 'session'
            else:
                start = next_item.id
                end = 0
                tmp_flag = False

            last_item = next_item

            __log('waiting for', next_item, 'to be processed')

            # check concat_queue
            while should_wait_for_more(ts_queue, wait_start):
                # get next processed item
                ts = concat_queue.get()[1]

                # if it's the awaited one
                if ts == next_item:
                    # append and loop back
                    ts_queue.append(ts)
                    break
                else:
                    if ts is None:
                        concat_queue.task_done()
                        concat_queue.put((ts, ts))
                        break
                    else:
                        # put it back to the concat_queue and wait a bit
                        __log('got', ts, 'instead')
                        concat_queue.task_done()
                        concat_queue.put((ts, ts))
                        time.sleep(0.5)

            if ts_queue[-1] != next_item:
                processing_queue.put((next_item, next_item))

            __log(next_item, 'is ready for concat')

        # if there is nothing in the queue
        if len(ts_queue) == 0:
            # if last_item was reset, finalize current stream
            if stream.alive is False or last_item is None:
                finalize_stream(stream, last_tmp, start, end)
                start = 0
                end = 0
                last_tmp = None
                continue

        shouldTranscode = True

        # resolution detection
        with subprocess.Popen(('ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'program_stream=width,height', '-of', 'csv=s=x:p=0', ts_queue[0].tsFilepath(),), stdout = subprocess.PIPE, stderr = subprocess.PIPE) as ffprobe:
            exit_code = ffprobe.wait()
            out, err = ffprobe.communicate()

            if exit_code is not 0:
                __log(ts_queue[0].id, 'failed to detect resolution', err)
            else:
                resolution = str(out, 'utf-8').splitlines()[0]
                shouldTranscode = resolution not in ['1920x1080', '1280x720', '854x480', '640x360', '426x240']
                __log(ts_queue[0].id, 'resolution', resolution)

        __log(stream, 'transcode' if shouldTranscode else 'copy', len(ts_queue), 'segments:', ', '.join(str(ts.id) for ts in ts_queue))

        end = ts_queue[-1].id
        ffmpeg_opts = ('ffmpeg', '-y', '-i', 'concat:{}'.format('|'.join(ts.tsFilepath() for ts in ts_queue)),) + (Utils.transcode_options if shouldTranscode else Utils.copy_options) + (ts_queue[0].tcFilepath(),)
        with subprocess.Popen(ffmpeg_opts, stdout = subprocess.PIPE, stderr = subprocess.PIPE) as ffmpeg:
            exit_code = ffmpeg.wait()

            if exit_code is not 0:
                out, err = ffmpeg.communicate()
                with open(ts_queue[0].stdoutFilepath(), 'a') as f:
                    f.write('========\n')
                    f.write(str(ffmpeg.args))
                    f.write('\n========\n')
                    f.write(str(out, 'utf-8'))
                    f.write('========\n')

                with open(ts_queue[0].stderrFilepath(), 'a') as f:
                    f.write('========\n')
                    f.write(str(ffmpeg.args))
                    f.write('\n========\n')
                    f.write(str(err, 'utf-8'))
                    f.write('========\n')

                sys.exit(-1)

        for ts in ts_queue:
            Utils.remove_file(ts.tsFilepath())

        __log(stream, 'concat', len(ts_queue), 'segments:', ', '.join(str(ts.id) for ts in ts_queue))

        list_path = os.path.join(stream.root, 'list.txt')

        with open(list_path, 'w') as f:
            if last_tmp is not None:
                f.write("file '{}'\n".format(last_tmp))

            f.write("file '{}'\n".format(ts_queue[0].tcFilepath()))

        output_tmp = os.path.join(stream.root, tmp0Name if tmp_flag else tmp1Name)

        with subprocess.Popen(('ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', list_path,) + Utils.copy_options + (output_tmp,), stdout = subprocess.PIPE, stderr = subprocess.PIPE) as ffmpeg:
            exit_code = ffmpeg.wait()

            if exit_code is not 0:
                out, err = ffmpeg.communicate()
                with open(output_tmp + '_out.txt', 'a') as f:
                    f.write('========\n')
                    f.write(str(ffmpeg.args))
                    f.write('\n========\n')
                    f.write(str(out, 'utf-8'))
                    f.write('========\n')

                with open(output_tmp + '_err.txt', 'a') as f:
                    f.write('========\n')
                    f.write(str(ffmpeg.args))
                    f.write('\n========\n')
                    f.write(str(err, 'utf-8'))
                    f.write('========\n')

        if not os.path.exists(output_tmp):
            __log('failed to concat, abort', stream)
            stream = None
            break

        Utils.remove_file(ts_queue[0].tcFilepath())

        for ts in ts_queue:
            concat_queue.task_done()

        if last_tmp is not None:
            Utils.remove_file(last_tmp)

        Utils.remove_file(list_path)

        tmp_flag = not tmp_flag
        last_tmp = output_tmp

        __log(stream, 'concat completed')

        if last_item is None:
            finalize_stream(stream, last_tmp, start, end)
            start = 0
            end = 0
            last_tmp = None

    finalize_stream(stream, last_tmp, start, end)

    __log('exiting')

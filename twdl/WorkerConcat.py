# Copyright (c) 2018 by Dmitry Odintsov
# This code is licensed under the MIT license (MIT)
# (http://opensource.org/licenses/MIT)

# Stream segment concat routine module

import os
import subprocess
import time

from datetime import datetime

from . import Utils

def WorkerConcat(processing_queue, concat_queue):
    """ Worker class for concatenating processed TS segments """

    def __log(*argv):
        print('[worker]', '[cc]', datetime.now(), *argv)

    tmp0Name = 'tmp0.mp4'
    tmp1Name = 'tmp1.mp4'

    def finalize_stream(stream, last_tmp):
        if stream is not None and last_tmp is not None:
            __log('finalizing', stream)

            output_file = os.path.join(stream.root, Utils.stream_name.format(name = stream.name()))

            with subprocess.Popen(('ffmpeg', '-i', last_tmp,) + Utils.copy_options + (output_file,), stdout = subprocess.PIPE, stderr = subprocess.PIPE) as ffmpeg:
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
            Expected cutoff point is either 10 items in queue or
            non-empty queue waiting for at least 20 seconds since wait_start
        """
        return len(queue) < 10 and \
            (len(queue) < 1 or (datetime.now() - wait_start).seconds < 20)

    __log('starting')

    stream = None
    tmp_flag = False
    last_tmp = None
    last_item = None

    while True:
        ts_queue = []

        wait_start = datetime.now()

        __log('concat loop')

        # check processing_queue
        while should_wait_for_more(ts_queue, wait_start):
            __log('waiting for next item to process')

            # get next awaited item
            next_item = processing_queue.get()[1]
            processing_queue.task_done()

            # if it's None, exit
            if next_item is None:
                if len(ts_queue) == 0:
                    wait_start = None
                    break
                else:
                    processing_queue.put((next_item, next_item))
                    break

            # check if stream changed from the last segment
            if last_item is not None and \
                last_item.stream != next_item.stream:
                # if it did, put the item back, reset last_item and stop waiting for more segments
                processing_queue.put((next_item, next_item))
                last_item = None
                break

            last_item = next_item

            # if current stream is different, remember it
            if stream != last_item.stream:
                stream = last_item.stream
                tmp_flag = False

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
            # if wait_start was reset, exit
            if wait_start is None:
                break
            # or if last_item was reset, finalize current stream
            elif last_item is None:
                finalize_stream(stream, last_tmp)
                last_tmp = None
                continue

        __log(stream, 'concat', len(ts_queue), 'segments:', ', '.join(str(ts.id) for ts in ts_queue))

        list_path = os.path.join(stream.root, 'list.txt')

        with open(list_path, 'w') as f:
            if last_tmp is not None:
                f.write("file '{}'\n".format(last_tmp))

            for ts in ts_queue:
                f.write("file '{}'\n".format(ts.tcFilepath()))

        output_tmp = os.path.join(stream.root, tmp0Name if tmp_flag else tmp1Name)

        with subprocess.Popen(('ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_path,) + Utils.copy_options + (output_tmp,), stdout = subprocess.PIPE, stderr = subprocess.PIPE) as ffmpeg:
            exit_code = ffmpeg.wait()

            if exit_code is not 0:
                out, err = ffmpeg.communicate()
                with open(output_tmp + '_out.txt', 'a') as f:
                    f.write('========\n')
                    f.write(str(out, 'utf-8'))
                    f.write('========\n')

                with open(output_tmp + '_err.txt', 'a') as f:
                    f.write('========\n')
                    f.write(str(err, 'utf-8'))
                    f.write('========\n')

        if not os.path.exists(output_tmp):
            __log('failed to concat, abort', stream)
            stream = None
            break

        for ts in ts_queue:
            Utils.remove_file(ts.tcFilepath())
            concat_queue.task_done()

        if last_tmp is not None:
            Utils.remove_file(last_tmp)

        Utils.remove_file(list_path)

        tmp_flag = not tmp_flag
        last_tmp = output_tmp

        __log(stream, 'concat completed')

        if last_item is None:
            finalize_stream(stream, last_tmp)
            last_tmp = None

    finalize_stream(stream, last_tmp)

    __log('exiting')

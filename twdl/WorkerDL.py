# Copyright (c) 2018 by Dmitry Odintsov
# This code is licensed under the MIT license (MIT)
# (http://opensource.org/licenses/MIT)

# Segment download routine module

import requests

from datetime import datetime

def WorkerDL(dl_queue, processing_queue, concat_queue):
    """ Worker class for downloading TS segments """

    def __log(*argv):
        print('[worker]', '[dl]', datetime.now(), *argv)

    __log('starting')

    while True:
        ts = dl_queue.get()[1]

        if ts is None:
            dl_queue.task_done()
            break

        __log(ts, 'started')

        processing_queue.put((ts, ts))

        filepath = ts.tsFilepath()

        try:
            r = requests.get(ts.url, stream = True)
        except:
            e = sys.exc_info()[1]
            __log('exception caught:', repr(e))
            dl_queue.task_done()
            dl_queue.put((ts, ts))
            continue

        try:
            with open(filepath, 'wb') as f:
                for chunk in r:
                    f.write(chunk)

            __log(ts.id, 'completed')

            concat_queue.put((ts, ts))
        except OSError as e:
            __log(ts.id, 'exception caught:', repr(e))
            dl_queue.put((ts, ts))

        dl_queue.task_done()

    __log('exiting')

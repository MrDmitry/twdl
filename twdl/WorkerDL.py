# Copyright (c) 2018 by Dmitry Odintsov
# This code is licensed under the MIT license (MIT)
# (http://opensource.org/licenses/MIT)

# Segment download routine module

import requests

from datetime import datetime

def WorkerDL(dl_queue, processing_queue, tc_queue):
    """ Worker class for downloading TS segments """

    def __log(*argv):
        print('[worker]', '[dl]', datetime.now(), *argv)

    __log('starting')

    while True:
        ts = dl_queue.get()[1]

        if ts is None:
            dl_queue.task_done()
            break

        __log(ts.id, 'started')

        processing_queue.put((ts, ts))

        filepath = ts.tsFilepath()

        try:
            r = requests.get(ts.url, stream = True)
        except:
            e = sys.exc_info()[0]
            __log('exception caught:', e)
            dl_queue.task_done()
            dl_queue.put((ts, ts))
            continue

        try:
            with open(filepath, 'wb') as f:
                for chunk in r:
                    f.write(chunk)

            __log(ts.id, 'completed')

            tc_queue.put((ts, ts))
        except OSError as e:
            __log(ts.id, 'exception caught:', e)
            dl_queue.put((ts, ts))

        dl_queue.task_done()

    __log('exiting')

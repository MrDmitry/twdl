#!/usr/bin/env python

# Copyright (c) 2018 by Dmitry Odintsov
# This code is licensed under the MIT license (MIT)
# (http://opensource.org/licenses/MIT)

import argparse
import json
import os
import queue
import signal
import sys
import threading

from datetime import datetime

import twdl

headers = None

stopSignal = threading.Event()

def __log(*argv):
    print('[main]', datetime.now(), *argv)

def signal_handler(s, frame):
    if s == signal.SIGINT:
        __log('[system]', 'SIGINT detected; shutting down')
        stopSignal.set()

def main(args, config):
    """ Main entry point for the program """
    signal.signal(signal.SIGINT, signal_handler)

    __log('root directory:', config['root'])
    __log('starting listening for', args.channel_name)

    stream_queue = queue.Queue()

    dl_queue = queue.PriorityQueue()
    processing_queue = queue.PriorityQueue()
    tc_queue = queue.PriorityQueue()
    concat_queue = queue.PriorityQueue()

    w_stream = threading.Thread(target = twdl.WorkerStream, args = (stopSignal, headers, config['root'], args.channel_name, stream_queue,))
    w_stream.start()

    w_m3u8 = threading.Thread(target = twdl.WorkerM3U8, args = (headers, stream_queue, dl_queue,))
    w_m3u8.start()

    w_dl = []

    for i in range(4):
        w = threading.Thread(target = twdl.WorkerDL, args = (dl_queue, processing_queue, tc_queue,))
        w_dl.append(w)
        w.start()

    w_transcode = threading.Thread(target = twdl.WorkerTranscode, args = (tc_queue, concat_queue,))
    w_transcode.start()

    w_concat = threading.Thread(target = twdl.WorkerConcat, args = (processing_queue, concat_queue,))
    w_concat.start()

    stopSignal.wait()

    __log('waiting for stream worker')

    w_stream.join()

    stream_queue.put(None)

    __log('waiting for M3U8 worker')

    w_m3u8.join()

    for i in range(len(w_dl)):
        dl_queue.put((twdl.Segment(0, '', None), None))

    __log('waiting for DL workers')

    for t in w_dl:
        t.join()

    __log('waiting for transcode worker')

    tc_queue.put((twdl.Segment(sys.maxsize, '', None), None))
    w_transcode.join()

    __log('waiting for concat worker')

    processing_queue.put((twdl.Segment(sys.maxsize, '', None), None))
    concat_queue.put((twdl.Segment(sys.maxsize, '', None), None))
    w_concat.join()

    __log('exiting')

    sys.exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'twitch channel live recorder')

    parser.add_argument('-c', '--config', type = str, default = None, help = 'configuration file')
    parser.add_argument('channel_name')
    args = parser.parse_args()

    config = twdl.Utils.process_config(__file__, args.config)

    headers = config['twitch_headers']

    main(args, config)


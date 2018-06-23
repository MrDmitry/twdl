# Copyright (c) 2018 by Dmitry Odintsov
# This code is licensed under the MIT license (MIT)
# (http://opensource.org/licenses/MIT)

# Utilities module

import json
import os
import string
import sys

from datetime import datetime

TS_DIR = 'ts'
TC_DIR = 'ffmpeg'
LOG_DIR = 'logs'

transcode_options = ('-acodec', 'copy', '-bsf:a', 'aac_adtstoasc', '-c:v', 'libx264', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-crf', '1', '-b:v', '20M', '-bufsize', '10M', '-maxrate', '30M', '-vf', 'scale=1920:1080',)
copy_options = ('-c', 'copy', '-bsf:a', 'aac_adtstoasc',)

valid_chars = '-_.() %s%s' % (string.ascii_letters, string.digits)

stream_name = '{name}.mp4'
vod_name = '{vodId} - {elapsed}.mp4'

def __log(*argv):
    print('[util]', datetime.now(), *argv)

def create_dir_if_needed(path):
    if not os.path.exists(path):
        __log('[dir]', 'create', path)
        try:
            os.makedirs(path)
            __log('[dir]', 'success', path)
        except OSError as e:
            __log('[dir]', 'exception caught:', e)
            pass

def remove_file(path):
    __log('[remove]', path)
    try:
        os.remove(path)
        __log('[remove]', 'success')
    except OSError as e:
        __log('[remove]', 'exception caught:', e)
        pass

def process_config(current_file, config):
    default_config = {
        'root': os.path.realpath(current_file),
        'twitch_headers': {
            'Client-ID': ''
        }
    }

    result = default_config

    if config is not None:
        try:
            with open(config, 'r') as f:
                cfg = json.loads(f.read())
                for k, v in cfg.items():
                    result[k] = v
        except:
            e = sys.exc_info()[0]
            __log('exception caught:', e)
            result = default_config

    result['root'] = os.path.realpath(result['root'])
    create_dir_if_needed(result['root'])

    if not os.path.isdir(result['root']):
        result['root'] = os.path.dirname(result['root'])

    return result

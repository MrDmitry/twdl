#!/usr/bin/env python

# Copyright (c) 2018 by Dmitry Odintsov
# This code is licensed under the MIT license (MIT)
# (http://opensource.org/licenses/MIT)

import argparse

import twdl

if __name__=="__main__":
    parser = argparse.ArgumentParser(description = 'twitch vod downloader')

    typeGroup = parser.add_mutually_exclusive_group(required=True)
    ffmpegGroup = parser.add_argument_group('ffmpeg', 'uses ffmpeg to download the vod portion using vod -id')

    typeGroup.add_argument('-ffmpeg', action='store_true', help='use ffmpeg to download')
    typeGroup.add_argument('-streamlink', action='store_true', help='use streamlink to download')

    ffmpegGroup.add_argument('-end', type=str, help='end time')

    parser.add_argument('-c', '--config', type = str, default = None, help = 'configuration file')
    parser.add_argument('-start', type=str, help='start time')
    parser.add_argument('-dur', type=str, help='duration')
    parser.add_argument('vod_id', type=int, help='vod id')

    args = parser.parse_args()

    config = twdl.Utils.process_config(__file__, args.config)

    if args.ffmpeg:
        headers = config['twitch_headers']

        twdl.VodFfmpeg(config['root'], headers, args.vod_id, args.start, args.end, args.dur)
    elif args.streamlink:
        twdl.VodStreamlink(config['root'], args.vod_id, args.start, args.dur)
    else:
        parser.print_help()

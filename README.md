# twdl - Twitch livestream/vod downloader

## Dependencies

Depends on [ffmpeg](https://github.com/FFmpeg/FFmpeg) for downloading livestreams and transcoding video files

Depends on [streamlink](https://github.com/streamlink/streamlink) for downloading VODs

Python dependencies: requests, m3u8, json

## live.py

- Listens for live twitch streams identified by channel name
- While stream is live, downloads chunks of stream and transcodes them
- If chunks are not 1080p, they are upscaled to 1080p (`ffmpeg` options are located in `twdl/Utils.py`)
- After processing chunks are placed on a queue and stitched back together

Example config file:
```json
{
    "root": "/home/user/twdl",
    "twitch_headers": {
        "Client-ID": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
}
```

Usage:
```
usage: live.py [-h] [-c CONFIG] channel_name

twitch channel live recorder

positional arguments:
  channel_name

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        configuration file
```

## vod.py

Downloads a portion (or complete) vod identified by vod id

Example config file:
```json
{
    "root": "/home/user/twdl",
    "twitch_headers": {
        "Client-ID": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
}
```

Note: `twitch_headers` section in configuration file is only required with `-ffmpeg` option

Usage:
```
usage: vod.py [-h] (-ffmpeg | -streamlink) [-end END] [-c CONFIG]
              [-start START] [-dur DUR]
              vod_id

twitch vod downloader

positional arguments:
  vod_id                vod id

optional arguments:
  -h, --help            show this help message and exit
  -ffmpeg               use ffmpeg to download
  -streamlink           use streamlink to download
  -c CONFIG, --config CONFIG
                        configuration file
  -start START          start time
  -dur DUR              duration

ffmpeg:
  uses ffmpeg to download the vod portion using vod -id

  -end END              end time
```

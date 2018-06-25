# twdl - Twitch livestream/vod downloader

## Dependencies

Depends on [ffmpeg](https://github.com/FFmpeg/FFmpeg) for downloading livestreams and transcoding video files

Depends on [streamlink](https://github.com/streamlink/streamlink) for downloading VODs

Python dependencies: requests, m3u8, json

## live.py

- Listens for live twitch streams identified by channel name
- While stream is live, downloads chunks of stream
- Periodically concatenate segments to form a chunk (frequency is configured via `online_tick` and `offline_tick` config parameters)
- If chunk is not of expected resolution (`1920x1080`, `1280x720`, `854x480`, `640x360`, `426x240`), it is upscaled to `1920x1080` (`ffmpeg` options are located in `twdl/Utils.py`), otherwise it's copied as-is
- Add processed chunk to the current stream recording

Example config file:
```json
{
    "root": "/home/user/twdl",
    "online_tick": 60,
    "offline_tick": 180,
    "m3u8_tick": 5,
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

Note: `twitch_headers` section in configuration file is required when started with `-ffmpeg` option

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

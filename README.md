# FAU-TV Video Downloader

Downloads all videos of a given course (even if the download has been restricted) to a local folder.
This software is provided without warranty. Usage is discouraged! Usage of this software is at your own risk!

## Usage

```bash
usage: dl [-h] [--outDir OUTDIR] [--starterUrl STARTERURL]
          [--startAt STARTAT]
          courseId

Download clips from a course

positional arguments:
  courseId                  Course ID

options:
  -h, --help                show this help message and exit
  --outDir OUTDIR           Output directory
  --starterUrl STARTERURL   Starter URL
  --startAt STARTAT         Skip all previous indizes (starts at 1)
```

## Procedure

Upon starting, a firefox instance is opened, prompting you to log in using IDM SSO. As soon as the url changes to something starting with `https://www.fau.tv`, download will be starting. If you do not want to provide your credentials, you can provide `https://www.fau.tv` as a starter url.

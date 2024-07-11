# FAU-TV Video Downloader

Downloads all videos of a given course (even if the download has been restricted) to a local folder.
This software is provided without warranty. Usage is discouraged! Usage of this software is at your own risk!

## Usage

```bash
./dl '<fau course id>' '[output directory]' '[starter url]'
```

# Procedure

Upon starting, a firefox instance is opened, prompting you to log in using IDM SSO. As soon as the url changes to something starting with `https://www.fau.tv`, download will be starting. If you do not want to provide your credentials, you can provide `https://www.fau.tv` as a starter url.

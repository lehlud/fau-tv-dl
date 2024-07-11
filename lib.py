from selenium import webdriver
import time
from dataclasses import dataclass
import requests
import re
import subprocess
import shutil


_token: "Token" = None


@dataclass
class Token():
    auth_token: str
    session_id: str
    session_ci: str

    def cookies(self):
        cookies = {}

        if self.auth_token is not None:
            cookies["SimpleSAMLAuthToken"] = self.auth_token

        if self.session_id is not None:
            cookies["SimpleSAMLSessionID"] = self.session_id

        if self.session_ci is not None:
            cookies["session_ci"] = self.session_ci

        return cookies


@dataclass
class ClipDetails():
    clip_id: str

    combined_media_id: str = None
    combined_playlist_url: str = None
    camera_media_id: str = None
    camera_playlist_url: str = None
    slides_media_id: str = None
    slides_playlist_url: str = None

    def media_ids(self):
        return [id for id in [
            self.combined_media_id,
            self.camera_media_id,
            self.slides_media_id,
        ] if id is not None]

    def playlist_urls(self):
        return [url for url in [
            self.combined_playlist_url,
            self.camera_playlist_url,
            self.slides_playlist_url,
        ] if url is not None]


def load_token(auth_url: str):
    global _token

    driver = webdriver.Firefox()

    driver.get(auth_url)

    while not driver.current_url.startswith('https://www.fau.tv/'):
        time.sleep(0.5)

    def get_value(cookie):
        if cookie is None:
            return None
        return cookie.get("value")

    _token = Token(
        auth_token=get_value(driver.get_cookie("SimpleSAMLAuthToken")),
        session_id=get_value(driver.get_cookie("SimpleSAMLSessionID")),
        session_ci=get_value(driver.get_cookie("session_ci")),
    )

    driver.close()


def get_course_clip_ids(course_id: str) -> list[str]:
    global _token

    regex = re.compile(r'(/clip/id/)([0-9]+)(\"\s*class=\"preview\")')

    urls = []

    url = f'https://www.fau.tv/course/id/{course_id}'
    with requests.get(url, cookies=_token.cookies()) as r:
        clip_matches = regex.findall(r.text)
        for match in clip_matches:
            urls.append(match[1])

    return urls


def get_clip_details(clip_id: str) -> ClipDetails:
    global _token

    url = f'https://www.fau.tv/clip/id/{clip_id}'
    details = ClipDetails(clip_id=clip_id)

    with requests.get(url, cookies=_token.cookies()) as r:
        def get_details(keyword: str):
            mediaid_re = re.compile(
                r'(' + keyword + r'Sources[^,]*,\s+mediaid\:\s+\")([0-9]+)'
            )

            playlist_url_re = re.compile(
                r'(file\:\s+\")([^\"]*' + keyword + r'\.smil[^\"]*)(\")'
            )

            mediaid_matches = mediaid_re.findall(r.text)
            if len(mediaid_matches) > 0:
                setattr(details, keyword + "_media_id", mediaid_matches[0][1])

            playlist_url_matches = playlist_url_re.findall(r.text)
            if len(playlist_url_matches) > 0:
                setattr(details, keyword + "_playlist_url",
                        playlist_url_matches[0][1])

        get_details("combined")
        get_details("camera")
        get_details("slides")

    return details


def download_media(media_id: str, outfile_path: str):
    global _token

    url = f'https://itunes.video.uni-erlangen.de/get/file/' + \
        str(media_id) + '?download=1'

    with requests.get(url, stream=True, cookies=_token.cookies()) as r:
        if (r.status_code != 200):
            return False

        with open(outfile_path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    return True


def download_playlist(playlist_url: str, outfile_path: str):
    subprocess.run([
        'ffmpeg',
        '-i', playlist_url,
        '-c', 'copy',
        outfile_path,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


def download_clip(clip_id: str, outfile_path: str):
    details = get_clip_details(clip_id)

    if len(details.media_ids()) > 0:
        media_id = details.media_ids()[0]
        print(f"Trying to download clip {clip_id} using media id {media_id}")
        if download_media(media_id, outfile_path):
            return

    if len(details.playlist_urls()) > 0:
        playlist_url = details.playlist_urls()[0]
        print(f"Trying to download clip {clip_id} using playlist url {playlist_url}")
        download_playlist(playlist_url, outfile_path)

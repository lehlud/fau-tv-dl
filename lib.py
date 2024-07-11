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
        return {
            "SimpleSAMLAuthToken": self.auth_token,
            "SimpleSAMLSessionID": self.session_id,
            "session_ci": self.session_ci,
        }


@dataclass
class ClipDetails():
    combined_media_id: str = None
    combined_playlist_url: str = None
    camera_media_id: str = None
    camera_playlist_url: str = None
    slides_media_id: str = None
    slides_playlist_url: str = None


def load_token(auth_url: str = "https://www.fau.tv/auth/sso"):
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

    print(_token)

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
    details = ClipDetails()

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
    ])


def download_clip(clip_id: str, outfile_path: str):
    details = get_clip_details(clip_id)

    media_id = next(id for id in [
        details.combined_media_id,
        details.camera_media_id,
        details.slides_media_id,
    ] if id is not None)

    if download_media(media_id, outfile_path):
        return

    url = next(url for url in [
        details.combined_playlist_url,
        details.camera_playlist_url,
        details.slides_playlist_url,
    ] if url is not None)

    download_playlist(url, outfile_path)

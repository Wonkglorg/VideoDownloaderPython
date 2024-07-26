import os
import re
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import yt_dlp
from urllib3.connection import HTTPSConnection
from urllib3.exceptions import ReadTimeoutError


# todo:jmd file_name_template is not working atm and just uses default values.

class YTVideoDownloader:

    def __init__(self):
        video_formats = [
            'mp4', 'webm', 'avi', 'mkv', 'mov', 'flv', 'wmv', 'mpeg', 'mpg', '3gp', 'm4v',
            'ogv', 'rm', 'rmvb', 'vob', 'mts', 'ts', 'm2ts', 'divx', 'f4v'
        ]

        audio_formats = [
            'wav', 'mp3', 'aac', 'flac', 'ogg', 'm4a', 'wma', 'alac', 'opus', 'ac3', 'eac3',
            'aiff', 'amr', 'au', 'caf', 'dts', 'mp2', 'mka'
        ]
        self.video_formats = video_formats
        self.audio_formats = audio_formats

    def download_single_frame_video(self, url: str, output_dir: str, album_image: str, low_hardware_mode=False,
                                    with_metadata: bool = True,
                                    subfolder_playlists: bool = True,
                                    retries: int = 5,
                                    backoff_factor: float = 1,
                                    file_name_template: str = "{title}") -> None:
        """

        :param the url of the video / playlist to download
        :param output_dir the path of the output directory
        :param album_image the path of the album image
        :param low_hardware_mode if set to true downbloads the mp4 and converts it using a still frame(Takes less CPU but more time to donwload) else downloads the mp3 and converts it to a video (takes more cpu for the encoder but less time to download)
        :param subfolder_playlists if playlists should be sub foldered based on their playlist name
        :param threads number of download threads
        :param retries number of download retries before quitting
        :param backoff_factor the exponential time offset in seconds to wait before retrying
        :param file_name_template the name format of the video file to be downloaded
        """

        filet_type = "mp3"
        if low_hardware_mode:
            filet_type = "mp4"

        results = self.download(url, output_dir, filet_type, with_metadata, file_name_template=file_name_template,
                                subfolder_playlists=subfolder_playlists, retries=retries, backoff_factor=backoff_factor)

        if subfolder_playlists:
            if len(results) > 1:
                playlist_name = results.get(list(results)[0]).get('playlist', '')
                if playlist_name is not '':
                    sanitized_playlist_name = self._sanitize_for_windows(playlist_name)
                    playlist_dir = os.path.join(output_dir, sanitized_playlist_name)
                    os.makedirs(playlist_dir, exist_ok=True)
                    output_dir = playlist_dir

        for entry in results:
            file_name = os.path.basename(entry)
            if low_hardware_mode:
                self._replace_video_with_static_image(entry, os.path.join(output_dir, file_name), album_image)
                continue
            self._create_video_from_audio_with_static_image(entry, os.path.join(output_dir, file_name), album_image)

    def download(self, url: str, output_dir: str, file_format: str = "mp4", with_meta: bool = True, retries: int = 5,
                 backoff_factor: float = 1, show_album_cover_on_mp3: bool = True, subfolder_playlists: bool = True,
                 album_cover_image: str = None,
                 threads: int = 4,
                 file_name_template: str = "{title}") -> dict:
        """

        :param url the url of the video / playlist to download \n
        :param output_dir the path of the output directory \n
        :param file_format the file format of the video \n
        :param with_meta if the meta should be injected into the output \n
        :param retries number of retries to download the video before quitting \n
        :param backoff_factor the factor to increase the download delay \n
        :param show_album_cover_on_mp3 if the album cover should be shown on mp3 file formats (if no cover is selected tries to download the first frame from the video as the cover) \n
        :param album_cover_image the album cover image to use  \n
        :param subfolder_playlists if playlists should be sub foldered based on their playlist name \n
        :param threads number of download threads \n
        :param file_name_template the file name template to use for the file output \n
        :returns a dict key = file name, value = dict of video data
        """
        os.makedirs(output_dir, exist_ok=True)
        file_format = file_format.lower()
        for attempt in range(retries):
            if url is None or output_dir is None:
                print("URL or Output directory cannot be None")
                return {}

            try:
                with yt_dlp.YoutubeDL() as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                    is_playlist = info_dict.get('_type') == 'playlist'

                    if is_playlist:
                        return self._download_playlist(output_dir, info_dict, file_format, threads, subfolder_playlists,
                                                       with_meta,
                                                       show_album_cover_on_mp3, album_cover_image,
                                                       retries, backoff_factor, file_name_template)
                    else:
                        if file_format in self.audio_formats:
                            return self._download_audio(url, output_dir, info_dict, file_format, with_meta,
                                                        show_album_cover_on_mp3, album_cover_image,
                                                        file_name_template)
                        else:
                            return self._download_video(url, output_dir, info_dict, file_format, with_meta,
                                                        album_cover_image, file_name_template)

            except (yt_dlp.utils.DownloadError, HTTPSConnection, ReadTimeoutError) as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    sleep_time = backoff_factor * (2 ** attempt)
                    print(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    print("All retries failed.")
                    raise

    def _download_playlist(self, output_dir: str, info_dict: dict, file_format: str, threads, subfolder_playlists,
                           with_meta: bool = True,
                           show_album_cover: bool = True,
                           album_cover_image: str = None, retries: int = 5,
                           backoff_factor: float = 1,
                           file_name_template: str = "{title}") -> dict:
        playlist_name = info_dict.get('title', 'playlist')
        if subfolder_playlists:
            sanitized_playlist_name = self._sanitize_for_windows(playlist_name)
            playlist_dir = os.path.join(output_dir, sanitized_playlist_name)
            os.makedirs(playlist_dir, exist_ok=True)
            output_dir = playlist_dir
        print(f"Downloading playlist: {playlist_name}")

        results = {}
        with ThreadPoolExecutor(max_workers=threads) as executor:
            future_to_entry = {
                executor.submit(self._download_entry, entry, output_dir, file_format, with_meta, show_album_cover,
                                album_cover_image, file_name_template, retries, backoff_factor): entry
                for entry in info_dict.get('entries', [])
            }

            for future in as_completed(future_to_entry):
                entry = future_to_entry[future]
                try:
                    results.update(future.result())
                except Exception as e:
                    print(f"Download failed for entry {entry['title']}: {e}")
        return results

    def _download_entry(self, entry, output_dir, file_format, with_meta, show_album_cover, album_cover_image,
                        file_name_template, retries, backoff_factor) -> dict:
        for attempt in range(retries):
            try:
                if file_format in self.audio_formats:
                    return self._download_audio(entry.get("webpage_url"), output_dir, entry,
                                                file_format, with_meta, show_album_cover,
                                                album_cover_image, file_name_template)
                else:
                    return self._download_video(entry.get("webpage_url"), output_dir, entry,
                                                file_format, with_meta, album_cover_image,
                                                file_name_template)
            except (yt_dlp.utils.DownloadError, HTTPSConnection, ReadTimeoutError) as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    sleep_time = backoff_factor * (2 ** attempt)
                    print(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    print("All retries failed.")
                    raise

    def _download_audio(self, url: str, output_dir: str, info_dict: dict, file_format: str, with_meta: bool = True,
                        show_album_cover: bool = True,
                        album_cover_image: str = None,
                        file_name_template: str = "{title}") -> dict:
        meta_data = self._extract_meta_from_info_dict(info_dict)
        file_name = self._resolve_file_name_template(file_name_template, meta_data)
        output_file_path = os.path.join(output_dir, file_name + "." + file_format)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': file_format,
                'preferredquality': '192',
            }],
            'postprocessor_args': ['-ar', '44100'],
            'noplaylist': True,
            'no_warnings': True,
            'extract_flat': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if with_meta:
            temp_output_file = tempfile.mktemp(suffix=f".{file_format}")
            self._add_metadata_to_file(output_file_path, temp_output_file, meta_data)
            shutil.copy(temp_output_file, output_file_path)
            os.remove(temp_output_file)

        if album_cover_image:
            temp_output_file = tempfile.mktemp(suffix=f".{file_format}")
            self._add_cover_image_to_audio(output_file_path, temp_output_file, album_cover_image)
            shutil.copy(temp_output_file, output_file_path)
            os.remove(temp_output_file)
        return {output_file_path: info_dict}

    def _download_video(self, url: str, output_dir: str, info_dict: dict, file_format: str, with_meta: bool = True,
                        album_cover_image: str = None,
                        file_name_template: str = "{title}") -> dict:
        meta_data = self._extract_meta_from_info_dict(info_dict)
        file_name = self._resolve_file_name_template(file_name_template, meta_data)
        output_file_path = os.path.join(output_dir, file_name + "." + file_format)

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'no_warnings': True,
            'extract_flat': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if with_meta:
            temp_output_file = tempfile.mktemp(suffix=f".{file_format}")
            self._add_metadata_to_file(output_file_path, temp_output_file, meta_data)
            shutil.copy(temp_output_file, output_file_path)
            os.remove(temp_output_file)

        if album_cover_image:
            temp_output_file = tempfile.mktemp(suffix=f".{file_format}")
            self._add_cover_image_to_video(output_file_path, temp_output_file, album_cover_image)
            shutil.copy(temp_output_file, output_file_path)
            os.remove(temp_output_file)
        return {output_file_path: info_dict}

    def _resolve_file_name_template(self, file_name_template, meta_data):
        resolved_file_name = file_name_template
        for key, value in meta_data.items():
            resolved_file_name = resolved_file_name.replace(f"{{{key}}}", value)
        return self._sanitize_for_windows(resolved_file_name)

    @staticmethod
    def _extract_meta_from_info_dict(info_dict):
        title = info_dict.get('title')
        artist = info_dict.get('artist') or info_dict.get('uploader')
        album = info_dict.get('album') or ""
        thumbnail_url = info_dict.get('thumbnail')
        genre = info_dict.get('genre') or ""
        release_date = info_dict.get('release_date') or ""
        track_number = info_dict.get('track') or ""
        meta_data = {
            "title": title,
            "artist": artist,
            "album": album,
            "thumbnail_url": thumbnail_url,
            "genre": genre,
            "release_date": release_date,
            "track_number": track_number
        }
        return meta_data

    @staticmethod
    def _sanitize_for_windows(s):
        return re.sub(r'[<>:"/\\|?*]', '_', s)

    @staticmethod
    def _download_image_to_temp(url):
        response = requests.get(url, stream=True)
        response.raise_for_status()
        temp_file = tempfile.mktemp(suffix='.jpg')
        with open(temp_file, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        return temp_file

    @staticmethod
    def _add_metadata_to_file(input_file, output_file, meta_data):
        cmd = [
            'ffmpeg', '-i', input_file,
            '-metadata', f'title={meta_data["title"]}',
            '-metadata', f'artist={meta_data["artist"]}',
            '-metadata', f'album={meta_data["album"]}',
            '-metadata', f'genre={meta_data["genre"]}',
            '-metadata', f'date={meta_data["release_date"]}',
            '-metadata', f'track={meta_data["track_number"]}',
            '-c', 'copy', output_file
        ]
        subprocess.run(cmd, check=True)

    @staticmethod
    def _add_cover_image_to_audio(input_file, output_file, cover_image_file):
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-i', cover_image_file,
            '-map', '0',
            '-map', '1',
            '-c', 'copy',
            '-id3v2_version', '3',
            '-metadata:s:v', 'title="Album cover"',
            '-metadata:s:v', 'comment="Cover (front)"',
            output_file
        ]
        subprocess.run(cmd, check=True)

    @staticmethod
    def _add_cover_image_to_video(input_file, output_file, cover_image_file):
        cmd = [
            'ffmpeg', '-i', input_file, '-i', cover_image_file, '-map', '0', '-map', '1', '-c', 'copy', '-metadata:s:v',
            'title="Album cover"', '-metadata:s:v', 'comment="Cover (front)"', output_file
        ]
        subprocess.run(cmd, check=True)

    @staticmethod
    def _create_video_from_audio_with_static_image(input_file: str, output_file: str, image_file: str) -> None:
        """
        Creates a video format out of audio and a static image, mimicking mp3's with album covers
        :param input_file: the audio file to convert
        :param output_file: the final output
        :param image_file: the static image file
        """
        video_codec = "libx264"
        audio_codec = "copy"
        image_format = "yuv420p"
        frame_rate = "1"

        output_file_mp4 = os.path.splitext(output_file)[0] + '.mp4'

        cmd = [
            'ffmpeg',
            '-i', input_file,  # Input audio
            '-i', image_file,  # Input image
            '-c:v', video_codec,  # Video codec to use
            '-r', frame_rate,  # Frame rate
            '-pix_fmt', image_format,  # Pixel format
            '-loop', '1',  # Loop the image
            '-c:a', audio_codec,  # Audio codec
            '-strict', 'experimental',
            '-b:a', '192k',  # Audio bitrate
            '-shortest',  # Stop when the shortest input ends
            '-y',  # Overwrite output files without asking
            output_file_mp4
        ]

        subprocess.run(cmd, check=True)

        if os.path.exists(input_file):
            os.remove(input_file)

    @staticmethod
    def _replace_video_with_static_image(input_file, output_file, image_file):
        """
        Replaces a video with a static image mimicking an mp3 with an album cover
        :param input_file: the video file to convert
        :param output_file: the final output
        :param image_file: the static image file
        """
        video_codec = "libx264"
        audio_codec = "copy"
        image_format = "yuv420p"
        frame_rate = "1"

        temp_output_file = os.path.splitext(output_file)[0] + '_temp.mp4'

        cmd = [
            'ffmpeg',
            '-i', input_file,  # Input video
            '-i', image_file,  # Input image
            '-c:v', video_codec,  # Video codec to use
            '-r', frame_rate,  # Frame rate
            '-pix_fmt', image_format,  # Pixel format
            '-map', '0:a?',  # Map audio if it exists
            '-map', '1:0',  # Map image from the second file
            '-c:a', audio_codec,  # Copy audio without re-encoding
            '-y',  # Overwrite output files without asking
            temp_output_file
        ]

        subprocess.run(cmd, check=True)

        # If the input file and output file are the same, replace the input file with the temporary output file
        if os.path.abspath(input_file) == os.path.abspath(output_file):
            os.replace(temp_output_file, output_file)
        else:
            # Otherwise, move the temporary output file to the desired output file
            os.rename(temp_output_file, output_file)

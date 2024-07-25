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

#todo:jmd figure out what metadata is actually important and mostly valid? Create own mp3 plugin for eagle which takes in the mp3 files meta data and gets its thumbnail if one exists
# Once this is completed continue with eagle plugins.

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

        """
        Custom Downloader Option mimics the behaviour of mp3's with a thumbnail but as a 1 fps size optimized mp4 format
        :param video_url: 
        :return: 
        """

    def download(self, url: str, output_dir: str, file_format: str = "mp4", with_meta: bool = True, retries: int = 5,
                 backoff_factor: float = 1, show_album_cover_on_mp3: bool = True,
                 album_cover_image: str = None,
                 threads: int = 4,
                 custom_ffmpeg_command: array = None,
                 file_name_template: str = "{title}") -> None:
        # todo:jmd add custom ffmpeg command resolver, provide placholders like, "file path" "output file path" etc, then let it modify the file, for example making it 1 frame or similar, could be quite handy. otherwise id have to make so many different methods for stuff.
        """
        @:parameter url the url of the video / playlist to download \n
        @:parameter output_dir the path of the output directory \n
        @:parameter file_format the file format of the video \n
        @:parameter with_meta if the meta should be injected into the output \n
        @:parameter retries number of retries to download the video before quitting \n
        @:parameter create_single_frame_video if the video should be created in a single frame (also requires album_cover_image to be set \n
        @:parameter backoff_factor the factor to increase the download delay \n
        @:parameter show_album_cover_on_mp3 if the album cover should be shown on mp3 file formats (if no cover is selected tries to download the first frame from the video as the cover) \n
        @:parameter album_cover_image the album cover image to use  \n
        @:parameter threads number of download threads \n
        @:parameter file_name_template the file name template to use for the file output
        """
        os.makedirs(output_dir, exist_ok=True)
        file_format = file_format.lower()
        for attempt in range(retries):

            if url is None or output_dir is None:
                print("URL or Output directory cannot be None")
                return

            try:
                with yt_dlp.YoutubeDL() as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                    is_playlist = info_dict.get('_type') == 'playlist'

                    if is_playlist:
                        self.download_playlist(url, output_dir, info_dict, file_format, threads, with_meta,
                                               show_album_cover_on_mp3,
                                               album_cover_image,
                                               retries, backoff_factor,
                                               file_name_template, is_playlist)
                        return
                    else:
                        if file_format in self.audio_formats:
                            self._download_audio(url, output_dir, info_dict, file_format, with_meta,
                                                 show_album_cover_on_mp3,
                                                 album_cover_image,
                                                 file_name_template, is_playlist)
                        else:
                            self._download_video(url, output_dir, info_dict, file_format, with_meta, album_cover_image,
                                                 file_name_template, is_playlist)
                        return

            except (yt_dlp.utils.DownloadError, HTTPSConnection, ReadTimeoutError) as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    sleep_time = backoff_factor * (2 ** attempt)
                    print(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    print("All retries failed.")
                    raise

    def download_playlist(self, url: str, output_dir: str, info_dict: dict, file_format: str, threads,
                          with_meta: bool = True,
                          show_album_cover: bool = True,
                          album_cover_image: str = None, retries: int = 5,
                          backoff_factor: float = 1,
                          file_name_template: str = "{title}", is_playlist: bool = False) -> None:
        playlist_name = info_dict.get('title', 'playlist')
        sanitized_playlist_name = self._sanitize_for_windows(playlist_name)
        playlist_dir = os.path.join(output_dir, sanitized_playlist_name)
        os.makedirs(playlist_dir, exist_ok=True)
        output_dir = playlist_dir
        print(f"Downloading playlist: {playlist_name}")

        with ThreadPoolExecutor(max_workers=threads) as executor:
            future_to_entry = {
                executor.submit(self._download_entry, entry, output_dir, file_format, with_meta, show_album_cover,
                                album_cover_image, file_name_template, is_playlist, retries, backoff_factor): entry
                for entry in info_dict.get('entries', [])
            }

            for future in as_completed(future_to_entry):
                entry = future_to_entry[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"Download failed for entry {entry['title']}: {e}")

    def _download_entry(self, entry, output_dir, file_format, with_meta, show_album_cover, album_cover_image,
                        file_name_template, is_playlist, retries, backoff_factor):
        for attempt in range(retries):
            try:
                if file_format in self.audio_formats:
                    self._download_audio(entry.get("webpage_url"), output_dir, entry, file_format, with_meta,
                                         show_album_cover, album_cover_image, file_name_template, is_playlist)
                else:
                    self._download_video(entry.get("webpage_url"), output_dir, entry, file_format, with_meta,
                                         album_cover_image, file_name_template, is_playlist)
                break

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
                        file_name_template: str = "{title}", is_playlist: bool = False) -> None:
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
            'noplaylist': True,  # Ensures only the single video is processed
            # 'quiet': True,  # Reduces output verbosity
            'no_warnings': True,  # Suppresses warnings
            'extract_flat': True,  # Extracts information without downloading extra metadata
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if with_meta:
            temp_output_file = tempfile.mktemp(suffix=f".{file_format}")
            self._add_metadata_to_file(output_file_path, temp_output_file, meta_data)
            shutil.copy(temp_output_file, output_file_path)
            os.remove(temp_output_file)

        if album_cover_image is None:
            thumbnail_url = meta_data.get('thumbnail_url')
            if thumbnail_url:
                album_cover_image = self._download_image_to_temp(thumbnail_url)

        if album_cover_image:
            temp_output_file = tempfile.mktemp(suffix=f".{file_format}")
            self._add_cover_image_to_audio(output_file_path, temp_output_file, album_cover_image)
            shutil.copy(temp_output_file, output_file_path)
            os.remove(temp_output_file)

    def _download_video(self, url: str, output_dir: str, info_dict: dict, file_format: str, with_meta: bool = True,
                        album_cover_image: str = None,
                        file_name_template: str = "{title}", is_playlist: bool = False) -> None:
        meta_data = self._extract_meta_from_info_dict(info_dict)
        file_name = self._resolve_file_name_template(file_name_template, meta_data)
        output_file_path = os.path.join(output_dir, file_name + "." + file_format)

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'noplaylist': True,  # Ensures only the single video is processed
            # 'quiet': True,  # Reduces output verbosity
            'no_warnings': True,  # Suppresses warnings
            'extract_flat': True,  # Extracts information without downloading extra metadata
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

    @staticmethod
    def _add_cover_image_to_audio(input_file_path: str, output_file_path: str, thumbnail_image: str):
        command = [
            'ffmpeg',
            '-i', input_file_path,  # Input MP3 file
            '-i', thumbnail_image,  # Cover image file
            '-map', '0',  # Map all streams from the MP3 file
            '-map', '1',  # Map the cover image file
            '-c', 'copy',  # Copy streams without re-encoding
            '-id3v2_version', '3',  # Use ID3v2 version 3
            '-metadata:s:t:0', 'mimetype=image/jpeg',  # Set the MIME type of the image
            '-y',  # Overwrite output file without asking
            output_file_path  # Output MP3 file with cover
        ]
        subprocess.run(command, check=True)

    @staticmethod
    def _extract_meta_from_info_dict(info_dict) -> dict:
        artist = info_dict.get('artist', info_dict.get('channel'))
        artist_str = ', '.join(artist) if isinstance(artist, list) else artist
        metadata = {
            'title': info_dict.get('title', ''),
            'description': info_dict.get('description', ''),
            'artist': artist_str,
            'year': info_dict.get('year', ''),
            'author_url': info_dict.get('channel_url', ''),
            'album': info_dict.get('playlist', ''),
            'release_date': info_dict.get('release_date', ''),
            'genre': ', '.join(info_dict.get('categories', [])),
            'duration': info_dict.get('duration', ''),
            'thumbnail_url': info_dict.get('thumbnail', ''),
            'channel': info_dict.get('uploader', ''),
            'channel_url': info_dict.get('uploader_url', ''),
            'video_url': info_dict.get('url', ''),
        }
        return metadata

    @staticmethod
    def _resolve_file_name_template(file_name_format: str, meta_data: dict) -> str:
        file_name = file_name_format
        for key, value in meta_data.items():
            if isinstance(value, str):
                placeholder = f"{{{key}}}"
                file_name = file_name.replace(placeholder, value)
        return file_name

    @staticmethod
    def _add_metadata_to_file(input_file_path, output_file_path, metadata):
        metadata_args = [
            '-metadata', f'title={metadata.get("title", "")}',
            '-metadata', f'description={metadata.get("description", "")}',
            '-metadata', f'artist={metadata.get("artist", "")}',
            '-metadata', f'album={metadata.get("album", "")}',
            '-metadata', f'release_date={metadata.get("release_date", "")}',
            '-metadata', f'genre={metadata.get("genre", "")}',
            '-metadata', f'duration={metadata.get("duration", "")}',
            '-metadata', f'thumbnail_url={metadata.get("thumbnail_url", "")}',
            '-metadata', f'channel={metadata.get("channel", "")}',
            '-metadata', f'channel_url={metadata.get("channel_url", "")}',
            '-metadata', f'video_url={metadata.get("video_url", "")}',
            '-metadata', f'year={metadata.get("year", "")}'
        ]

        command = [
            'ffmpeg',
            '-i', input_file_path,
            *metadata_args,
            '-c', 'copy',
            '-y',
            output_file_path
        ]

        print(f"Adding metadata with command: {' '.join(command)}")
        subprocess.run(command, check=True)

    @staticmethod
    def _download_image_to_temp(url: str) -> str:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        temp_file = tempfile.mktemp(suffix='.jpg')
        with open(temp_file, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        return temp_file

    @staticmethod
    def _sanitize_for_windows(name):
        return re.sub(r'[<>:"/\\|?*]', '', name)

    @staticmethod
    def _add_cover_image_to_video(input_file_path: str, output_file_path: str, album_cover_image: str):
        command = [
            'ffmpeg',
            '-i', input_file_path,  # Input video file
            '-i', album_cover_image,  # Cover image file
            '-map', '0',  # Map all streams from the video file
            '-map', '1',  # Map the cover image file
            '-c', 'copy',  # Copy streams without re-encoding
            '-disposition:v:1', 'attached_pic',  # Set the disposition for the cover image
            '-y',  # Overwrite output file without asking
            output_file_path  # Output video file with cover
        ]
        subprocess.run(command, check=True)

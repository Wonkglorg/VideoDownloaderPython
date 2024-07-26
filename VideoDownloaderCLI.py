from Downloader import YTVideoDownloader


class VideoDownloaderCLI:
    def __init__(self, url: str,
                 output_dir: str,
                 album_image: str,
                 file_format: str,
                 show_album_cover_on_mp3: bool,
                 low_hardware_mode: bool,
                 with_metadata: bool,
                 subfolder_playlists: bool,
                 single_frame_video: bool,
                 retries: int,
                 backoff_factor: float,
                 threads: int,
                 file_name_template: str):

        downloader = YTVideoDownloader()

        if single_frame_video:
            downloader.download_single_frame_video(url, output_dir, album_image, low_hardware_mode, with_metadata,
                                                   subfolder_playlists, retries, backoff_factor, file_name_template)
        else:
            downloader.download(url, output_dir, file_format, with_metadata, retries, backoff_factor,
                                show_album_cover_on_mp3, subfolder_playlists, album_image, threads, file_name_template)

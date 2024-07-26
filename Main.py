import argparse

from VideoDownloaderCLI import VideoDownloaderCLI
from VideoDownloaderUI import VideoDownloaderUI


# todo:jmd open ui if file is clicked directly and not opened using cmd.

def main():
    parser = argparse.ArgumentParser(description="YouTube Video Downloader with optional UI")
    parser.add_argument('--ui', action='store_true', help="Launch the downloader with a graphical user interface")
    parser.add_argument('-url', type=str, required=True, help="The URL of the video or playlist to download")
    parser.add_argument('-directory', type=str, required=True, help="The directory where the video will be saved")
    parser.add_argument('-image', type=str, help="The path to the album image")
    parser.add_argument('-file_format', type=str, default="mp4", help="The format of the output file (default: mp4)")
    parser.add_argument('--with_meta', action='store_true', default=True, help="Include metadata (default: True)")
    parser.add_argument('-retries', type=int, default=5, help="Number of download retries before quitting (default: 5)")
    parser.add_argument('-backoff_factor', type=float, default=1,
                        help="Exponential backoff factor for retries (default: 1)")
    parser.add_argument('--show_album_cover_on_mp3', action='store_true', default=True,
                        help="Show album cover on mp3 (default: True)")
    parser.add_argument('--subfolder_playlists', action='store_true', default=True,
                        help="Organize playlists into subfolders (default: True)")
    parser.add_argument('-threads', type=int, default=4, help="Number of download threads (default: 4)")
    parser.add_argument('-file_name_template', type=str, default="{title}",
                        help="Template for the output file name (default: {title})")
    parser.add_argument('--single_frame_video', action='store_true', default=False,
                        help="If the Video should be rendered as a single frame (requires an -image to be present")
    parser.add_argument('--low_hardware_mode', action='store_true', default=False,
                        help="(Only functional when --single_frame_video is present), if true downloads the mp4 and converts it to a still image (requires an less cpu power to convert but longer download times) if false downloads an mp3 version and converts it to an mp4 (requires more cpu power to convert but less download times)")

    args = parser.parse_args()

    url = args.url
    directory = args.directory
    image_path = args.image
    file_format = args.file_format
    with_meta = args.with_meta
    retries = args.retries
    backoff_factor = args.backoff_factor
    show_album_cover_on_mp3 = args.show_album_cover_on_mp3
    subfolder_playlists = args.subfolder_playlists
    threads = args.threads
    file_name_template = args.file_name_template
    single_frame_video = args.single_frame_video
    low_hardware_mode = args.low_hardware_mode

    if args.ui:
        VideoDownloaderUI(url, directory, image_path, file_format, show_album_cover_on_mp3, low_hardware_mode,
                          with_meta,
                          subfolder_playlists, single_frame_video, retries, backoff_factor, threads,
                          file_name_template)
    else:
        VideoDownloaderCLI(url, directory, image_path, file_format, show_album_cover_on_mp3, low_hardware_mode,
                           with_meta,
                           subfolder_playlists, single_frame_video, retries, backoff_factor, threads,
                           file_name_template)


if __name__ == "__main__":
    main()

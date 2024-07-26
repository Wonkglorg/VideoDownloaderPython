import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

import yt_dlp


# todo:jmd correctly input ui values from inputs, or run defaults.
# Add defaults global values to make sure they all are the same and don't need changes in so many places


class VideoDownloaderUI:
    def __init__(self,
                 url: str,
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
                 file_name_template: str
                 ):
        # Create the main window
        root = tk.Tk()
        root.title("YouTube Downloader and Converter")

        # URL Entry
        tk.Label(root, text="YouTube URL:").grid(row=0, column=0, padx=10, pady=10)
        url_entry = tk.Entry(root, width=50)
        url_entry.grid(row=0, column=1, padx=10, pady=10)

        # Output Directory Entry
        tk.Label(root, text="Output Directory (optional):").grid(row=1, column=0, padx=10, pady=10)
        dir_entry = tk.Entry(root, width=50)
        dir_entry.grid(row=1, column=1, padx=10, pady=10)
        tk.Button(root, text="Browse", command=browse_directory).grid(row=1, column=2, padx=10, pady=10)

        # Thumbnail Entry
        tk.Label(root, text="Thumbnail Image:").grid(row=2, column=0, padx=10, pady=10)
        thumbnail_entry = tk.Entry(root, width=50)
        thumbnail_entry.grid(row=2, column=1, padx=10, pady=10)
        tk.Button(root, text="Browse", command=browse_thumbnail).grid(row=2, column=2, padx=10, pady=10)

        # MP4 Download Option
        mp4_var = tk.BooleanVar(value=True)
        tk.Checkbutton(root, text="Download as MP4", variable=mp4_var).grid(row=3, column=1, padx=10, pady=10)

        # Submit Button
        tk.Button(root, text="Download and Convert", command=process_input).grid(row=4, column=1, padx=10, pady=20)

        # Run the main loop
        root.mainloop()


def process_input():
    url = url_entry.get()
    output_dir = dir_entry.get()
    thumbnail_file = thumbnail_entry.get()
    download_as_mp4 = mp4_var.get()

    if not url:
        messagebox.showerror("Input Error", "YouTube URL must be filled in.")
        return

    if not output_dir:
        output_dir = os.getcwd()

    if not os.path.isdir(output_dir):
        messagebox.showerror("Directory Error", "The specified output directory does not exist.")
        return

    if not thumbnail_file or not os.path.isfile(thumbnail_file):
        messagebox.showerror("Thumbnail Error", "The specified thumbnail image does not exist.")
        return

    try:
        main(url, output_dir, thumbnail_file, download_as_mp4)
    except Exception as e:
        messagebox.showerror("Error", str(e))


def browse_directory():
    directory = filedialog.askdirectory()
    if directory:
        dir_entry.delete(0, tk.END)
        dir_entry.insert(0, directory)


def browse_thumbnail():
    file = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
    if file:
        thumbnail_entry.delete(0, tk.END)
        thumbnail_entry.insert(0, file)


def main(url, output_dir, thumbnail_file, download_as_mp4):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    with yt_dlp.YoutubeDL() as ydl:
        info_dict = ydl.extract_info(url, download=False)

    metadata = extract_metadata_from_info_dict(info_dict)

    if 'entries' in info_dict:
        # It's a playlist
        playlist_name = info_dict.get('title', 'playlist')
        sanitized_playlist_name = sanitize_for_windows(playlist_name)
        playlist_dir = os.path.join(output_dir, sanitized_playlist_name)
        os.makedirs(playlist_dir, exist_ok=True)
        print(f"Downloading playlist: {playlist_name}")

        # Download the playlist with retries
        if download_as_mp4:
            download_with_retries(url, playlist_dir, is_playlist=True, is_audio=False)
        else:
            download_with_retries(url, playlist_dir, is_playlist=True, is_audio=True)

        # Convert files if necessary
        for root, _, files in os.walk(playlist_dir):
            for file in files:
                if file.endswith('.part'):  # Skip incomplete downloads
                    continue
                input_file = os.path.join(root, file)
                if download_as_mp4:
                    if is_video_file(input_file):
                        try:
                            output_file = os.path.join(root, file)  # Define the output file path
                            convert_video(input_file, output_file, thumbnail_file, metadata)
                            delete_file(input_file)  # Optionally delete the original video file
                        except subprocess.CalledProcessError as e:
                            print(f"Error converting file {input_file}: {e}")
                else:
                    if file.lower().endswith('.mp3'):
                        output_file = os.path.join(root, f"{os.path.splitext(file)[0]}.mp4")
                        try:
                            convert_audio_to_video(input_file, output_file, thumbnail_file, metadata)
                            delete_file(input_file)  # Optionally delete the original audio file
                        except subprocess.CalledProcessError as e:
                            print(f"Error converting file {input_file}: {e}")
    else:
        # It's a single video
        print(f"Downloading video: {info_dict['title']}")

        # Download the video or audio with retries
        if download_as_mp4:
            download_with_retries(url, output_dir, is_playlist=False, is_audio=False)
        else:
            download_with_retries(url, output_dir, is_playlist=False, is_audio=True)

        # Convert files if necessary
        for root, _, files in os.walk(output_dir):
            for file in files:
                if file.endswith('.part'):  # Skip incomplete downloads
                    continue
                input_file = os.path.join(root, file)
                if download_as_mp4:
                    if is_video_file(input_file):
                        try:
                            output_file = os.path.join(output_dir, file)  # Define the output file path
                            convert_video(input_file, output_file, thumbnail_file, metadata)
                            delete_file(input_file)  # Optionally delete the original video file
                        except subprocess.CalledProcessError as e:
                            print(f"Error converting file {input_file}: {e}")
                else:
                    if file.lower().endswith('.mp3'):
                        output_file = os.path.join(output_dir, f"{os.path.splitext(file)[0]}.mp4")
                        try:
                            convert_audio_to_video(input_file, output_file, thumbnail_file, metadata)
                            delete_file(input_file)  # Optionally delete the original audio file
                        except subprocess.CalledProcessError as e:
                            print(f"Error converting file {input_file}: {e}")


if __name__ == "__main__":
    VideoDownloaderUI("", "", "", "", False, False, True, False, False, 5, 1.0, 4, "{name}")

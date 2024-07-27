import os
import subprocess
from tkinter import filedialog, messagebox

import customtkinter as ctk
import yt_dlp

from Downloader import YTVideoDownloader


# todo:jmd correctly input ui values from inputs, or run defaults.
# todo: show tooltops for all entries
# todo, add option to show previews of the downloaded videos, so I can choose to only get some of them (should clear each selection, so it lets me stilluse the album as a way to seperate them)
# Curreent method is relativly slow for getting preview dat aoptimize later.
# Add defaults global values to make sure they all are the same and don't need changes in so many places

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(tw, text=self.text, justify='left',
                             fg_color="white", corner_radius=5,
                             text_color="black", font=("tahoma", 12))
        label.pack(ipadx=1, ipady=1)

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

class VideoDownloaderUI:
    downloader = YTVideoDownloader()

    def __init__(self,
                 url: str = "",
                 output_dir: str = "",
                 album_image: str = "",
                 file_format: str = "mp4",
                 show_album_cover_on_mp3: bool = True,
                 low_hardware_mode: bool = False,
                 with_metadata: bool = True,
                 subfolder_playlists: bool = True,
                 single_frame_video: bool = False,
                 retries: int = 5,
                 backoff_factor: float = 1.0,
                 threads: int = 4,
                 file_name_template: str = "%(name)"
                 ):
        self.url = url
        self.output_dir = output_dir
        self.album_image = album_image
        self.file_format = file_format
        self.show_album_cover_on_mp3 = show_album_cover_on_mp3
        self.low_hardware_mode = low_hardware_mode
        self.with_metadata = with_metadata
        self.subfolder_playlists = subfolder_playlists
        self.single_frame_video = single_frame_video
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.threads = threads
        self.file_name_template = file_name_template

        # Create the main window
        self.root = ctk.CTk()
        self.root.title("YouTube Downloader and Converter")

        # URL Entry
        ctk.CTkLabel(self.root, text="YouTube URL:").grid(row=0, column=0, padx=10, pady=10)
        self.url_entry = ctk.CTkEntry(self.root, width=400)
        self.url_entry.grid(row=0, column=1, padx=10, pady=10)
        self.url_entry.insert(0, self.url)
        ToolTip(self.url_entry, "Enter the URL of the YouTube video you want to download.")

        # Output Directory Entry
        ctk.CTkLabel(self.root, text="Output Directory (optional):").grid(row=1, column=0, padx=10, pady=10)
        self.dir_entry = ctk.CTkEntry(self.root, width=400)
        self.dir_entry.grid(row=1, column=1, padx=10, pady=10)
        self.dir_entry.insert(0, self.output_dir)
        ctk.CTkButton(self.root, text="Browse", command=self.browse_directory).grid(row=1, column=2, padx=10, pady=10)
        ToolTip(self.dir_entry, "Select the directory where the downloaded files will be saved.")

        # Thumbnail Entry
        ctk.CTkLabel(self.root, text="Thumbnail Image:").grid(row=2, column=0, padx=10, pady=10)
        self.thumbnail_entry = ctk.CTkEntry(self.root, width=400)
        self.thumbnail_entry.grid(row=2, column=1, padx=10, pady=10)
        self.thumbnail_entry.insert(0, self.album_image)
        ctk.CTkButton(self.root, text="Browse", command=self.browse_thumbnail).grid(row=2, column=2, padx=10, pady=10)
        ToolTip(self.thumbnail_entry, "Select the thumbnail image for the video.")

        # File Format Option
        ctk.CTkLabel(self.root, text="File Format:").grid(row=3, column=0, padx=10, pady=10)
        self.file_format_var = ctk.StringVar(value=self.file_format)
        all_formats = self.downloader.video_formats + self.downloader.audio_formats
        self.file_format_menu = ctk.CTkOptionMenu(self.root, variable=self.file_format_var, values=all_formats)
        self.file_format_menu.grid(row=3, column=1, padx=10, pady=10)
        ToolTip(self.file_format_menu, "Choose the format for the downloaded file.")

        # Show Album Cover on MP3 Option
        self.album_cover_var = ctk.BooleanVar(value=self.show_album_cover_on_mp3)
        self.album_cover_check = ctk.CTkCheckBox(self.root, text="Show Album Cover on MP3", variable=self.album_cover_var)
        self.album_cover_check.grid(row=4, column=0, padx=10, pady=10)
        ToolTip(self.album_cover_check, "Show album cover when downloading MP3 files.")

        # Low Hardware Mode Option
        self.low_hardware_var = ctk.BooleanVar(value=self.low_hardware_mode)
        self.low_hardware_check = ctk.CTkCheckBox(self.root, text="Low Hardware Mode", variable=self.low_hardware_var)
        self.low_hardware_check.grid(row=4, column=1, padx=10, pady=10)
        ToolTip(self.low_hardware_check, "Enable low hardware mode for slower computers.")

        # With Metadata Option
        self.with_metadata_var = ctk.BooleanVar(value=self.with_metadata)
        self.with_metadata_check = ctk.CTkCheckBox(self.root, text="Include Metadata", variable=self.with_metadata_var)
        self.with_metadata_check.grid(row=5, column=0, padx=10, pady=10)
        ToolTip(self.with_metadata_check, "Include metadata in the downloaded files.")

        # Subfolder Playlists Option
        self.subfolder_playlists_var = ctk.BooleanVar(value=self.subfolder_playlists)
        self.subfolder_playlists_check = ctk.CTkCheckBox(self.root, text="Subfolder for Playlists", variable=self.subfolder_playlists_var)
        self.subfolder_playlists_check.grid(row=5, column=1, padx=10, pady=10)
        ToolTip(self.subfolder_playlists_check, "Create subfolders for playlist downloads.")

        # Single Frame Video Option
        self.single_frame_video_var = ctk.BooleanVar(value=self.single_frame_video)
        self.single_frame_video_check = ctk.CTkCheckBox(self.root, text="Single Frame Video", variable=self.single_frame_video_var)
        self.single_frame_video_check.grid(row=6, column=0, padx=10, pady=10)
        ToolTip(self.single_frame_video_check, "Download only a single frame of the video.")

        # Retries Entry
        ctk.CTkLabel(self.root, text="Retries:").grid(row=6, column=1, padx=10, pady=10)
        self.retries_entry = ctk.CTkEntry(self.root, width=50)
        self.retries_entry.grid(row=6, column=2, padx=10, pady=10)
        self.retries_entry.insert(0, self.retries)
        ToolTip(self.retries_entry, "Set the number of retries for downloading.")

        # Backoff Factor Entry
        ctk.CTkLabel(self.root, text="Backoff Factor:").grid(row=7, column=0, padx=10, pady=10)
        self.backoff_entry = ctk.CTkEntry(self.root, width=50)
        self.backoff_entry.grid(row=7, column=1, padx=10, pady=10)
        self.backoff_entry.insert(0, self.backoff_factor)
        ToolTip(self.backoff_entry, "Set the backoff factor for retries.")

        # Threads Entry
        ctk.CTkLabel(self.root, text="Threads:").grid(row=7, column=2, padx=10, pady=10)
        self.threads_entry = ctk.CTkEntry(self.root, width=50)
        self.threads_entry.grid(row=7, column=3, padx=10, pady=10)
        self.threads_entry.insert(0, self.threads)
        ToolTip(self.threads_entry, "Set the number of threads for downloading.")

        # File Name Template Entry
        ctk.CTkLabel(self.root, text="File Name Template:").grid(row=8, column=0, padx=10, pady=10)
        self.template_entry = ctk.CTkEntry(self.root, width=400)
        self.template_entry.grid(row=8, column=1, padx=10, pady=10)
        self.template_entry.insert(0, self.file_name_template)
        ToolTip(self.template_entry, "Set the template for the file name.")

        # Submit Button
        ctk.CTkButton(self.root, text="Download and Convert", command=self.process_input).grid(row=9, column=1, padx=10, pady=20)

        # Run the main loop
        self.root.mainloop()

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, ctk.END)
            self.dir_entry.insert(0, directory)

    def browse_thumbnail(self):
        thumbnail = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.png")])
        if thumbnail:
            self.thumbnail_entry.delete(0, ctk.END)
            self.thumbnail_entry.insert(0, thumbnail)

    def process_input(self):
        # Placeholder function to process input and start download/conversion
        print("Processing input...")
        print("URL:", self.url_entry.get())
        print("Output Directory:", self.dir_entry.get())
        print("Thumbnail Image:", self.thumbnail_entry.get())
        print("File Format:", self.file_format_var.get())
        print("Show Album Cover on MP3:", self.album_cover_var.get())
        print("Low Hardware Mode:", self.low_hardware_var.get())
        print("Include Metadata:", self.with_metadata_var.get())
        print("Subfolder for Playlists:", self.subfolder_playlists_var.get())
        print("Single Frame Video:", self.single_frame_video_var.get())
        print("Retries:", self.retries_entry.get())
        print("Backoff Factor:", self.backoff_entry.get())
        print("Threads:", self.threads_entry.get())
        print("File Name Template:", self.template_entry.get())


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

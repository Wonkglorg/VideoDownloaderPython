from tkinter import filedialog, messagebox

import customtkinter as ctk

from Downloader import YTVideoDownloader


# todo label and correctly hide values if not available in that selection example: single fram evideo
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.id = None
        self.widget.bind("<Enter>", self.schedule_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def schedule_tooltip(self, event):
        self.id = self.widget.after(500, self.show_tooltip)  # 500ms delay before showing the tooltip

    def show_tooltip(self):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(tw, text=self.text, justify='left', bg_color="#000000", fg_color="#000000",
                             corner_radius=5, font=("Tahoma", 12))
        label.pack(ipadx=1, ipady=1)

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None


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
                 single_frame_video: bool = True,
                 retries: int = 5,
                 backoff_factor: float = 1.0,
                 threads: int = 4,
                 file_name_template: str = "%(name)",
                 download_meta=False
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
        self.download_meta = download_meta

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
        self.album_cover_check = ctk.CTkCheckBox(self.root, text="Show Album Cover on MP3",
                                                 variable=self.album_cover_var)
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
        self.subfolder_playlists_check = ctk.CTkCheckBox(self.root, text="Subfolder for Playlists",
                                                         variable=self.subfolder_playlists_var)
        self.subfolder_playlists_check.grid(row=5, column=1, padx=10, pady=10)
        ToolTip(self.subfolder_playlists_check, "Create subfolders for playlist downloads.")

        # Single Frame Video Option
        self.single_frame_video_var = ctk.BooleanVar(value=self.single_frame_video)
        self.single_frame_video_check = ctk.CTkCheckBox(self.root, text="Single Frame Video",
                                                        variable=self.single_frame_video_var)
        self.single_frame_video_check.grid(row=6, column=0, padx=10, pady=10)
        ToolTip(self.single_frame_video_check, "Download only a single frame of the video.")

        # Download Meta Option
        self.download_meta_var = ctk.BooleanVar(value=self.download_meta)
        self.download_meta_file = ctk.CTkCheckBox(self.root, text="Download Meta Data File",
                                                  variable=self.download_meta_var)
        self.download_meta_file.grid(row=6, column=1, padx=10, pady=10)
        ToolTip(self.download_meta_file, "Download Meta seperatly.")

        # Retries Entry
        ctk.CTkLabel(self.root, text="Retries:").grid(row=6, column=2, padx=10, pady=10)
        self.retries_entry = ctk.CTkEntry(self.root, width=50)
        self.retries_entry.grid(row=6, column=3, padx=10, pady=10)
        self.retries_entry.insert(0, self.retries)
        ToolTip(self.retries_entry, "Set the number of retries for downloading.")

        # Backoff Factor Entry
        ctk.CTkLabel(self.root, text="Backoff Factor:").grid(row=7, column=1, padx=10, pady=10)
        self.backoff_entry = ctk.CTkEntry(self.root, width=50)
        self.backoff_entry.grid(row=7, column=2, padx=10, pady=10)
        self.backoff_entry.insert(0, self.backoff_factor)
        ToolTip(self.backoff_entry, "Set the backoff factor for retries.")

        # Threads Entry
        ctk.CTkLabel(self.root, text="Threads:").grid(row=7, column=2, padx=10, pady=10)
        self.threads_entry = ctk.CTkEntry(self.root, width=50)
        self.threads_entry.grid(row=8, column=0, padx=10, pady=10)
        self.threads_entry.insert(0, self.threads)
        ToolTip(self.threads_entry, "Set the number of threads for downloading.")

        # File Name Template Entry
        ctk.CTkLabel(self.root, text="File Name Template:").grid(row=8, column=0, padx=10, pady=10)
        self.template_entry = ctk.CTkEntry(self.root, width=400)
        self.template_entry.grid(row=8, column=1, padx=10, pady=10)
        self.template_entry.insert(0, self.file_name_template)
        ToolTip(self.template_entry, "Set the template for naming downloaded files.")

        # Quality Preset Dropdown
        ctk.CTkLabel(self.root, text="Quality Preset:").grid(row=9, column=0, padx=10, pady=10)
        self.quality_preset_var = ctk.StringVar(value="1080p")
        quality_presets = ["144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p"]
        self.quality_preset_menu = ctk.CTkOptionMenu(self.root, variable=self.quality_preset_var,
                                                     values=quality_presets)
        self.quality_preset_menu.grid(row=9, column=1, padx=10, pady=10)
        ToolTip(self.quality_preset_menu, "Choose the quality preset for the download.")

        # Download Button
        self.download_button = ctk.CTkButton(self.root, text="Download", command=self.download_video)
        self.download_button.grid(row=10, column=0, columnspan=2, padx=10, pady=20)
        ToolTip(self.download_button, "Click to start downloading the video.")

        self.root.mainloop()

    def browse_directory(self):
        selected_dir = filedialog.askdirectory()
        if selected_dir:
            self.dir_entry.delete(0, ctk.END)
            self.dir_entry.insert(0, selected_dir)

    def browse_thumbnail(self):
        selected_image = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif")])
        if selected_image:
            self.thumbnail_entry.delete(0, ctk.END)
            self.thumbnail_entry.insert(0, selected_image)

    def download_video(self):
        self.url = self.url_entry.get()
        self.output_dir = self.dir_entry.get()
        self.album_image = self.thumbnail_entry.get()
        self.file_format = self.file_format_var.get()
        self.show_album_cover_on_mp3 = self.album_cover_var.get()
        self.low_hardware_mode = self.low_hardware_var.get()
        self.with_metadata = self.with_metadata_var.get()
        self.subfolder_playlists = self.subfolder_playlists_var.get()
        self.single_frame_video = self.single_frame_video_var.get()
        self.retries = int(self.retries_entry.get())
        self.backoff_factor = float(self.backoff_entry.get())
        self.threads = int(self.threads_entry.get())
        self.file_name_template = self.template_entry.get()
        self.quality_preset = self.quality_preset_var.get()
        self.download_meta = self.download_meta_var.get()

        if (self.single_frame_video):
            YTVideoDownloader().download_single_frame_video(
                url=self.url,
                output_dir=self.output_dir,
                album_image=self.album_image,
                low_hardware_mode=self.low_hardware_mode,
                with_metadata=self.with_metadata,
                subfolder_playlists=self.subfolder_playlists,
                retries=self.retries,
                backoff_factor=self.backoff_factor,
                download_meta_seperate=self.download_meta
                # file_name_template=self.file_name_template,
            )
        else:

            YTVideoDownloader().download(
                url=self.url,
                output_dir=self.output_dir,
                album_cover_image=self.album_image,
                file_format=self.file_format,
                show_album_cover_on_mp3=self.show_album_cover_on_mp3,
                with_meta=self.with_metadata,
                subfolder_playlists=self.subfolder_playlists,
                retries=self.retries,
                backoff_factor=self.backoff_factor,
                threads=self.threads,
                download_meta_seperate=self.download_meta
                # file_name_template=self.file_name_template
            )
        messagebox.showinfo("Download Complete", "The video has been successfully downloaded.")


if __name__ == "__main__":
    app = VideoDownloaderUI()

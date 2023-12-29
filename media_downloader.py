from CTkMessagebox import CTkMessagebox
from tkinter import ttk, filedialog
import customtkinter
import threading
import tkinter
import yt_dlp
import os

"""
command to make an exe file using pyinstaller:
pyinstaller --name=MediaDownloader --onefile --windowed --icon=icon.ico --upx-dir=/home/rafail/Documents/upx --collect-all customtkinter --collect-all CTkMessagebox --collect-all ffmpeg --hidden-import='PIL._tkinter_finder' media_downloader.py
"""

def get_link_info(search_query):
    """
    The `get_link_info` function extracts information (title and URL) from a YouTube video given a
    search query or a direct video link.
    
    :param search_query: The `search_query` parameter is a string that represents the query to search
    for on YouTube. It can be either a URL of a YouTube video or a search term
    :return: The function `get_link_info` returns a tuple containing the title and URL of a video or
    webpage.
    """
    try:
        ydl_opts = {
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if search_query.startswith("http"):
                info = ydl.extract_info(search_query, download=False)
            else:
                query = f"ytsearch:{search_query}"
                search_results = ydl.extract_info(query, download=False)['entries']
                if not search_results:
                    raise ValueError(f"No results found for query: {search_query}")
                info = search_results[0]

            title = info.get('title', 'Title not found')
            url = info.get('webpage_url', 'URL not found')
            title = sanitize_title(title)
        return title, url

    except Exception as e:
        show_error(f"An error occurred: {str(e)}")
        return None

def replace_extensions(in_download_path, download_path):
    """
    The function `replace_extensions` takes in a download path and replaces the file extensions of any
    webm or mkv files in that path with mp4.
    
    :param in_download_path: The `in_download_path` parameter is the path to the directory where the
    video files are currently located. This is the directory from which the video files will be
    processed and have their extensions replaced
    :param download_path: The `download_path` parameter is the path where the downloaded files are
    stored. It is the directory where the files with the extensions `.webm` and `.mkv` are located
    """
    # Define the list of video extensions to handle
    webm_file = [filename for filename in os.listdir(in_download_path) if filename.endswith('.webm')]
    mkv_file = [filename for filename in os.listdir(in_download_path) if filename.endswith('.mkv')]

    if webm_file:
        if download_path != None:
            webm_file = download_path + ".webm"
        mp4_filename = webm_file.replace('.webm', '.mp4')
        os.rename(webm_file, mp4_filename)
    
    if mkv_file:
        if download_path != None:
            mkv_file = download_path + ".mkv"
        mp4_filename = mkv_file.replace('.mkv', '.mp4')
        os.rename(mkv_file, mp4_filename)

def get_playlist_info(playlist_url):
    """
    The function `get_playlist_info` extracts information from a YouTube playlist URL, including the
    playlist title, video titles, and video URLs.
    
    :param playlist_url: The `playlist_url` parameter is the URL of the YouTube playlist that you want
    to extract information from
    :return: The function `get_playlist_info` returns three values: `playlist_title`, `titles`, and
    `urls`.
    """
    youtube_dlp_options = {
        'extract_flat': True,
        'skip_unavailable_fragments': True,
        'quiet': True,
        'dump_single_json': True,
    }

    try:
        with yt_dlp.YoutubeDL(youtube_dlp_options) as yt_downloader:
            data = yt_downloader.extract_info(playlist_url, download=False)
            playlist_title = data.get('title', 'Untitled') + ".txt"
            playlist_titles = [entry['title'] for entry in data.get('entries', []) if
                               'title' in entry and 'url' in entry]
            urls = [entry['url'] for entry in data.get('entries', []) if 'title' in entry and 'url' in entry]
            titles = []
            for title in playlist_titles:
                title = sanitize_title(title)
                titles.append(title)
        playlist_title = sanitize_title(playlist_title)
    except yt_dlp.utils.DownloadError as e:
        show_error("There was an error while downloading the playlist.")
        return None, None
    return playlist_title, titles, urls

def download_from_file(download_video, video_resolution="best"):
    """
    The function `download_from_file` allows the user to select a text file containing video URLs, and
    then downloads the videos to a specified location.
    
    :param download_video: The parameter "download_video" is a boolean value that determines whether to
    download the video or just extract its information. If set to True, the video will be downloaded. If
    set to False, only the video information will be extracted
    :param video_resolution: The `video_resolution` parameter is an optional parameter that specifies
    the desired resolution of the downloaded video. By default, it is set to "best", which means the
    highest available resolution will be downloaded. However, you can pass a specific resolution value
    (e.g., "720p", "1080, defaults to best (optional)
    :return: The function does not explicitly return anything.
    """
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        folder_name = os.path.splitext(os.path.basename(file_path))[0]
        download_path = filedialog.askdirectory()

        if not download_path:
            show_error("Select a save location")
            return
        else:
            download_path = os.path.join(download_path, f"{folder_name}")

        with open(file_path, 'r') as file:
            for line in file:
                url = line.strip()
                title, url = get_link_info(url)
                download_link(url, title, download_video, video_resolution, download_path=download_path)
        show_success("Download complete")

    else:
        show_error("provide a file")

def download_link_menu(input_path_or_url, download_video, video_resolution):
    """
    The function `download_link_menu` takes an input path or URL, checks if it is a valid YouTube link,
    and downloads the video or playlist based on the specified resolution.
    
    :param input_path_or_url: The input_path_or_url parameter is a string that represents the path or
    URL of the video or playlist that needs to be downloaded. It can be a local file path or a URL of a
    video or playlist on YouTube
    :param download_video: A boolean value indicating whether to download the video or just the audio
    :param video_resolution: The `video_resolution` parameter is used to specify the desired resolution
    of the downloaded video. It allows the user to choose the quality of the video they want to download
    :return: nothing.
    """
    if not input_path_or_url:
        show_error("provide a url")
        return
    
    if input_path_or_url.startswith(("https://www.youtube.com/watch?", "https://www.youtube.com/shorts")):
        title, url = get_link_info(input_path_or_url)
        if download_link(url, title, download_video, video_resolution):
            show_success("Download complete")

    elif input_path_or_url.startswith(("https://www.youtube.com/playlist?", "https://www.youtube.com/")):
        filename, titles, urls = get_playlist_info(input_path_or_url)
        if download_playlist(filename, titles, urls, download_video, video_resolution):
            show_success("Download complete")

    elif input_path_or_url.startswith(("https://www.instagram.com/", "https://www.facebook.com/")):
        title, url = get_link_info(input_path_or_url)
        if download_link(url, title, download_video, " "):
            show_success("Download complete")

    else:
        title, url = get_link_info(input_path_or_url)
        if download_link(url, title, download_video, video_resolution):
            show_success("Download complete")

def download_link(url, title, download_video, video_resolution, download_path=None):
    """
    The function `download_link` downloads a video or audio file from a given URL and saves it to a
    specified location with the specified title and resolution.
    
    :param url: The URL of the video that you want to download
    :param title: The title parameter is a string that represents the title of the video that will be
    downloaded
    :param download_video: The `download_video` parameter is a boolean value that determines whether to
    download the video or just the audio. If `download_video` is `True`, the function will download both
    the audio and video of the specified resolution. If `download_video` is `False`, the function will
    only download the
    :param video_resolution: The `video_resolution` parameter is used to specify the desired resolution
    of the video to be downloaded. It can be set to a specific resolution value (e.g., "720p", "1080p")
    or to "best" to download the best available resolution
    :param download_path: The `download_path` parameter is the path where the downloaded video or audio
    file will be saved. It is an optional parameter, so if it is not provided, the user will be prompted
    to select a save location using a file dialog. If the user cancels or does not select a save
    location
    :return: a boolean value. It returns True if the download is successful and False if there is an
    error during the download process.
    """
    try:
        if download_path == None:
            download_path = filedialog.askdirectory()
            if not download_path:
                show_error("Select a save location")
                return

        in_download_path = download_path
        download_path = os.path.join(download_path, f"{title}")

        if download_video:
            if video_resolution == "best":
                youtube_dlp_options = {
                    'outtmpl': f'{download_path}.%(ext)s',
                    'format': 'bestaudio+bestvideo',
                    'quiet': True,
                    'progress_hooks': [update_progress],
                }

            elif video_resolution == " ":
                youtube_dlp_options = {
                    'outtmpl': f'{download_path}.%(ext)s',
                    'format': 'best',
                    'quiet': True,
                    'progress_hooks': [update_progress],
                }

            else:
                youtube_dlp_options = {
                    'outtmpl': f'{download_path}.%(ext)s',
                    'format': f'bestvideo[height<={video_resolution}]+bestaudio/best[height<={video_resolution}]',
                    'quiet': True,
                    'progress_hooks': [update_progress],
                }

        else:
            youtube_dlp_options = {
                'outtmpl': f'{download_path}.%(ext)s',
                'format': 'bestaudio',  # Download the best available audio format
                'quiet': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',  # Convert audio to MP3 format
                    'preferredquality': '192',  # Bitrate for the converted audio
                }],
                'progress_hooks': [update_progress],
            }

        with yt_dlp.YoutubeDL(youtube_dlp_options) as youtube_dlp_instance:
            current_title_label_var.set(title)
            youtube_dlp_instance.download([url])

        if download_video:
            replace_extensions(in_download_path, download_path)
            
            if language_menu.get() != None and language_menu.get() != "Select":
                download_subtitles(url, download_path)

        return True

    except yt_dlp.utils.DownloadError as e:
        show_error(f"Download error: {str(e)}")
    except Exception as e:
        show_error(f"An error occurred: {str(e)}")
    return False

def download_subtitles(url, download_path):
    """
    The function `download_subtitles` downloads subtitles for a given video URL and saves them to a
    specified download path.
    
    :param url: The URL of the video from which you want to download subtitles
    :param download_path: The `download_path` parameter is the path where you want to save the
    downloaded subtitles file. It should be a string representing the directory path where you want to
    save the file
    :return: The function does not explicitly return anything.
    """
    try:
        subtitles_lang = language_menu.get()
        if not subtitles_lang:
            show_error("Subtitles language not selected.")
            return

        youtube_dlp_options = {
            'outtmpl': f'{download_path}.%(ext)s',
            'writesubtitles': True,
            'quiet': True,
            'subtitleslangs': [subtitles_lang],
            'skip_download': True,
        }

        youtube_dlp_instance = yt_dlp.YoutubeDL(youtube_dlp_options)
        info_dict = youtube_dlp_instance.extract_info(url, download=False)

        if 'subtitles' in info_dict and subtitles_lang in info_dict['subtitles']:
            download_path = f"{download_path}.{subtitles_lang}.vtt"
            vtt_filename = download_path

            try:
                youtube_dlp_instance.download([url])

                if vtt_filename and os.path.exists(vtt_filename):
                    srt_filename = vtt_filename.replace('.vtt', '.srt')
                    os.rename(vtt_filename, srt_filename)
                else:
                    show_error(f"Subtitles download failed for {subtitles_lang}.")
            except yt_dlp.utils.DownloadError as e:
                show_error(f"Download error: {str(e)}")
            except yt_dlp.utils.ExtractorError as e:
                show_error(f"Extraction error: {str(e)}")
        else:
            show_error(f"No subtitles found in {subtitles_lang}.")

    except Exception as e:
        show_error(f"An error occurred: {str(e)}")

def download_playlist(filename, titles, urls, download_video, video_resolution): 
    """
    The function `download_playlist` downloads a playlist of videos, and
    downloads the videos to a folder with the name of the playlst title.
    
    :param filename: The title of the folder
    :param titles: The `titles` parameter is a list of titles for the videos in the playlist. Each title
    corresponds to a URL in the `urls` parameter
    :param urls: The `urls` parameter is a list of URLs that correspond to the videos in the playlist.
    Each url represents the location of a video that needs to be downloaded
    :param download_video: The parameter "download_video" is a boolean value that determines whether to
    download the video or just the audio of the playlist. If it is set to True, the function will
    download the video but if it is set to false, it will download only the audio.
    :param video_resolution: The `video_resolution` parameter is used to specify the desired resolution
    of the downloaded videos. This parameter is used in the `download_link` function to download the video with the
    specified resolution
    """
    folder_name = os.path.join(filedialog.askdirectory(), os.path.splitext(filename)[0])
    save_file = os.path.join(folder_name, filename)
    os.makedirs(folder_name)

    with open(save_file, "w", encoding="utf-8") as file:
        file.write("\n".join(titles))

    for url, title in zip(urls, titles):
        download_path = folder_name
        download_link(url, title, download_video, video_resolution, download_path)

def sanitize_title(title):
    """
    The `sanitize_title` function replaces prohibited characters in a title with underscores.
    
    :param title: The `title` parameter is a string representing the title that needs to be sanitized
    :return: the sanitized title, which is a string with any prohibited characters replaced with
    underscores.
    """
    prohibited_chars = [':', '/', '\\', '//', ',', '#', '|']
    sanitized_title = ''.join(['_' if char in prohibited_chars else char for char in title])
    return sanitized_title

def show_error(output):
    """
    The function "show_error" displays an error message using a message box.

    :param output: The error message that you want to display
    """
    CTkMessagebox(title="Error", message=output, icon="cancel")

def show_success(output):
    """
    The function `show_success` displays a success message with an output and an option to thank the
    user.
    
    :param output: The output parameter is the message that you want to display in the messagebox. It
    can be a string or any other data type that can be converted to a string
    """
    CTkMessagebox(title="Success", message=output, icon="check", option_1="Thanks")

def update_progress(data):
    """
    The function updates the progress of a download based on the total bytes and downloaded bytes.
    
    :param data: The `data` parameter is a dictionary that contains information about the progress of a
    download. It should have the following keys:
    """
    if data['status'] == 'downloading':
        total_bytes = data.get('total_bytes')
        downloaded_bytes = data.get('downloaded_bytes')

        if total_bytes and downloaded_bytes:
            progress_bar_var.set(downloaded_bytes / total_bytes * 100)

def start_download(download_option, video_resolution="best"):
    """
    The function "start_download" takes in a download option and a video resolution (with a default
    value of "best"), and based on the download option, it calls different target functions with the
    appropriate arguments to start a download thread.
    
    :param download_option: The `download_option` parameter is used to determine the type of download
    operation to perform. It can have the following values:
    :param video_resolution: The `video_resolution` parameter is a string that specifies the desired
    resolution of the video to be downloaded. By default, it is set to "best", which means the highest
    available resolution will be downloaded. However, you can pass a different resolution value to
    download videos in specific resolutions, defaults to best (optional)
    :return: The function does not explicitly return anything.
    """
    url = url_entry.get()

    if resolution_menu.get() == "Select" and (download_option == 2 or download_option == 4):
        show_error("Please select a video resolution.")
        return

    if download_option == 1:
        target_function = download_link_menu
        target_args = url, False, video_resolution

    elif download_option == 2:
        target_function = download_link_menu
        target_args = url, True, video_resolution

    elif download_option == 3:
        target_function = download_from_file
        target_args = False, video_resolution

    elif download_option == 4:
        target_function = download_from_file
        target_args = True, video_resolution

    download_thread = threading.Thread(target=target_function, args=(target_args))
    download_thread.start()

if __name__ == "__main__":
    app = customtkinter.CTk()
    app.title("Media downloader")

    # Set the window size
    window_width = 700
    window_height = 620

    # Get the screen width and height
    screen_width = app.winfo_screenwidth()
    screen_height = app.winfo_screenheight()

    # Calculate the x and y coordinates for the window to be centered
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2

    # Set the geometry of the window to center it on the screen
    app.geometry(f"{window_width}x{window_height}+{x}+{y}")

    title = customtkinter.CTkLabel(app, text="Insert a url or a title")
    title.pack()

    url_entry_var = tkinter.StringVar()
    url_entry = customtkinter.CTkEntry(app, width=350, textvariable=url_entry_var)
    url_entry.pack()

    progress_bar_var = tkinter.DoubleVar()
    progress_bar = ttk.Progressbar(app, variable=progress_bar_var, maximum=100)
    progress_bar.pack(pady=10, padx=10)

    current_title_label_var = tkinter.StringVar()
    current_title_label = customtkinter.CTkLabel(app, textvariable=current_title_label_var)
    current_title_label.pack(pady=10, padx=10)

    resolution_label = customtkinter.CTkLabel(app, text="Select Video resolution:")
    resolution_label.pack(pady=10, padx=10)

    resolution_menu = customtkinter.CTkOptionMenu(app, values=["480", "720", "1080", "best"])
    resolution_menu.pack(pady=10, padx=10)
    resolution_menu.set("Select")

    language_label = customtkinter.CTkLabel(app, text="Select Language to download video subtitles:")
    language_label.pack(pady=10, padx=10)

    language_menu = customtkinter.CTkOptionMenu(app, values=["en", "fr", "de", "rus"])
    language_menu.pack(pady=10, padx=10)
    language_menu.set("Select")

    download_label = customtkinter.CTkLabel(app, text="Download options:")
    download_label.pack()

    audio_button = customtkinter.CTkButton(app, text="Download Audio", command=lambda: start_download(1))
    audio_button.pack(pady=10, padx=10)

    video_button = customtkinter.CTkButton(app, text="Download Video", command=lambda: start_download(2, resolution_menu.get()))
    video_button.pack(pady=10, padx=10)

    audio_file_button = customtkinter.CTkButton(app, text="Download Audio from File", command=lambda: start_download(3))
    audio_file_button.pack(pady=10, padx=10)

    video_file_button = customtkinter.CTkButton(app, text="Download Video from File",command=lambda: start_download(4, resolution_menu.get()))
    video_file_button.pack(pady=10, padx=10)

    app.mainloop()
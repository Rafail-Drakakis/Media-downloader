from CTkMessagebox import CTkMessagebox
from tkinter import filedialog
import customtkinter
import tkinter
import yt_dlp
import os

"""
command to make an exe file using pyinstaller:
pyinstaller --name=SubtitlesDownloader --onefile --windowed --icon=icon.ico --upx-dir=/home/rafail/Documents/upx --collect-all customtkinter --collect-all CTkMessagebox --collect-all ffmpeg --hidden-import='PIL._tkinter_finder' media_downloader.py
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

    except yt_dlp.DownloadError as e:
        show_error(f"Download error: {str(e)}")
        return None
    except Exception as e:
        show_error(f"An error occurred: {str(e)}")
        return None
       
def download_subtitles(video_url, download_path):
    """
    The function `download_subtitles` downloads subtitles for a given video URL and saves them to a
    specified download path.
    
    :param video_url: The URL of the video from which you want to download subtitles
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
        info_dict = youtube_dlp_instance.extract_info(video_url, download=False)

        if 'subtitles' in info_dict and subtitles_lang in info_dict['subtitles']:
            download_path = f"{download_path}.{subtitles_lang}.vtt"
            vtt_filename = download_path

            try:
                youtube_dlp_instance.download([video_url])

                if vtt_filename and os.path.exists(vtt_filename):
                    srt_filename = vtt_filename.replace('.vtt', '.srt')
                    os.rename(vtt_filename, srt_filename)
                else:
                    show_error(f"Subtitles download failed for {subtitles_lang}.")
                show_success("Download complete")

            except yt_dlp.utils.DownloadError as e:
                show_error(f"Download error: {str(e)}")
            except yt_dlp.utils.ExtractorError as e:
                show_error(f"Extraction error: {str(e)}")
        else:
            show_error(f"No subtitles found in {subtitles_lang}.")

    except Exception as e:
        show_error(f"An error occurred: {str(e)}")

def validate_link(video_url):
    """
    The function `validate_link` checks if a given video URL is valid by using the `yt_dlp` library to
    extract information from the video.
    
    :param video_url: The video_url parameter is a string that represents the URL of a video
    :return: a boolean value. If the video URL is valid and can be extracted using the
    `yt_dlp.YoutubeDL().extract_info()` method without any download errors, then the function will
    return `True`. Otherwise, if there is a download error, the function will return `False`.
    """
    try:
        info = yt_dlp.YoutubeDL().extract_info(video_url, download=False)
        return True
    except yt_dlp.DownloadError:
        return False
    
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
    CTkMessagebox(title = "Success", message=output, icon="check", option_1="Thanks")

def get_directory(url):
    title, video_url = get_link_info(url)
    download_path = filedialog.askdirectory()
    
    if not download_path:
        show_error("Select a save location")
        return
    else:
        download_path = os.path.join(download_path, f"{title}")
        download_subtitles(video_url, download_path)

def start_download():
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
    
    if url.startswith("https://www.youtube.com/watch?"):    
        if validate_link(url):          
            get_directory(url)
        else:
            show_error("Invalid link")
    else:
        get_directory(url)


if __name__ == "__main__":
    app = customtkinter.CTk() 
    app.title("Subtitles downloader")

    # Set the window size
    window_width = 400
    window_height = 300

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

    language_label = customtkinter.CTkLabel(app, text="Select Language to download video subtitles:")
    language_label.pack(pady=10, padx=10)

    language_menu = customtkinter.CTkOptionMenu(app, values=["en", "fr", "de", "rus"])
    language_menu.pack(pady=10, padx=10)
    language_menu.set("Select")

    audio_button = customtkinter.CTkButton(app, text="Download", command=lambda: start_download())
    audio_button.pack(pady=10, padx=10)

    app.mainloop()
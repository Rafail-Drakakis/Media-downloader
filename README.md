Media Downloader

Description
A simple and user-friendly tool to download media from YouTube. It allows users to input a search query or a direct YouTube link, fetches the video's information, and downloads the media.

Installation and usage
- On linux and Mac OS:
1. Ensure you have Python 3.9 or above installed on your machine.
2. Clone this repository or download the source code.
3. Navigate to the directory containing `media_downloader.py`.
4. Install the required dependencies using the command: `pip install -r requirements.txt`

Run the program using the following command: 
```
python media_downloader.py
```
Follow the on-screen instructions to search and download your desired media.

- On windows:

1. Download as ffmpeg, the folder from this link. https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z and save it in the C directory preferably as "ffmpeg".
2. Right-click on the Start Button

On Windows 10 (Also Windows 8.1)
3. Select “System” from the context menu.
4. Click “Advanced system settings”
5. Go to the “Advanced” tab
6. Click “Environment Variables…”
7. Click variable called “Path” and click “Edit…”
8. Click “New”
9. Enter the path to the folder containing the binary you want on your PATH. For example, to add ffmpeg, add:
C:\ffmpeg\bin (assuming you have saved the file in the C directory)
10. Click “OK” to save the changes to your variables and restart your computer for the changes to take effect.

On windows 11
3.Open the Setting
4.Under System, click on "About".
5.Click on "Advanced system settings".
6.Click "Environment Variables...".
7.The environment variables panel shows up on the screen. ...
8. Click “New”
9. Enter the path to the folder containing the binary you want on your PATH. For example, to add ffmpeg, add:
C:\ffmpeg\bin (assuming you have saved the file in the C directory)
10. Click “OK” to save the changes to your variables and restart your computer for the changes to take effect.

Dependencies
- tkinter
- customtkinter
- yt_dlp
- CTkMessagebox

License
This software is released under the MIT licence. For more details, refer to the LICENSE file in the repository.
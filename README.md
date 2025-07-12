# Media Downloader

A simple, user-friendly tool for downloading media from YouTube.  
Users can input a search query or a direct YouTube link, view video details, and download the media.

---

## Features

- Search YouTube or paste direct links  
- Preview video information before downloading  
- Simple, cross-platform usage (Windows, macOS, Linux)

---

## Installation & Usage

### Linux / macOS

1. Make sure you have **Python 3.9+** installed.
2. Clone this repository or download the source code.
3. Open a terminal and navigate to the directory containing `media_downloader.py`.
4. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Run the application:

   ```bash
   python media_downloader.py
   ```

6. Follow the on-screen instructions to search and download media.

---

### Windows Setup

1. Download the **ffmpeg** build from:  
   https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z  
2. Extract the folder and save it (preferably to `C:\ffmpeg`).

#### Add ffmpeg to System PATH

##### Windows 10 / Windows 8.1

1. Right-click the Start button and select **System**.
2. Click **Advanced system settings**.
3. Go to the **Advanced** tab and click **Environment Variables...**.
4. Select the variable named **Path** and click **Edit...**.
5. Click **New** and enter:

   ```
   C:\ffmpeg\bin
   ```

6. Click **OK** to save changes and **restart your computer**.

##### Windows 11

1. Open **Settings** → **System** → **About**.
2. Click **Advanced system settings**.
3. Click **Environment Variables...**.
4. Select the **Path** variable and click **Edit...**.
5. Click **New** and enter:

   ```
   C:\ffmpeg\bin
   ```

6. Click **OK** and **restart your computer**.

---

## Dependencies

The following Python packages are required:

- `tkinter`
- `customtkinter`
- `yt_dlp`
- `CTkMessagebox`

Install them via:

```bash
pip install -r requirements.txt
```

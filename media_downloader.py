import sys
import os
import re
from datetime import timedelta

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QComboBox, QCheckBox, QProgressBar, QTextEdit,
    QGroupBox, QFormLayout, QMessageBox
)

# yt-dlp is the engine under the hood
import yt_dlp


# --------------------------
# Utilities
# --------------------------
def human_readable_size(num):
    if num is None:
        return "—"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return f"{num:3.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"


def format_eta(seconds):
    if seconds is None:
        return "—"
    try:
        return str(timedelta(seconds=int(seconds)))
    except Exception:
        return "—"


def sanitize_template(s):
    """
    Minimal guard so users don't accidentally create invalid templates on Windows.
    """
    return re.sub(r'[<>:"/\\|?*]+', '_', s)


# --------------------------
# Worker Thread
# --------------------------
class DownloadWorker(QThread):
    progress = pyqtSignal(dict)      # emits progress dict from yt-dlp (plus our extras)
    started_single = pyqtSignal(str) # each file start (filename or title)
    finished_single = pyqtSignal(str)
    log = pyqtSignal(str)
    done = pyqtSignal(bool, str)     # (ok, message)

    def __init__(self, url, mode, video_quality, audio_format, audio_bitrate,
                 out_dir, out_tpl, download_playlist, ffmpeg_location=None, parent=None):
        super().__init__(parent)
        self.url = url.strip()
        self.mode = mode  # "video" or "audio"
        self.video_quality = video_quality  # e.g., "best", "1080p", etc.
        self.audio_format = audio_format    # "mp3", "m4a", "opus"
        self.audio_bitrate = audio_bitrate  # e.g., "320k", "192k"
        self.out_dir = out_dir
        self.out_tpl = out_tpl
        self.download_playlist = download_playlist
        self.ffmpeg_location = ffmpeg_location
        self._cancel = False

    def cancel(self):
        self._cancel = True

    # ------------- yt-dlp config builders -------------
    def _build_format_string(self):
        if self.mode == "audio":
            # just best audio; extraction handled via postprocessor
            return "bestaudio/best"
        # video:
        if self.video_quality == "best":
            return "bestvideo*+bestaudio/best"
        # Restrict by height but keep best available <= target
        height = self.video_quality.replace("p", "")
        return f"(bestvideo[height<={height}]/best[height<={height}])+bestaudio/best[height<={height}]"

    def _postprocessors(self):
        if self.mode == "audio":
            return [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": self.audio_format,
                "preferredquality": self.audio_bitrate.replace("k", ""),
            }]
        else:
            # merge video+audio when needed
            return [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}]

    def _progress_hook(self, d):
        # Cancellation: raising an exception from hook stops download.
        if self._cancel:
            raise yt_dlp.utils.DownloadCancelled("User cancelled")

        status = d.get("status")
        payload = {
            "status": status,
            "downloaded_bytes": d.get("downloaded_bytes"),
            "total_bytes": d.get("total_bytes") or d.get("total_bytes_estimate"),
            "speed": d.get("speed"),
            "eta": d.get("eta"),
            "filename": d.get("filename") or d.get("info_dict", {}).get("title"),
        }

        # Tell the UI when each file starts/finishes (works for playlists too)
        if status == "downloading" and d.get("tmpfilename"):
            self.started_single.emit(os.path.basename(d.get("tmpfilename")))
        if status == "finished" and d.get("filename"):
            self.finished_single.emit(os.path.basename(d.get("filename")))

        self.progress.emit(payload)

    def run(self):
        # Ensure output dir exists
        os.makedirs(self.out_dir, exist_ok=True)

        outtmpl = os.path.join(self.out_dir, sanitize_template(self.out_tpl))

        # Build ydl options
        ydl_opts = {
            "format": self._build_format_string(),
            "outtmpl": outtmpl,
            "noplaylist": not self.download_playlist,
            "ignoreerrors": True,        # continue playlist on errors
            "progress_hooks": [self._progress_hook],
            "concurrent_fragment_downloads": 4,  # speedup on DASH/HLS
            "merge_output_format": "mp4",        # typical container
            "postprocessors": self._postprocessors(),
            "windowsfilenames": True,
            "quiet": True,
            "no_warnings": True,
            # retries in flaky networks
            "retries": 5,
            "fragment_retries": 5,
        }

        if self.mode == "audio":
            # keep audio filenames tidy
            ydl_opts["preferredquality"] = self.audio_bitrate.replace("k", "")
        if self.ffmpeg_location:
            ydl_opts["ffmpeg_location"] = self.ffmpeg_location

        try:
            self.log.emit("Preparing download…")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                if info is None:
                    raise RuntimeError("Could not extract info. Check the URL.")
                title = info.get("title") or "Unknown title"
                entries = info.get("entries")
                if entries:
                    self.log.emit(f"Playlist detected: {info.get('title','playlist')} — {len(list(entries))} items.")
                else:
                    self.log.emit(f"Video: {title}")

                # Perform download
                ydl.download([self.url])

            if self._cancel:
                self.done.emit(False, "Download cancelled.")
            else:
                self.done.emit(True, "All downloads completed.")
        except yt_dlp.utils.DownloadCancelled as e:
            self.done.emit(False, str(e))
        except Exception as e:
            self.done.emit(False, f"Error: {e}")


# --------------------------
# UI
# --------------------------
class DownloaderUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media downloader")
        self.setMinimumWidth(720)
        self.worker = None

        main = QVBoxLayout(self)

        # URL + playlist toggle
        url_group = QGroupBox("Source")
        url_form = QFormLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Paste a video or playlist URL… (YouTube, Vimeo, etc.)")
        self.playlist_chk = QCheckBox("Download entire playlist (if URL is a playlist)")
        url_form.addRow("URL:", self.url_edit)
        url_form.addRow("", self.playlist_chk)
        url_group.setLayout(url_form)

        # Mode & quality
        fmt_group = QGroupBox("Format")
        fmt_form = QFormLayout()

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Video", "Audio"])

        self.video_quality_combo = QComboBox()
        self.video_quality_combo.addItems(["best", "1080p", "720p", "480p"])
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(["mp3", "m4a", "opus"])
        self.audio_bitrate_combo = QComboBox()
        self.audio_bitrate_combo.addItems(["320k", "256k", "192k", "160k", "128k"])

        fmt_form.addRow("Mode:", self.mode_combo)
        fmt_form.addRow("Video quality:", self.video_quality_combo)
        fmt_form.addRow("Audio format:", self.audio_format_combo)
        fmt_form.addRow("Audio bitrate:", self.audio_bitrate_combo)
        fmt_group.setLayout(fmt_form)

        # Output options
        out_group = QGroupBox("Output")
        out_form = QFormLayout()
        self.dir_edit = QLineEdit(os.path.join(os.path.expanduser("~"), "Downloads"))
        self.dir_btn = QPushButton("Browse…")
        dir_row = QHBoxLayout()
        dir_row.addWidget(self.dir_edit, 1)
        dir_row.addWidget(self.dir_btn, 0)

        self.template_edit = QLineEdit("%(title)s [%(id)s].%(ext)s")
        self.template_edit.setToolTip("yt-dlp template. Examples:\n%(title)s.%(ext)s\n%(playlist_index)02d - %(title)s.%(ext)s\n%(uploader)s/%(title)s.%(ext)s")

        self.ffmpeg_edit = QLineEdit()
        self.ffmpeg_edit.setPlaceholderText("Optional: path to FFmpeg (leave empty if in PATH)")

        out_form.addRow("Save to:", QWidget())
        out_form.itemAt(out_form.rowCount()-1, QFormLayout.FieldRole).widget().setLayout(dir_row)
        out_form.addRow("Filename template:", self.template_edit)
        out_form.addRow("FFmpeg location:", self.ffmpeg_edit)
        out_group.setLayout(out_form)

        # Controls
        ctrl_row = QHBoxLayout()
        self.download_btn = QPushButton("Download")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        ctrl_row.addWidget(self.download_btn)
        ctrl_row.addWidget(self.cancel_btn)

        # Progress + log
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.speed_label = QLabel("Speed: —")
        self.eta_label = QLabel("ETA: —")
        se_row = QHBoxLayout()
        se_row.addWidget(self.speed_label)
        se_row.addSpacing(12)
        se_row.addWidget(self.eta_label)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(160)

        # Assemble
        main.addWidget(url_group)
        main.addWidget(fmt_group)
        main.addWidget(out_group)
        main.addLayout(ctrl_row)
        main.addWidget(self.progress)
        main.addLayout(se_row)
        main.addWidget(self.log)

        # Hook up
        self.mode_combo.currentTextChanged.connect(self._toggle_mode_fields)
        self._toggle_mode_fields(self.mode_combo.currentText())
        self.dir_btn.clicked.connect(self._choose_dir)
        self.download_btn.clicked.connect(self._start_download)
        self.cancel_btn.clicked.connect(self._cancel_download)

    def _toggle_mode_fields(self, mode_text):
        is_video = (mode_text.lower() == "video")
        self.video_quality_combo.setEnabled(is_video)
        self.audio_format_combo.setEnabled(not is_video)
        self.audio_bitrate_combo.setEnabled(not is_video)

    def _choose_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Choose Download Folder", self.dir_edit.text())
        if d:
            self.dir_edit.setText(d)

    def _start_download(self):
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Missing URL", "Please paste a video or playlist URL.")
            return

        mode = "video" if self.mode_combo.currentText().lower() == "video" else "audio"
        video_quality = self.video_quality_combo.currentText()
        audio_format = self.audio_format_combo.currentText()
        audio_bitrate = self.audio_bitrate_combo.currentText()
        out_dir = self.dir_edit.text().strip()
        out_tpl = self.template_edit.text().strip() or "%(title)s [%(id)s].%(ext)s"
        playlist = self.playlist_chk.isChecked()
        ffmpeg_location = self.ffmpeg_edit.text().strip() or None

        # Reset UI
        self.progress.setValue(0)
        self.speed_label.setText("Speed: —")
        self.eta_label.setText("ETA: —")
        self.log.clear()

        self.worker = DownloadWorker(
            url=url,
            mode=mode,
            video_quality=video_quality,
            audio_format=audio_format,
            audio_bitrate=audio_bitrate,
            out_dir=out_dir,
            out_tpl=out_tpl,
            download_playlist=playlist,
            ffmpeg_location=ffmpeg_location
        )

        self.worker.progress.connect(self._on_progress)
        self.worker.log.connect(self._append_log)
        self.worker.started_single.connect(lambda name: self._append_log(f"Starting: {name}"))
        self.worker.finished_single.connect(lambda name: self._append_log(f"Finished: {name}"))
        self.worker.done.connect(self._on_done)

        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

        self.worker.start()

    def _cancel_download(self):
        if self.worker:
            self.worker.cancel()
            self._append_log("Cancelling…")

    def _on_progress(self, d):
        total = d.get("total_bytes")
        downloaded = d.get("downloaded_bytes") or 0
        status = d.get("status")

        if total and total > 0:
            pct = int(downloaded * 100 / total)
            self.progress.setValue(max(0, min(100, pct)))
        elif status == "finished":
            self.progress.setValue(100)

        self.speed_label.setText(f"Speed: {human_readable_size(d.get('speed'))}/s")
        self.eta_label.setText(f"ETA: {format_eta(d.get('eta'))}")

        # Keep a tidy one-liner status
        if status == "downloading":
            self._status_line(downloaded, total, d.get("filename"))
        elif status == "finished":
            self._append_log("Post-processing / merge finished.")

    def _status_line(self, downloaded, total, name):
        if total:
            msg = f"Downloading {os.path.basename(str(name))} — {human_readable_size(downloaded)} / {human_readable_size(total)}"
        else:
            msg = f"Downloading {os.path.basename(str(name))} — {human_readable_size(downloaded)}"
        self._append_log(msg, transient=True)

    def _append_log(self, text, transient=False):
        if transient:
            # replace last line if it's a transient status to avoid flooding
            cursor = self.log.textCursor()
            cursor.movePosition(cursor.End)
            cursor.select(cursor.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deletePreviousChar()  # remove newline if present
            self.log.append(text)
        else:
            self.log.append(text)

    def _on_done(self, ok, message):
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.worker = None
        if ok:
            self.progress.setValue(100)
        self._append_log(message)
        if ok:
            QMessageBox.information(self, "Completed", message)
        else:
            QMessageBox.warning(self, "Stopped", message)


def main():
    app = QApplication(sys.argv)
    ui = DownloaderUI()
    ui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

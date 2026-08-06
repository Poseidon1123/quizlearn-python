import asyncio
import hashlib
import threading
from pathlib import Path

import edge_tts
from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


class PronunciationService(QObject):
    """Tải phát âm tiếng Anh bằng edge-tts, lưu cache và phát bằng Qt."""

    started = Signal(str)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        cache_dir: str | Path,
        voice: str = "en-US-AriaNeural",
        parent=None,
    ):
        super().__init__(parent)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.voice = voice

        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(1.0)

        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)

        self._active_requests: set[str] = set()
        self._lock = threading.Lock()

    def speak(self, text: str) -> None:
        value = " ".join(text.strip().split())
        if not value:
            self.failed.emit("Không có nội dung để phát âm.")
            return

        audio_path = self._cache_path(value)
        if audio_path.exists() and audio_path.stat().st_size > 0:
            self._play(audio_path)
            return

        request_key = str(audio_path)
        with self._lock:
            if request_key in self._active_requests:
                return
            self._active_requests.add(request_key)

        self.started.emit(value)
        thread = threading.Thread(
            target=self._download_worker,
            args=(value, audio_path, request_key),
            daemon=True,
        )
        thread.start()

    def _cache_path(self, text: str) -> Path:
        digest = hashlib.sha256(
            f"{self.voice}\0{text}".encode("utf-8")
        ).hexdigest()
        return self.cache_dir / f"{digest}.mp3"

    def _download_worker(
        self,
        text: str,
        audio_path: Path,
        request_key: str,
    ) -> None:
        temporary_path = audio_path.with_suffix(".tmp.mp3")
        try:
            asyncio.run(
                edge_tts.Communicate(
                    text=text,
                    voice=self.voice,
                ).save(str(temporary_path))
            )
            temporary_path.replace(audio_path)
            self.finished.emit(str(audio_path))
        except Exception as error:
            temporary_path.unlink(missing_ok=True)
            self.failed.emit(
                "Không thể tải phát âm. Hãy kiểm tra Internet.\n\n"
                f"{error}"
            )
        finally:
            with self._lock:
                self._active_requests.discard(request_key)

    def _play(self, audio_path: Path) -> None:
        self.player.stop()
        self.player.setSource(
            QUrl.fromLocalFile(str(audio_path.resolve()))
        )
        self.player.play()

    def play_downloaded_file(self, audio_path: str) -> None:
        self._play(Path(audio_path))

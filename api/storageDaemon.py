import subprocess
import os
import shlex
import time
import sys
import threading
from distutils.command.check import check
from pathlib import Path
from typing import Optional



class TonStorageDaemon:
    def __init__(self, daemon_path: str):
        self.daemon_path = Path(daemon_path).expanduser()
        if not self.daemon_path.exists():
            raise FileNotFoundError(f"Daemon not found at {self.daemon_path}")

    def _stream_output(self, pipe, prefix):
        for line in pipe:
            print(f"{prefix}{line.strip()}", flush=True)

    def start(self, config_path: str, ip: str, port: str, db_path: str):
        db_path = Path(db_path).expanduser()
        db_path.mkdir(parents=True, exist_ok=True)

        command = [
            str(self.daemon_path),
            "-v", "3",
            "-C", str(Path(config_path).absolute()),
            "-I", ip,
            "-p", port,
            "-D", str(db_path)
        ]

        print(f"Storage daemon startup: {' '.join(command)}")

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Построчная буферизация
            universal_newlines=True
        )

        # Запускаем потоки для чтения вывода
        threading.Thread(
            target=self._stream_output,
            args=(process.stdout, "[OUT] "),
            daemon=True
        ).start()

        threading.Thread(
            target=self._stream_output,
            args=(process.stderr, "[ERR] "),
            daemon=True
        ).start()

        return process


if __name__ == "__main__":
    try:
        daemon = TonStorageDaemon(
            daemon_path="/Users/gtsk/Downloads/storage-daemon-mac-arm64"
        )
        process = daemon.start(
            config_path="/Users/gtsk/Downloads/testnet-global.config.json",
            ip="127.0.0.1:3333",
            port="5555",
            db_path="~/ton-storage-db-testnet"
        )

        print(f"🔄 storage daemon startup successfully (PID: {process.pid}). press Ctrl+C for stop.")
        process.wait()  # Ожидаем завершения (для демона это "вечно")

    except KeyboardInterrupt:
        print("\n🛑 stopping storage daemon...")
        process.terminate()
    except Exception as e:
        print(f"❌ error: {e}", file=sys.stderr)
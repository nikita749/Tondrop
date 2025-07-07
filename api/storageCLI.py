import subprocess
import os
import shlex
import time
import sys
import threading
from distutils.command.check import check
from pathlib import Path
from typing import Optional



class TonStorageCLI:
    def __init__(self, cli_path: str = "~/Downloads/storage-daemon-cli-mac-arm64"):
        self.cli_path = Path(cli_path).expanduser()
        if not self.cli_path.exists():
            raise FileNotFoundError(f"TON Storage CLI not found at {self.cli_path}")

    def _stream_output(self, pipe, prefix):
        for line in pipe:
            print(f"{prefix}{line.strip()}", flush=True)

    def upload(self, file_path: str) -> str:
        file_path = Path(file_path).absolute()
        if not file_path.exists():
            raise FileNotFoundError(f"file {file_path} not found")

        cmd = f"./{self.cli_path} upload {file_path}"
        result = subprocess.run(
            shlex.split(cmd),
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Upload failed: {result.stderr.strip()}")
        return result.stdout.strip()

    def download(self, bag_id: str, output_dir: str = ".") -> str:
        output_dir = Path(output_dir).absolute()
        output_dir.mkdir(exist_ok=True)

        cmd = f"./{self.cli_path} download {bag_id} {output_dir}"
        subprocess.run(
            shlex.split(cmd),
            check=True,
            capture_output=True
        )
        return str(output_dir / bag_id)

    def listFiles(self) -> list:
        cmd = f"./{self.cli_path} list"
        result = subprocess.run(
            shlex.split(cmd),
            capture_output=True,
            text=True
        )
        return result.stdout.splitlines()

    def delete(self, bag_id: str) -> bool:
        cmd = f"./{self.cli_path} delete {bag_id}"
        result = subprocess.run(
            shlex.split(cmd),
            capture_output=True
        )
        return result.returncode == 0


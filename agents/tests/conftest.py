from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections.abc import Generator
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REPO_ROOT = Path(__file__).resolve().parents[2]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="session")
def go_api_base_url(
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[str, None, None]:
    port = _free_port()
    db_dir = tmp_path_factory.mktemp("go_api_contract")
    db_path = db_dir / "contract.db"

    env = os.environ.copy()
    env["API_PORT"] = str(port)
    env["DB_DSN"] = f"file:{db_path}?_busy_timeout=5000&_journal_mode=WAL"

    proc = subprocess.Popen(
        ["go", "run", "./cmd/api"],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    base_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 30
    while time.time() < deadline:
        if proc.poll() is not None:
            out, err = proc.communicate(timeout=2)
            raise RuntimeError(f"go api exited early\nstdout:\n{out}\nstderr:\n{err}")
        try:
            resp = requests.get(f"{base_url}/health", timeout=1)
            if resp.status_code == 200:
                break
        except requests.RequestException:
            time.sleep(0.25)
    else:
        proc.terminate()
        out, err = proc.communicate(timeout=3)
        raise RuntimeError(
            f"go api did not become healthy\nstdout:\n{out}\nstderr:\n{err}"
        )

    try:
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture(scope="session")
def agent_api_base_url(
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[str, None, None]:
    port = _free_port()
    db_dir = tmp_path_factory.mktemp("agent_api_contract")
    db_path = db_dir / "adversarial.db"

    env = os.environ.copy()
    env["ADVERSARIAL_DB_PATH"] = str(db_path)
    env["AGENT_ALLOWED_ORIGINS"] = "http://localhost:5173,http://127.0.0.1:5173"

    proc = subprocess.Popen(
        [
            str(REPO_ROOT / ".venv" / "bin" / "python"),
            "-m",
            "uvicorn",
            "app.main:app",
            "--port",
            str(port),
            "--app-dir",
            "agents",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    base_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 30
    while time.time() < deadline:
        if proc.poll() is not None:
            out, err = proc.communicate(timeout=2)
            raise RuntimeError(
                f"agents api exited early\nstdout:\n{out}\nstderr:\n{err}"
            )
        try:
            resp = requests.get(f"{base_url}/health", timeout=1)
            if resp.status_code == 200:
                break
        except requests.RequestException:
            time.sleep(0.25)
    else:
        proc.terminate()
        out, err = proc.communicate(timeout=3)
        raise RuntimeError(
            f"agents api did not become healthy\nstdout:\n{out}\nstderr:\n{err}"
        )

    try:
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

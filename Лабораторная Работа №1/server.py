#!/usr/bin/env python3
"""
Файловый сервер: LIST, UPLOAD, DOWNLOAD, EXIT.
Протокол: строки UTF-8, завершающиеся \\n; тело файла — сырые байты после заголовка с размером.
"""

from __future__ import annotations

import argparse
import os
import re
import socket
import threading
from typing import Optional, Tuple

LINE_MAX = 4096
CHUNK = 65536


def safe_basename(name: str) -> Optional[str]:
    """Имя файла только в каталоге хранения, без path traversal."""
    base = os.path.basename(name.replace("\\", "/"))
    if not base or base in (".", ".."):
        return None
    if ".." in name.replace("\\", "/"):
        return None
    return base


def recv_line(conn: socket.socket) -> str:
    buf = bytearray()
    while True:
        if len(buf) > LINE_MAX:
            raise ValueError("строка слишком длинная")
        b = conn.recv(1)
        if not b:
            raise ConnectionError("соединение закрыто")
        buf.extend(b)
        if buf.endswith(b"\n"):
            return buf[:-1].decode("utf-8", errors="strict").rstrip("\r")


def recv_exact(conn: socket.socket, n: int) -> bytes:
    parts: list[bytes] = []
    got = 0
    while got < n:
        chunk = conn.recv(min(CHUNK, n - got))
        if not chunk:
            raise ConnectionError("обрыв при приёме данных")
        parts.append(chunk)
        got += len(chunk)
    return b"".join(parts)


def send_line(conn: socket.socket, text: str) -> None:
    conn.sendall((text + "\n").encode("utf-8"))


def handle_list(conn: socket.socket, storage: str) -> None:
    try:
        names = sorted(
            f for f in os.listdir(storage) if os.path.isfile(os.path.join(storage, f))
        )
    except OSError as e:
        send_line(conn, f"ERROR list: {e}")
        return
    send_line(conn, "OK")
    send_line(conn, str(len(names)))
    for n in names:
        send_line(conn, n)


def handle_upload(conn: socket.socket, storage: str, remote_name: str) -> None:
    base = safe_basename(remote_name)
    if not base:
        send_line(conn, "ERROR некорректное имя файла")
        return
    send_line(conn, "READY")
    try:
        size_s = recv_line(conn)
    except (ConnectionError, ValueError) as e:
        raise ConnectionError(str(e)) from e
    if not re.fullmatch(r"-?\d+", size_s):
        send_line(conn, "ERROR некорректный размер")
        return
    size = int(size_s)
    if size < 0:
        send_line(conn, "ERROR отрицательный размер")
        return
    path = os.path.join(storage, base)
    try:
        data = recv_exact(conn, size)
    except ConnectionError:
        send_line(conn, "ERROR обрыв передачи")
        raise
    try:
        with open(path, "wb") as f:
            f.write(data)
    except OSError as e:
        send_line(conn, f"ERROR запись: {e}")
        return
    send_line(conn, "OK")


def handle_download(conn: socket.socket, storage: str, remote_name: str) -> None:
    base = safe_basename(remote_name)
    if not base:
        send_line(conn, "ERROR некорректное имя файла")
        return
    path = os.path.join(storage, base)
    if not os.path.isfile(path):
        send_line(conn, "ERROR файл не найден")
        return
    try:
        size = os.path.getsize(path)
    except OSError as e:
        send_line(conn, f"ERROR {e}")
        return
    send_line(conn, f"OK {size}")
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(CHUNK)
                if not chunk:
                    break
                conn.sendall(chunk)
    except OSError:
        # заголовок уже ушёл — клиент может получить обрыв; сервер не падает
        pass


def handle_client(conn: socket.socket, addr: Tuple[str, int], storage: str) -> None:
    peer = f"{addr[0]}:{addr[1]}"
    try:
        while True:
            try:
                line = recv_line(conn)
            except ConnectionError:
                break
            except ValueError as e:
                try:
                    send_line(conn, f"ERROR {e}")
                except OSError:
                    pass
                break
            if not line:
                continue
            parts = line.split(maxsplit=1)
            cmd = parts[0].upper()
            arg = parts[1] if len(parts) > 1 else ""

            try:
                if cmd == "LIST":
                    if arg:
                        send_line(conn, "ERROR команда LIST не принимает аргументы")
                        continue
                    handle_list(conn, storage)
                elif cmd == "UPLOAD":
                    if not arg.strip():
                        send_line(conn, "ERROR укажите имя файла: UPLOAD <filename>")
                        continue
                    handle_upload(conn, storage, arg.strip())
                elif cmd == "DOWNLOAD":
                    if not arg.strip():
                        send_line(conn, "ERROR укажите имя файла: DOWNLOAD <filename>")
                        continue
                    handle_download(conn, storage, arg.strip())
                elif cmd == "EXIT":
                    send_line(conn, "BYE")
                    break
                else:
                    send_line(conn, "ERROR неизвестная команда")
            except ConnectionError:
                break
            except Exception as e:
                try:
                    send_line(conn, f"ERROR внутренняя: {e}")
                except OSError:
                    pass
    finally:
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        conn.close()


def ensure_storage(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def serve(host: str, port: int, storage: str) -> None:
    ensure_storage(storage)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((host, port))
        sock.listen(8)
        print(f"Сервер слушает {host}:{port}, каталог: {os.path.abspath(storage)}")
        while True:
            conn, addr = sock.accept()
            t = threading.Thread(
                target=handle_client, args=(conn, addr, storage), daemon=True
            )
            t.start()
    except KeyboardInterrupt:
        print("\nОстановка сервера.")
    finally:
        sock.close()


def main() -> None:
    p = argparse.ArgumentParser(description="Файловый TCP-сервер")
    p.add_argument("--host", default="0.0.0.0", help="адрес привязки")
    p.add_argument("--port", type=int, default=9000, help="порт")
    p.add_argument(
        "--storage",
        default="server_storage",
        help="каталог хранения файлов на сервере",
    )
    args = p.parse_args()
    serve(args.host, args.port, args.storage)


if __name__ == "__main__":
    main()

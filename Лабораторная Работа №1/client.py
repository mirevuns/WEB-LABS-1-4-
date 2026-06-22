#!/usr/bin/env python3
"""
Клиент файлового сервера: интерактивные команды LIST, UPLOAD, DOWNLOAD, EXIT.
"""

from __future__ import annotations

import argparse
import os
import re
import socket
import sys
from typing import Optional

LINE_MAX = 4096
CHUNK = 65536


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


def cmd_list(conn: socket.socket) -> None:
    send_line(conn, "LIST")
    line = recv_line(conn)
    if line.startswith("ERROR"):
        print(line)
        return
    if line != "OK":
        print(f"Неожиданный ответ: {line}")
        return
    n_s = recv_line(conn)
    if not re.fullmatch(r"\d+", n_s):
        print(f"Некорректное число файлов: {n_s}")
        return
    n = int(n_s)
    for _ in range(n):
        print(recv_line(conn))


def cmd_upload(conn: socket.socket, local_path: str) -> None:
    local_path = local_path.strip().strip('"')
    if not local_path:
        print("Укажите путь к файлу.")
        return
    if not os.path.isfile(local_path):
        print("Локальный файл не найден.")
        return
    server_name = os.path.basename(local_path.replace("\\", "/"))
    try:
        size = os.path.getsize(local_path)
    except OSError as e:
        print(f"Ошибка доступа к файлу: {e}")
        return

    send_line(conn, f"UPLOAD {server_name}")
    line = recv_line(conn)
    if line.startswith("ERROR"):
        print(line)
        return
    if line != "READY":
        print(f"Неожиданный ответ: {line}")
        return

    send_line(conn, str(size))
    try:
        with open(local_path, "rb") as f:
            sent = 0
            while sent < size:
                chunk = f.read(CHUNK)
                if not chunk:
                    break
                conn.sendall(chunk)
                sent += len(chunk)
    except OSError as e:
        print(f"Ошибка чтения: {e}")
        return
    except BrokenPipeError:
        print("Соединение разорвано при отправке.")
        return

    resp = recv_line(conn)
    print(resp if resp == "OK" else resp)


def cmd_download(conn: socket.socket, remote_name: str, local_path: Optional[str]) -> None:
    remote_name = remote_name.strip().strip('"')
    if not remote_name:
        print("Укажите имя файла на сервере.")
        return
    base = os.path.basename(remote_name.replace("\\", "/"))
    if local_path:
        out = local_path.strip().strip('"')
    else:
        out = base
    if not out:
        print("Некорректный путь сохранения.")
        return

    send_line(conn, f"DOWNLOAD {base}")
    line = recv_line(conn)
    if line.startswith("ERROR"):
        print(line)
        return
    m = re.fullmatch(r"OK (\d+)", line)
    if not m:
        print(f"Неожиданный ответ: {line}")
        return
    size = int(m.group(1))
    try:
        data = recv_exact(conn, size)
    except ConnectionError as e:
        print(str(e))
        return
    try:
        with open(out, "wb") as f:
            f.write(data)
    except OSError as e:
        print(f"Ошибка записи: {e}")
        return
    print(f"Сохранено: {os.path.abspath(out)} ({size} байт)")


def cmd_exit(conn: socket.socket) -> bool:
    send_line(conn, "EXIT")
    try:
        line = recv_line(conn)
        print(line)
    except ConnectionError:
        pass
    return True


def print_help() -> None:
    print(
        "Команды:\n"
        "  LIST\n"
        "  UPLOAD <локальный_путь_к_файлу>\n"
        "  DOWNLOAD <имя_на_сервере> [локальный_путь_сохранения]\n"
        "  EXIT\n"
        "  HELP"
    )


def repl(host: str, port: int) -> None:
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        conn.connect((host, port))
    except OSError as e:
        print(f"Не удалось подключиться: {e}")
        return

    print(f"Подключено к {host}:{port}. Введите HELP для списка команд.")
    done = False
    try:
        while not done:
            try:
                raw = input("> ").strip()
            except EOFError:
                print()
                break
            if not raw:
                continue
            tokens = raw.split(None, 1)
            cmd = tokens[0].upper()
            try:
                if cmd == "HELP":
                    print_help()
                elif cmd == "LIST":
                    cmd_list(conn)
                elif cmd == "UPLOAD":
                    if len(tokens) < 2:
                        print("Использование: UPLOAD <путь>")
                        continue
                    cmd_upload(conn, tokens[1])
                elif cmd == "DOWNLOAD":
                    dl = raw.split(None, 2)
                    if len(dl) < 2:
                        print("Использование: DOWNLOAD <имя> [куда_сохранить]")
                        continue
                    local = dl[2] if len(dl) > 2 else None
                    cmd_download(conn, dl[1], local)
                elif cmd == "EXIT":
                    done = cmd_exit(conn)
                else:
                    print("Неизвестная команда. Введите HELP.")
            except ConnectionError as e:
                print(f"Соединение потеряно: {e}")
                break
            except BrokenPipeError:
                print("Соединение разорвано.")
                break
    finally:
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        conn.close()


def main() -> None:
    p = argparse.ArgumentParser(description="Клиент файлового TCP-сервера")
    p.add_argument("--host", default="127.0.0.1", help="IP сервера")
    p.add_argument("--port", type=int, default=9000, help="порт")
    args = p.parse_args()
    repl(args.host, args.port)


if __name__ == "__main__":
    main()

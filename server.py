"""Local server and durable storage for LYMEC Gender Watch."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import shutil
import threading
import webbrowser
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
ARCHIVE_DIR = DATA_DIR / "archive"
RECORDS_FILE = DATA_DIR / "records.json"
CSV_FILE = DATA_DIR / "current-session.csv"
HOST = "127.0.0.1"
PORT = 8765
MAX_BODY_BYTES = 10 * 1024 * 1024
MAX_RECORDS = 100_000

STATIC_FILES = {
    "/": (ROOT / "index.html", "text/html; charset=utf-8"),
    "/index.html": (ROOT / "index.html", "text/html; charset=utf-8"),
    "/styles.css": (ROOT / "styles.css", "text/css; charset=utf-8"),
    "/app.js": (ROOT / "app.js", "text/javascript; charset=utf-8"),
    "/assets/lymec-logo.webp": (ROOT / "assets" / "lymec-logo.webp", "image/webp"),
}

storage_lock = threading.Lock()


def validate_entries(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError("Entries must be a list.")
    if len(value) > MAX_RECORDS:
        raise ValueError("The session contains too many entries.")

    cleaned: list[dict[str, object]] = []
    for index, entry in enumerate(value, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"Entry {index} is invalid.")

        entry_id = entry.get("id")
        gender = entry.get("gender")
        first_time = entry.get("firstTime")
        comment = entry.get("comment", "")
        timestamp = entry.get("timestamp")

        if not isinstance(entry_id, str) or not entry_id or len(entry_id) > 200:
            raise ValueError(f"Entry {index} has an invalid ID.")
        if gender not in {"Man", "Woman", "Non-binary"}:
            raise ValueError(f"Entry {index} has an invalid gender.")
        if not isinstance(first_time, bool):
            raise ValueError(f"Entry {index} has an invalid first-time value.")
        if not isinstance(comment, str) or len(comment) > 160:
            raise ValueError(f"Entry {index} has an invalid comment.")
        if not isinstance(timestamp, str) or len(timestamp) > 50:
            raise ValueError(f"Entry {index} has an invalid timestamp.")

        try:
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError(f"Entry {index} has an invalid timestamp.") from error

        cleaned.append(
            {
                "id": entry_id,
                "gender": gender,
                "firstTime": first_time,
                "comment": comment.strip(),
                "timestamp": timestamp,
            }
        )

    return cleaned


def load_records() -> list[dict[str, object]]:
    if not RECORDS_FILE.exists():
        return []
    with RECORDS_FILE.open("r", encoding="utf-8") as file:
        return validate_entries(json.load(file))


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def csv_content(entries: list[dict[str, object]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        [
            "Entry",
            "Gender",
            "First-time delegate",
            "Comment",
            "Recorded at",
            "Date",
            "Time",
            "Record ID",
        ]
    )

    for index, entry in enumerate(entries, start=1):
        recorded_at = datetime.fromisoformat(str(entry["timestamp"]).replace("Z", "+00:00"))
        local_time = recorded_at.astimezone()
        writer.writerow(
            [
                index,
                entry["gender"],
                "Yes" if entry["firstTime"] else "No",
                entry.get("comment", ""),
                local_time.isoformat(timespec="seconds"),
                local_time.strftime("%Y-%m-%d"),
                local_time.strftime("%H:%M:%S"),
                entry["id"],
            ]
        )

    return "\ufeff" + output.getvalue()


def write_records(entries: list[dict[str, object]]) -> None:
    # JSON is the recovery source and is written first. If Excel has the CSV
    # locked, no record is lost and the CSV can catch up on the next update.
    atomic_write(RECORDS_FILE, json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
    atomic_write(CSV_FILE, csv_content(entries))


def archive_records(entries: list[dict[str, object]]) -> str:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    label = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    json_archive = ARCHIVE_DIR / f"session-{label}.json"
    csv_archive = ARCHIVE_DIR / f"session-{label}.csv"

    if RECORDS_FILE.exists():
        shutil.copy2(RECORDS_FILE, json_archive)
    else:
        atomic_write(json_archive, json.dumps(entries, ensure_ascii=False, indent=2) + "\n")

    if CSV_FILE.exists():
        shutil.copy2(CSV_FILE, csv_archive)
    else:
        atomic_write(csv_archive, csv_content(entries))

    return str(csv_archive.relative_to(ROOT))


class AppHandler(BaseHTTPRequestHandler):
    server_version = "LYMECGenderWatch/1.0"

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/records":
            self.send_records()
            return

        static_file = STATIC_FILES.get(path)
        if static_file is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        file_path, content_type = static_file
        try:
            content = file_path.read_bytes()
        except OSError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def do_PUT(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/records":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid request size."})
            return

        if content_length <= 0 or content_length > MAX_BODY_BYTES:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid request size."})
            return

        try:
            body = json.loads(self.rfile.read(content_length).decode("utf-8"))
            entries = validate_entries(body.get("entries"))
            action = body.get("action", "update")
            if action not in {"update", "record", "undo", "reset", "restore"}:
                raise ValueError("Invalid update action.")
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError, AttributeError) as error:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return

        archived_file = None
        try:
            with storage_lock:
                current_entries = load_records()
                if action == "reset" and current_entries:
                    archived_file = archive_records(current_entries)
                write_records(entries)
        except PermissionError:
            self.send_json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "error": (
                        "The Excel backup is locked. Close current-session.csv in Excel "
                        "and make one more entry or undo to retry. The JSON recovery copy is safe."
                    )
                },
            )
            return
        except (OSError, ValueError, json.JSONDecodeError) as error:
            self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Backup failed: {error}"})
            return

        response: dict[str, object] = {
            "ok": True,
            "count": len(entries),
            "backupFile": str(CSV_FILE.relative_to(ROOT)),
        }
        if archived_file:
            response["archivedFile"] = archived_file
        self.send_json(HTTPStatus.OK, response)

    def send_records(self) -> None:
        try:
            with storage_lock:
                initialized = RECORDS_FILE.exists()
                entries = load_records()
        except (OSError, ValueError, json.JSONDecodeError) as error:
            self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Could not read backup: {error}"})
            return

        self.send_json(
            HTTPStatus.OK,
            {
                "entries": entries,
                "initialized": initialized,
                "backupFile": str(CSV_FILE.relative_to(ROOT)),
            },
        )

    def send_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format_string: str, *args: object) -> None:
        print(f"[{self.log_date_time_string()}] {format_string % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LYMEC Gender Watch locally.")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the browser automatically.")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    except OSError as error:
        raise SystemExit(f"Could not start on http://{HOST}:{PORT}: {error}") from error

    url = f"http://{HOST}:{PORT}"
    print("LYMEC Gender Watch")
    print(f"App:    {url}")
    print(f"Backup: {CSV_FILE}")
    print("Close this window or press Ctrl+C to stop the app.")

    if not args.no_browser:
        threading.Timer(0.7, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping LYMEC Gender Watch...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

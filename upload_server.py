#!/usr/bin/env python3
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import cgi
import os
import re
import shutil


UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "/workspace")).resolve()
PORT = int(os.environ.get("UPLOAD_PORT", "8000"))
SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(name: str) -> str:
    base = Path(name or "upload.bin").name
    cleaned = SAFE_NAME.sub("_", base).strip("._")
    return cleaned or "upload.bin"


def package_tag(filename: str) -> str | None:
    match = re.match(r"^([A-Za-z0-9_-]+)_lora_package\.zip$", filename)
    return match.group(1) if match else None


def render_page(message: str = "") -> bytes:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(
        [p for p in UPLOAD_DIR.iterdir() if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:30]

    rows = []
    for path in files:
        size_mb = path.stat().st_size / (1024 * 1024)
        tag = package_tag(path.name)
        hint = f"<code>install_ykc_package {escape(tag)}</code>" if tag else ""
        rows.append(
            "<tr>"
            f"<td>{escape(path.name)}</td>"
            f"<td>{size_mb:.1f} MB</td>"
            f"<td>{hint}</td>"
            "</tr>"
        )

    body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Anima LoRA Upload</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 32px; color: #1f2933; }}
    main {{ max-width: 880px; margin: 0 auto; }}
    h1 {{ font-size: 28px; margin-bottom: 8px; }}
    p {{ color: #52606d; }}
    form {{ border: 1px solid #ccd5df; padding: 24px; border-radius: 8px; background: #f8fafc; }}
    input[type=file] {{ display: block; width: 100%; margin: 18px 0; }}
    button {{ padding: 10px 16px; border: 0; border-radius: 6px; background: #305cde; color: white; font-weight: 700; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 24px; }}
    th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid #d9e2ec; }}
    code {{ background: #edf2f7; padding: 2px 6px; border-radius: 4px; }}
    .message {{ background: #e6ffed; border: 1px solid #9ae6b4; padding: 12px; border-radius: 6px; color: #22543d; }}
  </style>
</head>
<body>
<main>
  <h1>Anima LoRA Upload</h1>
  <p>Uploads are saved to <code>{escape(str(UPLOAD_DIR))}</code>.</p>
  {f'<div class="message">{escape(message)}</div>' if message else ''}
  <form method="post" enctype="multipart/form-data">
    <label for="file">Choose a LoRA package zip or model file</label>
    <input id="file" name="file" type="file" required>
    <button type="submit">Upload</button>
  </form>
  <table>
    <thead><tr><th>File</th><th>Size</th><th>Next command</th></tr></thead>
    <tbody>{''.join(rows) or '<tr><td colspan="3">No files yet.</td></tr>'}</tbody>
  </table>
</main>
</body>
</html>"""
    return body.encode("utf-8")


class UploadHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        message = query.get("message", [""])[0]
        page = render_page(message)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self) -> None:
        ctype, pdict = cgi.parse_header(self.headers.get("Content-Type", ""))
        if ctype != "multipart/form-data":
            self.send_error(400, "Expected multipart/form-data")
            return

        pdict["boundary"] = bytes(pdict["boundary"], "utf-8")
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST"})
        item = form["file"] if "file" in form else None
        if item is None or not item.filename:
            self.send_error(400, "No file uploaded")
            return

        filename = safe_filename(item.filename)
        target = (UPLOAD_DIR / filename).resolve()
        if UPLOAD_DIR not in target.parents and target != UPLOAD_DIR:
            self.send_error(400, "Invalid file name")
            return

        with target.open("wb") as handle:
            shutil.copyfileobj(item.file, handle)

        self.send_response(303)
        self.send_header("Location", f"/?message=Uploaded%20{filename}")
        self.end_headers()

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} - {fmt % args}")


def main() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), UploadHandler)
    print(f"Upload server listening on 0.0.0.0:{PORT}")
    print(f"Saving files to {UPLOAD_DIR}")
    server.serve_forever()


if __name__ == "__main__":
    main()

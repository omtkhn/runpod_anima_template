#!/usr/bin/env python3
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse
import cgi
import os
import shutil


ROOT = Path(os.environ.get("FILE_MANAGER_ROOT", "/workspace")).resolve()
PORT = int(os.environ.get("FILE_MANAGER_PORT", "2999"))
TOKEN = os.environ.get("FILE_MANAGER_TOKEN", "")


def inside_root(path: Path) -> bool:
    resolved = path.resolve()
    return resolved == ROOT or ROOT in resolved.parents


def clean_rel(raw: str) -> Path:
    rel = Path(unquote(raw).lstrip("/"))
    target = (ROOT / rel).resolve()
    if not inside_root(target):
        raise ValueError("Path escapes file manager root")
    return target


def href(path: Path) -> str:
    rel = path.resolve().relative_to(ROOT).as_posix()
    return "/?path=" + quote(rel)


def download_href(path: Path) -> str:
    rel = path.resolve().relative_to(ROOT).as_posix()
    return "/download?path=" + quote(rel)


def render_directory(current: Path, message: str = "") -> bytes:
    current.mkdir(parents=True, exist_ok=True)
    rel = "." if current == ROOT else current.relative_to(ROOT).as_posix()
    parent_link = ""
    if current != ROOT:
        parent_link = f'<a class="button" href="{href(current.parent)}">Parent</a>'

    rows = []
    for item in sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        name = item.name + ("/" if item.is_dir() else "")
        size = "-" if item.is_dir() else f"{item.stat().st_size / (1024 * 1024):.1f} MB"
        action = f'<a href="{href(item)}">Open</a>' if item.is_dir() else f'<a href="{download_href(item)}">Download</a>'
        rows.append(
            "<tr>"
            f"<td>{escape(name)}</td>"
            f"<td>{size}</td>"
            f"<td>{action}</td>"
            "</tr>"
        )

    token_input = ""
    if TOKEN:
        token_input = '<label>Token <input name="token" type="password" required></label>'

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RunPod File Manager</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 28px; color: #1f2933; }}
    main {{ max-width: 980px; margin: 0 auto; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    code {{ background: #edf2f7; padding: 2px 6px; border-radius: 4px; }}
    form {{ display: flex; flex-wrap: wrap; gap: 12px; align-items: end; margin: 22px 0; padding: 18px; border: 1px solid #ccd5df; border-radius: 8px; background: #f8fafc; }}
    input[type=file] {{ min-width: 280px; }}
    button, .button {{ padding: 9px 14px; border: 0; border-radius: 6px; background: #305cde; color: white; font-weight: 700; text-decoration: none; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
    th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid #d9e2ec; }}
    .message {{ background: #e6ffed; border: 1px solid #9ae6b4; padding: 12px; border-radius: 6px; color: #22543d; }}
    .bar {{ display: flex; gap: 10px; align-items: center; margin: 12px 0; }}
  </style>
</head>
<body>
<main>
  <h1>RunPod File Manager</h1>
  <p>Root: <code>{escape(str(ROOT))}</code></p>
  <p>Current: <code>{escape(rel)}</code></p>
  {f'<div class="message">{escape(message)}</div>' if message else ''}
  <div class="bar">{parent_link}<a class="button" href="{href(ROOT)}">Workspace Root</a></div>
  <form method="post" enctype="multipart/form-data">
    <input name="path" type="hidden" value="{escape(rel if rel != "." else "")}">
    <label>Upload file <input name="file" type="file" required></label>
    {token_input}
    <button type="submit">Upload Here</button>
  </form>
  <table>
    <thead><tr><th>Name</th><th>Size</th><th>Action</th></tr></thead>
    <tbody>{''.join(rows) or '<tr><td colspan="3">Empty directory.</td></tr>'}</tbody>
  </table>
</main>
</body>
</html>"""
    return html.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        try:
            target = clean_rel(query.get("path", [""])[0])
        except ValueError as exc:
            self.send_error(400, str(exc))
            return

        if parsed.path == "/download":
            if not target.is_file():
                self.send_error(404, "File not found")
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{target.name}"')
            self.send_header("Content-Length", str(target.stat().st_size))
            self.end_headers()
            with target.open("rb") as handle:
                shutil.copyfileobj(handle, self.wfile)
            return

        if target.is_file():
            self.send_response(303)
            self.send_header("Location", download_href(target))
            self.end_headers()
            return

        if not target.exists():
            self.send_error(404, "Directory not found")
            return

        page = render_directory(target, query.get("message", [""])[0])
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self) -> None:
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST"})
        if TOKEN and form.getfirst("token", "") != TOKEN:
            self.send_error(403, "Invalid token")
            return
        try:
            current = clean_rel(form.getfirst("path", ""))
        except ValueError as exc:
            self.send_error(400, str(exc))
            return
        if not current.is_dir():
            self.send_error(400, "Upload target is not a directory")
            return
        item = form["file"] if "file" in form else None
        if item is None or not item.filename:
            self.send_error(400, "No file uploaded")
            return
        filename = Path(item.filename).name
        target = (current / filename).resolve()
        if not inside_root(target):
            self.send_error(400, "Invalid file name")
            return
        with target.open("wb") as handle:
            shutil.copyfileobj(item.file, handle)
        self.send_response(303)
        self.send_header("Location", href(current) + f"&message=Uploaded%20{quote(filename)}")
        self.end_headers()

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} - {fmt % args}")


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"File manager listening on 0.0.0.0:{PORT}")
    print(f"Root directory: {ROOT}")
    if TOKEN:
        print("Upload token is enabled.")
    server.serve_forever()


if __name__ == "__main__":
    main()

"""Lightweight local preview server that renders Markdown files with GitHub styling.

Run with: python3 server.py
"""

from __future__ import annotations

import html
import http.server
import pathlib
import socketserver
import sys

PORT = 8000
ROOT = pathlib.Path(__file__).parent.resolve()

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>__TITLE__</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.0/github-markdown.min.css">
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    body {
      background-color: #f6f8fa;
      color: #1f2328;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 32px;
      display: flex;
      justify-content: center;
    }
    .container {
      max-width: 960px;
      width: 100%;
    }
    .profile-card {
      border: 1px solid #d0d7de;
      border-radius: 12px;
      padding: 36px;
      background: #ffffff;
      box-shadow: 0 1px 3px rgba(31,35,40,0.12), 0 8px 24px rgba(66,74,83,0.06);
    }
    .markdown-body {
      box-sizing: border-box;
      min-width: 200px;
      background: #ffffff !important;
      color: #1f2328 !important;
    }
    .markdown-body table tr {
      background-color: #ffffff !important;
      border-top: 1px solid #d0d7de !important;
    }
    .markdown-body table td, .markdown-body table th {
      border: 1px solid #d0d7de !important;
    }
    .markdown-body a {
      color: #0969da !important;
    }
    .header-bar {
      margin-bottom: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: #656d76;
      font-size: 13px;
    }
    .header-bar a {
      color: #0969da;
      text-decoration: none;
    }
    .header-bar a:hover {
      text-decoration: underline;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header-bar">
      <span>File: <strong>__FILENAME__</strong></span>
      __BACK_LINK__
    </div>
    <div class="profile-card">
      <article id="content" class="markdown-body"></article>
    </div>
  </div>

  <textarea id="raw-md" style="display:none;">__RAW_MD__</textarea>
  <script>
    const md = document.getElementById('raw-md').value;
    document.getElementById('content').innerHTML = marked.parse(md);
  </script>
</body>
</html>
"""


class MarkdownHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        # Clean path
        path = self.path.split("?")[0].split("#")[0]
        if path == "/" or path == "":
            target = ROOT / "README.md"
            self.send_rendered_markdown(target, "Amit Bhakt - PM & Builder Profile", "README.md", is_home=True)
            return
        elif path.endswith(".md"):
            clean_rel = path.lstrip("/")
            target = ROOT / clean_rel
            if target.exists():
                self.send_rendered_markdown(target, f"{clean_rel} - Amit Bhakt", clean_rel, is_home=False)
                return

        return super().do_GET()

    def send_rendered_markdown(self, filepath: pathlib.Path, title: str, filename: str, is_home: bool = False):
        try:
            content = filepath.read_text(encoding="utf-8")
            back_link = "" if is_home else '<span><a href="/">← Back to Profile</a></span>'
            rendered = (
                HTML_TEMPLATE.replace("__TITLE__", title)
                .replace("__FILENAME__", filename)
                .replace("__BACK_LINK__", back_link)
                .replace("__RAW_MD__", html.escape(content))
            )
            data = rendered.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_error(500, f"Error rendering markdown: {e}")


def main():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), MarkdownHandler) as httpd:
        print(f"--> Preview server running on http://localhost:{PORT}")
        httpd.serve_forever()


if __name__ == "__main__":
    main()

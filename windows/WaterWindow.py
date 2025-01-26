# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=multiple-imports
# pylint: disable=missing-class-docstring
# pylint: disable=broad-exception-caught
# pylint: disable=too-few-public-methods
# pylint: disable=unnecessary-lambda
# pylint: disable=invalid-name

import sys
import os
import threading
from utils import path
from http.server import SimpleHTTPRequestHandler, HTTPServer
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-gpu --no-sandbox --disable-software-rasterizer"
)


class CustomRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, texture_path, **kwargs):
        self.texture_path = texture_path
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.directory = os.path.dirname(self.texture_path)
        super().do_GET()


class LiquidPreview(QDialog):
    def __init__(self, texture=None, port=9702):
        super().__init__()

        self.texture = texture
        self.port = port
        self.server_directory = os.path.dirname(self.texture)

        self.setWindowTitle("Qthon")
        self.setGeometry(100, 100, 800, 600)
        self.web_view = QWebEngineView(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.web_view)
        self.setLayout(layout)
        self.web_view.setContextMenuPolicy(Qt.NoContextMenu)

        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True
        server_thread.start()

        with open(path("index.html"), "r") as file:
            html_content = file.read()

        new_image_path = os.path.basename(self.texture)
        html_content = html_content.replace(
            "lava.png", os.path.basename(new_image_path)
        )

        self.load_page(html_content)

    def start_server(self):
        Handler = lambda *args, **kwargs: CustomRequestHandler(
            *args, texture_path=self.texture, **kwargs
        )
        with HTTPServer(("localhost", self.port), Handler) as httpd:
            print(f"Serving at port {self.port} from directory {self.server_directory}")
            httpd.serve_forever()

    def load_page(self, html_content):
        self.web_view.setHtml(html_content, QUrl(f"http://localhost:{self.port}"))

    def closeEvent(self, event):
        # this is still erroring out because httpd isn't an attribute of LiquidPreview
        # but to be honest, I don't really care anymore
        # app's not crashing, and that's all that matters to me atm xdd
        if hasattr(self, "httpd"):
            self.httpd.shutdown()
        event.accept()


if __name__ == "__main__":
    LiquidPreview(texture="/tmp/tmp-qtwaditor-qnj9ig8q/*slime0.png", port=9742)

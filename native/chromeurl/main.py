#!/usr/bin/python3

"""
Native messaging host component of chrome current url extension.
Exposes the current chrome browser url via an http server endpoint.
"""


import argparse
import http.server
import json
import logging
import os
import signal
import socket
import struct
import sys
import threading
import time
import traceback

import requests

try:
    from .version import __version__
except Exception as ex:
    logging.error("unable to determine version: %s", ex)
    __version__ = "unknown"


current_url = None


def shutdown():
    """Shuts down the service process via a unix signal."""
    os.kill(os.getpid(), signal.SIGTERM)


def set_current_url(new_url):
    """Updates the current url."""
    global current_url
    current_url = new_url
    logging.debug("updated current_url to %s", current_url)


def get_current_url():
    """Retrieves the current url."""
    return current_url


class ChromeInfoServiceHandler(http.server.BaseHTTPRequestHandler):
    """A web server to serve info about a chrome browser instance."""

    def respond(self, status, body):
        """Sends an http response."""
        self.send_response(status)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/tabs/current/url":
            logging.debug("served current url")
            self.respond(200, current_url or "None")
        elif self.path == "/version":
            self.respond(200, __version__)
        elif self.path == "/shutdown":
            self.respond(200, "ok")
            logging.info("shutting down upon request...")
            shutdown()
        else:
            self.respond(400, "unknown route: {}".format(self.path))

    def do_POST(self):
        """Handle POST requests."""
        if self.path == "/tabs/current/url":
            length = int(self.headers.get('content-length'))
            data_raw = self.rfile.read(length)
            try:
                data = json.loads(data_raw.decode())
            except (ValueError, json.decoder.JSONDecodeError):
                self.respond(400, "invalid json")
                return
            if "url" not in data:
                self.respond(400, "invalid json")
            else:
                set_current_url(data["url"])
                self.respond(200, "ok")
        else:
            self.respond(400, "unknown route: {}".format(self.path))


class ChromeInfoService(object):
    """A web server to serve info about a chrome browser instance."""

    def __init__(self, port):
        self.port = port
        self.httpd = None

    def send_shutdown_request(self, shutdown_url=None):
        "Shutdown a previously running server."
        if not shutdown_url:
            shutdown_url = "http://localhost:{}/shutdown".format(self.port)
        resp = requests.get(shutdown_url)
        if resp.status_code // 100 == 2:
            logging.info("shutdown request was accepted: %s", resp.text)
        else:
            logging.error("shutdown via %s failed: %s %s",
                          shutdown_url, resp.status_code, resp.text)

    @staticmethod
    def port_is_open(port):
        """Returns true if the given port is open locally."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        is_open = result == 0
        sock.close()
        return is_open

    def start(self):
        """Start the http server."""
        logging.info("checking for port conflicts...")
        while self.port_is_open(self.port):
            try:
                logging.info("attempting to shut down an existing service "
                             "listening on %s...", self.port)
                self.send_shutdown_request()
            except requests.exceptions.ConnectionError as ex:
                logging.info("error shutting down previous service: %s", ex)
            time.sleep(2)
        server_address = ('', self.port)
        self.httpd = http.server.HTTPServer(server_address, ChromeInfoServiceHandler)
        logging.info("starting http server on %s", server_address)
        self.httpd.serve_forever()


class NativeMessagesLoop(object):
    """A loop to handle incoming messages from a chrome extension."""

    def __init__(self,
                 input_fh,
                 output_fh):
        self.input_fh = input_fh
        self.output_fh = output_fh

    def send(self, message):
        """Send the given message to the extension."""
        text_length_bytes = struct.pack("I", len(message))
        self.output_fh.write(text_length_bytes)
        self.output_fh.write(message.encode())
        self.output_fh.flush()

    def read_message(self):
        """Read the next message sent by the extension."""
        text_length_bytes = self.input_fh.read(4)
        logging.debug("raw 4: %s", text_length_bytes)
        if not text_length_bytes:
            # this means exit
            shutdown()

        text_length = struct.unpack("i", text_length_bytes)[0]
        logging.debug("reading message of length: %s", text_length)
        msg = self.input_fh.read(text_length).decode()
        logging.debug("message is %s", msg)
        return msg

    def start(self):
        "Continuously read messages sent by the chrome extension."
        logging.info("starting native messaging stdin read loop...")

        self.send("native messaging connection established")
        while True:
            msg = self.read_message()
            try:
                request = json.loads(msg)
            except ValueError as ex:
                traceback.print_exc()
                logging.error("unable to parse json: %s, %s", ex, msg)
                continue

            if not ("path" in request and "data" in request):
                logging.error("missing path or data in request: %s", request)
                continue

            path = request["path"]
            data = request["data"]

            if path == "/shutdown":
                shutdown()
            elif path == "/tabs/current/url":
                if "url" not in data:
                    logging.error("missing 'url': %s", data)
                else:
                    url = data["url"]
                    set_current_url(url)
            else:
                logging.error("unknown request: %s", data)


class Installer(object):
    """Install the chrome native host and external extension"""

    def __init__(self,
                 extension_hostname, extension_id,
                 executable_abs):
        self.extension_hostname = extension_hostname
        self.executable_abs = executable_abs
        self.extension_id = extension_id
        self.chrome_webstore_update_url = "https://clients2.google.com/service/update2/crx"

    @staticmethod
    def install_manifest(filename_sans_ext, manifest_dict, directory_candidates,
                         max_installations=float("inf")):
        """Install a manifest onto a number of possible directory candidates"""
        installed_manifests = []
        for cand_maybe_tilde in directory_candidates:
            if len(installed_manifests) >= max_installations:
                break
            cand = os.path.expanduser(cand_maybe_tilde)
            parent = os.path.dirname(cand)
            logging.debug("\tconsidering %s", cand)
            if not os.path.exists(cand) and os.path.exists(parent):
                # if parent exists, this could be the first native messaging host
                # so try to mkdir.
                try:
                    os.mkdir(cand)
                except OSError as ex:
                    logging.info("unable to mkdir %s: %s", cand, ex)
                    continue

            manifest_path = os.path.join(cand, "{}.json".format(filename_sans_ext))
            try:
                with open(manifest_path, "w") as manifest_fh:
                    json.dump(manifest_dict, manifest_fh, indent=4)
            except OSError as ex:
                logging.info("\tfailed to install manifest at %s:\n\t %s",
                             manifest_path, ex)
                continue
            installed_manifests.append(manifest_path)
            logging.info("installed manifest at: %s", manifest_path)

        return installed_manifests

    def install_native_host(self):
        """install chrome native host manifest file"""
        install_location_candidates = [
            # https://developer.chrome.com/extensions/nativeMessaging

            # OS X (system-wide)
            "/Library/Google/Chrome/NativeMessagingHosts/",
            "/Library/Application Support/Chromium/NativeMessagingHosts/",

            # OS X (user-specific, default path)
            "~/Library/Application Support/Google/Chrome/NativeMessagingHosts/",
            "~/Library/Application Support/Chromium/NativeMessagingHosts/",

            # Linux (system-wide)
            "/etc/opt/chrome/native-messaging-hosts/",
            "/etc/chromium/native-messaging-hosts/",

            # Linux (user-specific, default path)
            "~/.config/google-chrome/NativeMessagingHosts/",
            "~/.config/chromium/NativeMessagingHosts/"
        ]
        manifest = {
            "name": self.extension_hostname,
            "description": "chrome current url native host component",
            "path": self.executable_abs,
            "type": "stdio",
            "allowed_origins": [
                "chrome-extension://{}/".format(self.extension_id)
            ]
        }
        installed_manifests = self.install_manifest(self.extension_hostname,
                                                    manifest,
                                                    install_location_candidates)
        if not installed_manifests:
            logging.fatal("could not discover suitable native host installation directory")
            exit(1)

    def install_extension(self):
        """install chrome external extension"""
        external_extension_install_locations = [
            # https://developer.chrome.com/extensions/external_extensions
            "~/Library/Application Support/Google/Chrome/External Extensions/",
            "/Library/Application Support/Google/Chrome/External Extensions/",
            "/opt/google/chrome/extensions/",
            "/usr/share/google-chrome/extensions/",
            "/usr/share/chromium/extensions/"
        ]
        manifest = {
            "external_update_url": self.chrome_webstore_update_url
        }

        installed_manifests = self.install_manifest(
            self.extension_id, manifest,
            external_extension_install_locations)
        if not installed_manifests:
            webstore_url = "https://chrome.google.com/webstore/detail/{}".format(
                self.extension_id)
            logging.warning(
                "could not discover suitable external extension "
                "installation directory. "
                "Install the extension manually from the chrome webstore: %s",
                webstore_url)

    def install_all(self):
        """install both native host manifest and external extension"""
        self.install_native_host()
        self.install_extension()


def main():
    "Main"
    # Don't write anything to stdout, which is interpreted by the extension.
    sys.stdout = sys.stderr

    parser = argparse.ArgumentParser()
    # argument passed by the browser
    parser.add_argument("native-host-extension-id", nargs="?")
    parser.add_argument("--install", choices=["all", "native", "extension"])
    parser.add_argument("--extension-id",
                        # the published extension id
                        default="eibefbdcoojolecpoehkpmgfaeapngjk")
    parser.add_argument("-p", "--port", default=19615, type=int)
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.getLogger().setLevel(log_level)

    if args.install:
        installer = Installer(
            extension_hostname="com.erjoalgo.chrome_current_url",
            extension_id=args.extension_id,
            executable_abs=sys.argv[0]
        )
        if args.install == "all":
            installer.install_all()
        elif args.install == "native":
            installer.install_native_host()
        elif args.install == "extension":
            installer.install_extension()
        else:
            raise ValueError("unknown install option: {}".format(args.install))
        return

    logging.info("version: %s", __version__)
    native_loop = NativeMessagesLoop(
        # reopen sys.stdin, sys.stdout as binary to avoid utf errors.
        input_fh=open(0, "rb"), output_fh=open(1, "wb"))
    read_loop_thread = threading.Thread(target=native_loop.start)
    read_loop_thread.setDaemon(True)
    read_loop_thread.start()

    server = ChromeInfoService(args.port)
    server.start()


if __name__ == "__main__":
    main()

# Local Variables:
# compile-command: "./main.py fake-extension-id -p 19615 -v"
# End:

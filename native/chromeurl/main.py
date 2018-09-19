#!/usr/bin/python

"""
native messaging host component of chrome current url extension.
exposes the current chrome browser url via a REST endpoint
"""

from __future__ import print_function
from threading import Thread
import sys
import json
import time
import argparse
import logging
import urllib
import struct
import traceback
from . import install
from flask import Flask
from flask import request

logging.basicConfig()
logger = logging.getLogger('chromeurl')

try:
    from .version import __version__
except:
    logger.error("unable to determine version")
    __version__ = "unknown"


app = Flask(__name__)
port = None
current_url = None

@app.route("/tabs/current/url", methods=["GET", "POST"])
def get_current_url():
    "echo current url"
    global current_url
    logger.debug("{} /tabs/current/url".format(request.method))
    if request.method == "GET":
        return current_url or "None"
    elif request.method == "POST":
        data = request.json
        url = data["url"]
        current_url = url
        return ""
    else:
        logger.error("invalid method: {}".format(request.method))

@app.route("/version")
def version():
    try:
        from .version import __version__
        return __version__
    except Exception as ex:
        logger.error("unable to determine version: {}".format(ex))
        return "unknown"

@app.route("/shutdown")
def shutdown_request():
    "gracefully shutdown and free port for a newer process"
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    print ("got shutdown request. shutting down...")
    func()
    return 'Server shutting down...'

def send_shutdown_request():
    "shutdown a previously running server"
    shutdown_url = "http://localhost:{}/shutdown".format(port)
    print ("attempting to shut down an existing service via {}..."
           .format(shutdown_url))
    urllib.urlretrieve(shutdown_url)

def read_native_messages_loop(fh, log_fh):
    "continuously read chrome extension messages"
    global current_url

    def sendmsg(msg):
        msg_len_packed = struct.pack("i", len(msg))
        fh = sys.stdout
        fh.write(msg_len_packed)
        fh.write(msg)
        fh.flush()

    sendmsg("connected!")
    while True:
        msg_len_packed = fh.read(4)
        if not msg_len_packed:
            logger.debug("got empty message length?")
            time.sleep(.5)
            continue

        msg_len = struct.unpack("i", msg_len_packed)[0]
        logger.debug("got message of length: %s", msg_len)

        msg = fh.read(msg_len)
        logger.debug("message is %s", msg)
        try:
            data = json.loads(msg)
        except Exception as ex:
            traceback.print_exc()
            logger.error("unable to parse json: {}".format(msg))
            continue

        if "shutdown" in data:
            send_shutdown_request()
            break
        elif not "text" in data:
            logger.error("missing 'text' key: {}".format(data))
        else:
            url = data["text"]
            logger.debug("the url is %s", url)
            current_url = url
            if log_fh:
                print(url, file=log_fh)
                log_fh.flush()

EXTENSION_PUBLISHED_ID = "eibefbdcoojolecpoehkpmgfaeapngjk"
def main():
    "entry point"
    global port
    # don't write anything to stdout
    # real_stdout = sys.stdout
    sys.stdout = sys.stderr

    parser = argparse.ArgumentParser()
    parser.add_argument("extension_id", nargs="?",
                        default=EXTENSION_PUBLISHED_ID)
    parser.add_argument("--install", choices=["all", "native", "extension"])
    parser.add_argument("-p", "--port", default=19615)
    parser.add_argument("--log", help="optionally log urls to a file")
    parser.add_argument("--version", action="version", version=version())
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.install:
        if args.install == "all":
            install.install_all(args.extension_id)
        elif args.install == "native":
            install.install_native_host(args.extension_id)
        elif args.install == "extension":
            install.install_extension(args.extension_id)
        else:
            assert(False)
        return

    port = args.port

    logger.info("starting native messaging stdin read loop...")
    logger.info("version: {}".format(version()))

    try:
        send_shutdown_request()
        time.sleep(2)
    except:
        # normally the server isn't running, so this is ok
        pass

    logger.info("starting native messaging stdin read loop...")
    log_fh = open(args.log, "w") if args.log else None
    read_loop_thread = Thread(target=read_native_messages_loop,
                              args=(sys.stdin, log_fh))
    read_loop_thread.setDaemon(True)
    read_loop_thread.start()

    logger.info("starting http server on port %s", port)
    app.run(port=port)


if __name__ == "__main__":
    main()

# Local Variables:
# compile-command: "./main.py fake-extension-id -p 8080 --log /tmp/a.log"
# End:

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
from flask import Flask
from flask import request

try:
    from .version import __version__
except:
    __version__ = "unknown"

logging.basicConfig()
logger = logging.getLogger('chromeurl')

app = Flask(__name__)

current_url = None
@app.route("/tabs/current/url")
def get_current_url():
    "echo current url"
    return current_url or "None"

@app.route("/exit")
def exit_request():
    "safely exit and free port for a newer process"
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    print ("got exit request. exiting...")
    func()
    # sys.exit(0)
    return 'Server shutting down...'

def read_native_messages_loop(fh, log_fh):
    "continuously read chrome extension messages"
    global current_url

    while True:
        msg_len_str = fh.read(4)
        if not msg_len_str:
            logger.debug("got message of length 0?")
            time.sleep(.5)
            continue

        # platform dependent?
        msg_len = sum(ord(b)<<(8*(i)) for(i, b) in enumerate(msg_len_str))

        logger.debug("got message of length: %s %s", msg_len, (msg_len_str, len(msg_len_str)))

        msg = fh.read(msg_len)
        logger.debug("message is %s", msg)

        data = json.loads(msg)
        url = data["text"]
        logger.info("url is %s", url)

        current_url = url
        if log_fh:
            print(url, file=log_fh)
            log_fh.flush()

def main():
    "entry point"
    # don't write anything to stdout
    # real_stdout = sys.stdout
    sys.stdout = sys.stderr

    parser = argparse.ArgumentParser()
    parser.add_argument("extension_id") # chromium passes this positional arg on startup
    parser.add_argument("-p", "--port", default=19615)
    parser.add_argument("--log", help="optionally log urls to a file")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.info("starting native messaging stdin read loop...")

    log_fh = open(args.log, "w") if args.log else None
    read_loop_thread = Thread(target=read_native_messages_loop, args=(sys.stdin, log_fh))
    read_loop_thread.setDaemon(True)
    read_loop_thread.start()

    try:
        import urllib
        urllib.urlretrieve("http://localhost:{}/exit".format(args.port))
        print ("killed another running process...")
        time.sleep(2)
    except:
        # import traceback
        # traceback.print_exc()
        pass

    logger.info("starting http server on port %s", args.port)
    app.run(port=args.port)


if __name__ == "__main__":
    main()

# Local Variables:
# compile-command: "./main.py fake-extension-id -p 8080 --log /tmp/a.log"
# End:

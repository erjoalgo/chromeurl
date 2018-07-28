#!/usr/bin/python

from __future__ import print_function
from threading import Thread
import sys
import json
import time
from flask import Flask
import argparse
import logging

try:
    from .version import __version__
except:
    __version__="unknown"

parser = argparse.ArgumentParser()
parser.add_argument("extension_id") # chromium passes this positional arg on startup
parser.add_argument("-p", "--port", default=19615)
parser.add_argument("--log", help = "optionally log urls to a file")
parser.add_argument("--version", action="version", version=__version__)
parser.add_argument("-v", "--verbose", action="store_true")

args=parser.parse_args()
app = Flask(__name__)

logging.basicConfig()
logger = logging.getLogger('chromeurl')

if args.verbose:
    logger.setLevel(logging.DEBUG)

current_url=None
@app.route("/tabs/current/url")
def get_current_url():
    return current_url or ""

def read_native_messages_loop(fh):
    global current_url

    log_fh=open(args.log, "w") if args.log else None

    while True:
        msg_len_str=fh.read(4)
        if not msg_len_str:
            logger.debug ("got message of length 0?")
            time.sleep(.5)
            continue

        # platform dependent?
        msg_len=sum(ord(b)<<(8*(i)) for (i, b) in enumerate(msg_len_str))

        logger.debug ("got message of length: {} {}".format(msg_len, (msg_len_str, len(msg_len_str))))

        msg=fh.read(msg_len)
        logger.debug ("message is {}".format(msg))

        data=json.loads(msg)
        url=data["text"]
        logger.info ("url is {}".format(url))

        current_url=url
        if log_fh:
            print (url, file=log_fh)
            log_fh.flush()

def main():
    # don't write anything to stdout
    real_stdout=sys.stdout
    sys.stdout=sys.stderr

    logger.info("starting native messaging stdin read loop...")
    read_loop_thread = Thread(target = read_native_messages_loop, args = (sys.stdin, ))
    read_loop_thread.start()

    logger.info("starting http server on port {}".format(args.port))
    app.run(port=args.port)


if __name__ == "__main__":
    main()

# Local Variables:
# compile-command: "./chrome-current-url-native.py 123 -p 8080 --log /tmp/a.log"
# End:

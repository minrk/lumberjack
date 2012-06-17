#!/usr/bin/env python

import os,sys

import json

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options

from lumberjack.ircdb import IRCDatabase
from lumberjack.irclog import IRCLogger
from lumberjack.handlers import JSONHandler

# 8172 = int(''.join(map(str, map(string.uppercase.index, 'IRC'))))
define("port", default=8172, help="run on the given port", type=int)
define("config", default="lumberjack_config.json", type=str)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("templates/index.html")

def main():
    tornado.options.parse_command_line()
    with open(options.config) as f:
        settings = json.load(f)
    
    logger = IRCLogger(
                settings["server"],
                settings["port"],
                settings["channel"],
                settings["nick"],
                settings['db'],
    )
    logger.start_saving(5000)
    
    application = tornado.web.Application([
        (r"/", IndexHandler),
        (r"/json", JSONHandler),
        ],
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        db = IRCDatabase(settings['db']),
        channel = settings['channel'],
    )
    
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    try:
        tornado.ioloop.IOLoop.instance().start()
    finally:
        # close connections
        http_server.stop()


if __name__ == "__main__":
    while True:
        print "starting"
        main()

#!/usr/bin/env python

import os,sys

import json

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options

from lumberjack.ircdb import IRCDatabase
from lumberjack.handlers import JSONHandler

define("port", default=8888, help="run on the given port", type=int)
define("config", default="lumberjack_config.json", type=str)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("templates/index.html")

def main():
    tornado.options.parse_command_line()
    with open(options.config) as f:
        config = json.load(f)
    
    application = tornado.web.Application([
        (r"/", IndexHandler),
        (r"/json", JSONHandler),
        ],
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        db = IRCDatabase(config['db']),
        channel = config['channel'],
    )
    
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()

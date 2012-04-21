#!/usr/bin/env python

import os,sys

import json

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options

from lumberjackdb import LumberJackDatabase

define("port", default=8888, help="run on the given port", type=int)
define("db", default="../bot/lumberjack.db", type=str)


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class JSONHandler(tornado.web.RequestHandler):
    def get(self):
        db = self.application.db
        n = self.get_argument('n', 50)
        channel = self.get_argument('channel', '#ipython_bot')
        id = self.get_argument('id', 0)
        offset = self.get_argument('offset', 0)
        switch = self.get_argument('type', 'update')
        search = self.get_arguments('search', [])
        if search:
            switch = "search"
        if switch == 'tail':
            result = db.get_last(channel, n)
        elif switch == 'update':
            result = db.get_last(channel, n)
        elif switch == 'search':
            result = db.search(channel, search, limit=n, offset=offset)
        elif switch == 'context':
            ctx = self.get_argument('context', 'both')
            if ctx == 'before':
                result = db.get_before(channel, id, n)
            elif ctx == 'after':
                result = db.get_after(channel, id, n)
            else:
                result = db.get_context(channel, id, n)
        else:
            logging.error("unhandled request: %s" % switch)
            import IPython
            IPython.embed()
            result = []
        self.write(json.dumps(list(result)))
    

def main(db_file):
    tornado.options.parse_command_line()
    application = tornado.web.Application([
        (r"/", IndexHandler),
        (r"/json", JSONHandler),
        ],
        static_path=os.path.join(os.path.dirname(__file__), "static"),
    )
    application.db = LumberJackDatabase(db_file)
    
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        db_file = sys.argv[1]
    else:
        db_file = '../bot/lumberjack.db'
    main(db_file)

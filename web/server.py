#!/usr/bin/env python

import os,sys

import json

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("db", default="../bot/lumberjack.db", type=str)


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class JSONHandler(tornado.web.RequestHandler):
    def get(self):
        n = self.get_argument('n', 50)
        channel = self.get_argument('channel', 'ipython')
        id = self.get_argument('id', '')
        search = self.get_argument('search', '')
        offset = self.get_argument('offset', 0)
        switch = self.get_argument('type', 'default')
        self.write(json.dumps(['hello']))
    
    def connect_db(self):
        for i in range(5):
            try:
                self.db = sqlite3.connect(self.settings.db)
            except Exception:
                time.sleep(0.2)
            else:
                return
        raise tornado.web.HTTPError(500)
        
    

def main(db_file):
    tornado.options.parse_command_line()
    application = tornado.web.Application([
        (r"/", IndexHandler),
        (r"/json", JSONHandler),
        ],
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        db_file = db_file,
        
    )
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        db_file = sys.argv
    main()

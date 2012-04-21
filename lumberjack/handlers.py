"""
Handlers for exposing ircdb with tornado
"""

import json

import logging
import tornado.web


class JSONHandler(tornado.web.RequestHandler):
    def get(self):
        db = self.settings['db']
        n = self.get_argument('n', 50)
        channel = self.get_argument('channel', self.settings['channel'])
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
            raise tornado.web.HTTPError(404)
        self.write(json.dumps(list(result)))
    

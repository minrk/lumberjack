"""
Handlers for exposing ircdb with tornado
"""

import json

import logging
import tornado.web


class JSONHandler(tornado.web.RequestHandler):
    def get(self):
        db = self.settings['db']
        n = int(self.get_argument('n', 50))
        id = int(self.get_argument('id', 0))
        channel = self.get_argument('channel', self.settings['channel'])
        offset = int(self.get_argument('offset', 0))
        switch = self.get_argument('type', 'tail')
        search = self.get_arguments('search', [])
        if search:
            switch = "search"
        if switch == 'tail':
            result = db.get_last(channel, n)
        elif switch == 'update':
            result = db.get_since_id(channel, id, limit=n)
        elif switch == 'search':
            result = db.search(channel, search, limit=n, offset=offset)
        elif switch == 'context':
            ctx = self.get_argument('context', 'middle')
            if ctx == 'before':
                method = db.get_before
            elif ctx == 'after':
                method = db.get_after
            else:
                method = db.get_context
            result = method(channel, id, n)
            # for i in range(1,10):
            #     result = list(db.filter_silence(method(channel, id, i * n)))
            #     if len(result) >= n:
            #         break
        
        elif switch == 'tag':
            result = db.get_tag(channel, tag, limit=n)
        elif switch == 'user':
            result = db.get_user(channel)
        elif switch == 'lastseen':
            result = db.get_lastseen(channel, self.get_argument('user'))
        elif switch == 'user':
            result = db.get_user(channel, self.get_argument('user'))
        else:
            logging.error("unhandled request: %s" % switch)
            raise tornado.web.HTTPError(404)
        
        # if switch not in ('context', 'user', 'lastseen'):
        #     result = db.filter_silence(result)
        self.write(json.dumps(list(result)))
    

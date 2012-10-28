import json
import sqlite3
import datetime

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def cast_unicode(s):
    if isinstance(s, unicode):
        return s
    else:
        return s.decode('utf8', 'replace')


class IRCDatabase(object):
    
    def __init__(self, database):
        self.fname = database
        self.conn = sqlite3.connect (database)
        self.conn.row_factory = dict_factory
        #, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        self.cursor = self.conn.cursor()
        self.create_table()

    def __del__(self):
        try:
            self.conn.close()
        except:
            pass
    
    def create_table(self):
        self.cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS lumberjack
            (
                id integer primary key autoincrement,
                channel text,
                name    text,
                time    timestamp,
                message text,
                type    text,
                hidden  text
            )
            
            """)
        self.commit()

    def insert_line(self, channel, name, time, message, msgtype, hidden = "F"):

        """
        Sample line: "sfucsss, danly, 12:33-09/11/2009, I love hats, normal, 0"
        """
        channel, name, message = [ cast_unicode(s) for s in (channel, name, message)]
        args = (channel, name, time, message, msgtype, hidden)
        
        query = """INSERT INTO lumberjack
                        (channel, name, time, message, type, hidden)
                VALUES  (?      , ?   , ?   , ?      , ?   , ?)
                """

        self.cursor.execute(query, args)
    
    def commit(self):
        self.conn.commit()
    
    def _silent_after(self, r):
        if r['type'] == 'nick':
            name = r['message']
        else:
            name = r['name']
        after = self.get_user_after(r['channel'], name, r['id'])
        for entry in after:
            if entry['type'] == 'pubmsg':
                return False
            elif entry['type'] in ('quit', 'part'):
                return True
            elif entry['type'] == 'nick':
                return self._silent_after(entry)
        return True
    
    def _silent_before(self, r):
        before = self.get_user_before(r['channel'], r['name'], r['id'])
        for entry in before:
            if entry['type'] == 'pubmsg':
                return False
            elif entry['type'] == 'join':
                return True
            elif entry['type'] == 'nick':
                return self._silent_before(entry)
        return True
    
    def filter_silence(self, results):
        last_r = None
        for r in results:
            last_r = r
            if r['type'] == 'join':
                if not self._silent_after(r):
                    yield r
            elif r['type'] in ('quit', 'part'):
                if not self._silent_before(r):
                    yield r
            elif r['type'] == 'nick':
                if not self._silent_after(r):
                    yield r
                elif not self._silent_before(r):
                    yield r
            else:
                yield r
        if last_r:
            r = {
                'id' : last_r['id'],
                'time' : last_r['time'],
                'channel' : last_r['channel'],
                'type' : 'marker',
                'hidden' : 'T',
                'message' : '',
                'name' : '',
            }
            yield r
    
    def get_user_before(self, channel, user, id):
        query = """SELECT * FROM lumberjack
                WHERE channel = ? AND name = ? AND id < ?
                ORDER BY time DESC, id DESC
        """
        cursor = self.cursor.execute(query, (channel, user, id))
        return cursor
    
    def get_user_after(self, channel, user, id):
        query = """SELECT * FROM lumberjack
                WHERE channel = ? AND name = ? AND id > ?
                ORDER BY time ASC, id ASC
        """
        cursor = self.cursor.execute(query, (channel, user, id))
        return cursor
    
    def get_last(self, channel, n=100):
        query = """SELECT * FROM lumberjack 
                WHERE channel = ? 
                ORDER BY time DESC, id DESC LIMIT ?
        """
        cursor = self.cursor.execute(query, (channel, n))
        return reversed(list(cursor))
    
    def get_before(self, channel, id, n=100):
        query = """SELECT * FROM lumberjack
                WHERE channel = ? AND id < ?
                ORDER BY time DESC, id DESC LIMIT ?
        """
        return self.cursor.execute(query, (channel, id, n))
    
    def get_after(self, channel, id, n=100):
        query = """SELECT * FROM lumberjack
                WHERE channel = ? AND id > ?
                ORDER BY time ASC, id ASC LIMIT ?
        """
        return self.cursor.execute(query, (channel, id, n))
    
    def get_since_id(self, channel, id, limit=500):
        query = """SELECT * FROM lumberjack
                WHERE channel = ? AND id > ? 
                ORDER BY time ASC, id DESC LIMIT ?
        """
        return self.cursor.execute(query, (channel, id, limit))
    
    def get_offset(self, channel, id):
        query = """SELECT COUNT(*) as count FROM lumberjack
                WHERE channel = ? AND id < ?
                GROUP BY channel
        """
        cursor = self.cursor.execute(query, (channel, id))
        first = cursor.fetchone()
        if first is None:
            return 0
        else:
            return first[0]
    
    def get_context(self, channel, id, n=100):
        offset = self.get_offset(channel, id)
        offset = max(0, offset - n/2)
        
        query = """SELECT * FROM (SELECT * FROM lumberjack
                    WHERE channel = ?
                    LIMIT ? OFFSET ?
                ) channel_table
                ORDER BY time DESC
        """
        return self.cursor.execute(query, (channel, id, n))
    
    def search(self, channel, searches, limit=500, offset=0):
        query = """SELECT * FROM lumberjack
                WHERE channel = ?
        """
        args = [channel]
        if isinstance(searches, basestring):
            searches = [searches]
        for term in searches:
            query += " AND (message LIKE ? OR name LIKE ?) "
            wildterm = '%' + term + '%'
            args.append(wildterm)
            args.append(wildterm)
        query += "ORDER BY id DESC LIMIT ? OFFSET ?"
        args.append(limit)
        args.append(offset)
        cursor = self.cursor.execute(query, args)
        return reversed(list(cursor))
    
    def get_tag(self, channel, tag, limit=500):
        query = """SELECT * FROM lumberjack
                WHERE channel = ? AND message LIKE ?
                ORDER BY id DESC LIMIT ?
        """
        cursor = self.cursor.execute(query, (channel, tag + ':%', limit))
        return reversed(list(cursor))
    
    def get_lastseen(self, channel, user):
        query = """SELECT time FROM lumberjack
                WHERE channel = ? AND name = ?
                ORDER BY id DESC LIMIT 1
        """
        result = self.cursor.execute(query, (channel, user)).fetchone()
        if result:
            return result[0]
        else:
            # never seen before
            return None
    
    def get_user(self, channel, user, limit=500):
        query = """SELECT time FROM lumberjack
                WHERE channel = ? AND name = ?
                ORDER BY id DESC LIMIT ?
        """
        return self.cursor.execute(query, (channel, user, limit))


if __name__ == '__main__':
    with open('lumberjack_config.json') as f:
        settings = json.load(f)
    db = IRCDatabase(settings['db'])

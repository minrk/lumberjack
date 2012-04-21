import json
import sqlite3
import datetime


class LumberJackDatabase:
    
    def __init__(self, database):
        self.fname = database
        self.conn = sqlite3.connect (database, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
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
        
        args = (channel, name, time, message, msgtype, hidden)
        
        query = """INSERT INTO lumberjack
                        (channel, name, time, message, type, hidden)
                VALUES  (?      , ?   , ?   , ?      , ?   , ?)
                """

        self.cursor.execute(query, args)
    
    def commit(self):
        self.conn.commit()
    
    def get_last(self, channel, n=100):
        query = """SELECT * FROM lumberjack 
                WHERE channel = ? 
                ORDER BY time DESC, id DESC LIMIT ?
        """
        cursor = self.cursor.execute(query, (channel, n))
        return reversed(list(cursor))
    
    def get_before(self, channel, id, limit=500):
        query = """SELECT * FROM lumberjack
                WHERE channel = ? AND id < ?
                ORDER BY time DESC, id DESC LIMIT ?
        """
        return self.cursor.execute(query, (channel, id, limit))
    
    def get_after(self, channel, id, limit=500):
        query = """SELECT * FROM lumberjack
                WHERE channel = ? AND id > ?
                ORDER BY time ASC, id DESC LIMIT ?
        """
        return self.cursor.execute(query, (channel, id, limit))
    
    def get_between_now_and_id(self, channel, id, limit=500):
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
    db = LumberJackDatabase(settings['db'])

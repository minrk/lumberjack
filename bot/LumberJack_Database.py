import json
import sqlite3
import datetime

class LumberJackDatabase:
    
    def __init__(self, database):
        self.conn = sqlite3.connect (database)
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
                time    datetime,
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
        
        query = "INSERT INTO lumberjack (channel, name, time, message, type, hidden) VALUES (%s)" % ', '.join((['?']*len(args)))

        self.cursor.execute(query, args)
    
    def commit(self):
        self.conn.commit()


if __name__ == '__main__':
    with open('lumberjack_config.json') as f:
        settings = json.load(f)
    db = LumberJackDatabase(settings['db'])

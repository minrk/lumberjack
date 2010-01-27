import MySQLdb
import config
import datetime

class LumberJack_Database:
	
	def __init__(self, server, port, database, user, password):
		self.conn = MySQLdb.connect ( host = server,
						port = port, 
						user = user,
						passwd = password,
						db = database )
		self.cursor = self.conn.cursor()
			

	def __del__(self):
		try:
			self.conn.close()
		except: 
			return        

	def create_table(self):
		self.cursor.execute(
		"""
			CREATE TABLE IF NOT EXISTS main
			(
				id      INT(12) NOT NULL AUTO_INCREMENT PRIMARY KEY,
				channel VARCHAR(16),
				name    VARCHAR(16),
				time    DATETIME,
				message TEXT,
				type    VARCHAR(10),
				hidden  CHAR(1)
			) engine = InnoDB;
			
			""")

	def insert_line(self, channel, name, time, message, msgtype, hidden = "F"):

		"""
		Sample line: "sfucsss, danly, 12:33-09/11/2009, I love hats, normal, 0"
		"""
		query =	"INSERT INTO main (channel, name, time, message, type, hidden) VALUES" + \
		"(\""+self.conn.escape_string(channel)+ "\"," + \
		"\""+self.conn.escape_string(name)+"\"," + \
		"\""+time+"\"," + \
		"\""+self.conn.escape_string(message)+"\"," + \
		"\""+self.conn.escape_string(msgtype)+"\"," + \
		"\""+self.conn.escape_string(hidden)+"\")"

		self.cursor.execute(query)
		
	def commit(self):
		self.conn.commit()

if __name__ == "__main__":
	mysql_config = config.config("mysql_config.txt")
	db = LumberJack_Database( mysql_config["server"],
						int(mysql_config["port"]),
						mysql_config["database"], 
						mysql_config["user"],
						mysql_config["password"])
	db.create_table()
        
        
        
    

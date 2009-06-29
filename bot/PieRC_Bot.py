#! /usr/bin/env python
#

#libs
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr
import irclib
import sys
import re
import time

#mine
import PieRC_Database
import config
import CommandLine


# Configuration
irc_settings = config.config("irc_config.txt")
server = irc_settings["server"]
channel = irc_settings["channel"]
port = int(irc_settings["port"])
nick = irc_settings["nick"]

nick_reg = re.compile("^" + nick + "[:,](?iu)")
disconnect_reg = re.compile("(\sdisconnect\s)|(\squit\s)(?iu)")
echo_reg = re.compile("(echo)(?iu)")
last_seen = re.compile("last *seen (?P<username>[\S]*)(?iu)")
link_reg = re.compile("http://\S!(?iu)")


class Logger(irclib.SimpleIRCClient):
	def __init__(self, target):
		irclib.SimpleIRCClient.__init__(self)
		self.target = target
		self.echo = False
		
		# On creating the Bot, instantiate the database 
		mysql_config = config.config("mysql_config.txt")
		self.db = PieRC_Database.PieRC_Database( mysql_config["server"],
									int(mysql_config["port"]),
									mysql_config["database"], 
									mysql_config["user"],
									mysql_config["password"])
		
		self.commandline = CommandLine.CommandExecutor( self.db )
		
	def _dispatcher(self, c, e):
	# This determines how a new event is handled. 
		if(e.eventtype() == "topic" or 
		   e.eventtype() == "part" or
		   e.eventtype() == "join" or
		   e.eventtype() == "action" or
		   e.eventtype() == "nick" or
		   e.eventtype() == "pubmsg"):
			try: 
				source = e.source().split("!")[0]
			except IndexError:
				source = ""
			try:
				text = e.arguments()[0]
			except IndexError:
				text = ""
		
			# Most of the events are pushed straight to the DB.
			self.db.insert_now( channel.strip("#"), 			#channel
								source, 						#name
								text, 							#message
								e.eventtype() 					#message type
								)
		
		m = "on_" + e.eventtype()	
		if hasattr(self, m):
			getattr(self, m)(c, e)

	def on_nicknameinuse(self, c, e):
		c.nick(c.get_nickname() + "_")

	def on_welcome(self, connection, event):
		if irclib.is_channel(self.target):
			connection.join(self.target)

	def on_disconnect(self, connection, event):
		self.db.commit()
		sys.exit(0)
		
	def on_ping(self, connection, event):
		self.db.commit()

	def on_pubmsg(self, connection, event):
		text = event.arguments()[0]
		
		# Debugging output
		print "SOURCE: " + event.source();
		print "TARGET: " + event.target();
		for argument in event.arguments():
			print argument + ", "	

		# If you talk to the bot, this is how he responds.
		if nick_reg.search(text):
			if disconnect_reg.search(text):
				connection.privmsg(channel, "Aww.")
				connection.action(channel, "... TRANSFORM AND ROLL OUT!")
				self.disconnect()
			
			response = self.commandline.run_commands( text )
			
			connection.privmsg(channel, response )
			self.db.insert_now( channel.strip("#"), 			#channel
								"AutoBoose", 					#name
								response, 						#message
								'pubmsg'	 					#message type
								)

def main():

	c = Logger(channel)
	try:
		c.connect(server, port, nick)
	except irclib.ServerConnectionError, x:
		print x
		sys.exit(1)
	c.start()

if __name__ == "__main__":
	main()

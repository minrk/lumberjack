#! /usr/bin/env python
#
import logging
import json
import sys
import re
import time
import datetime

from tornado import ioloop
from tornado.iostream import IOStream

#libs
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr
import irclib

#mine
from LumberJack_Database import LumberJackDatabase

# Configuration

class Logger(irclib.SimpleIRCClient):
    
    def __init__(self, server, port, channel, nick, db, loop=None):
        irclib.SimpleIRCClient.__init__(self)
        
        # tornado ioloop
        if loop is None:
            loop = ioloop.IOLoop.instance()
        self.loop = loop
        
        #IRC details
        self.server = server
        self.port = port
        self.target = channel
        self.channel = channel
        self.nick = nick
        
        #DB details
        self.db = db
        
        #Regexes
        self.nick_reg = re.compile("^" + nick + "[:,](?iu)")
        
        #Message Cache
        self.message_cache = []        #messages are stored here before getting pushed to the db
        
        #Disconnect Countdown
        self.disconnect_countdown = 5
    
        self.last_ping = 0
        self.ircobj.delayed_commands.append( (time.time()+5, self._no_ping, [] ) )
     
        self.connect(self.server, self.port, self.nick)
    
    def connect(self, *args, **kwargs):
        logging.debug("IRC:connecting...")
        irclib.SimpleIRCClient.connect(self, *args, **kwargs)
        self.loop.add_handler(self.connection.socket.fileno(), self._handle_message, self.loop.READ)
    
    def _handle_message(self, fd, events):
        logging.debug("dispatching message")
        self.connection.process_data()
    
    def _no_ping(self):
        if self.last_ping >= 1200:
            raise irclib.ServerNotConnectedError
        else:
            self.last_ping += 10
        self.ircobj.delayed_commands.append( (time.time()+10, self._no_ping, [] ) )


    def _dispatcher(self, c, e):
    # This determines how a new event is handled. 
        if(e.eventtype() == "topic" or 
           e.eventtype() == "part" or
           e.eventtype() == "join" or
           e.eventtype() == "action" or
           e.eventtype() == "quit" or
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
        
            # Prepare a message for the buffer
            message_dict = {"channel": self.channel,
                            "name": source,
                            "message": text,
                            "type": e.eventtype(),
                            "time": str(datetime.datetime.utcnow()) } 
                            
            if e.eventtype() == "nick":
                message_dict["message"] = e.target()
            
            # Most of the events are pushed to the buffer. 
            self.message_cache.append( message_dict )
        
        m = "on_" + e.eventtype()    
        if hasattr(self, m):
            getattr(self, m)(c, e)

    def on_nicknameinuse(self, c, e):
        logging.error("nick in use")
        
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, connection, event):
        logging.info("welcome")
        if irclib.is_channel(self.target):
            connection.join(self.target)

    def on_disconnect(self, connection, event):
        logging.info("disconnect")
        self.on_ping(connection, event)
        connection.disconnect()
        raise irclib.ServerNotConnectedError

    def on_ping(self, connection, event):
        self.last_ping = 0
        self.save_messages()
    
    def save_messages(self):
        if not self.message_cache:
            logging.debug("no messages to save")
            return
        else:
            logging.info("saving %i messages" % len(self.message_cache))
        
        try:
            db = LumberJackDatabase( self.db )
            logging.info("saving %i messages" % len(self.message_cache))
            for message in self.message_cache:
                db.insert_line(message["channel"], message["name"], message["time"], message["message"], message["type"] )
            
            db.commit()
            if self.disconnect_countdown < 5:
                self.disconnect_countdown = self.disconnect_countdown + 1
            
            del db
            # clear the cache
            self.message_cache = []
                
        except Exception:
            logging.error("Couldn't connect to db: %s", self.db, exc_info=True)
            if self.disconnect_countdown <= 0:
                self.loop.stop()
            # connection.privmsg(self.channel, "Database connection lost! " + str(self.disconnect_countdown) + " retries until I give up entirely!" )
            self.disconnect_countdown = self.disconnect_countdown - 1
            

    def on_pubmsg(self, connection, event):
        text = event.arguments()[0]
        logging.info("pubmsg: %s", text)

        # If you talk to the bot, this is how he responds.
        if self.nick_reg.search(text):
            if text.split(" ")[1] and text.split(" ")[1] == "quit":
                connection.privmsg(self.channel, "Goodbye.")
                self.on_ping( connection, event )
                sys.exit( 0 ) 
                
            if text.split(" ")[1] and text.split(" ")[1] == "ping":
                self.on_ping(connection, event)
                return
    
    def start(self):
        pc = ioloop.PeriodicCallback(self.save_messages, 5000, self.loop)
        pc.start()
        self.loop.start()

def main(settings):
    logging.basicConfig(level=logging.INFO)
    c = Logger(
                settings["server"],
                settings["port"],
                settings["channel"],
                settings["nick"],
                settings['db'],
    ) 
    c.start()
    
if __name__ == "__main__":
    with open('lumberjack_config.json') as f:
        settings = json.load(f)

    reconnect_interval = settings["reconnect"]
    while True:
        try:
            main(settings)
        except irclib.ServerNotConnectedError:
            print "Server Not Connected! Let's try again!"             
            time.sleep(float(reconnect_interval))
            

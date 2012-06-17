#! /usr/bin/env python
#
import logging
import json
import sys
import re
import time
import datetime

from tornado import ioloop

#libs
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr
import irclib

#mine
from ircdb import IRCDatabase, cast_unicode

# Configuration

class IRCLogger(irclib.SimpleIRCClient):
    
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
        self.db = IRCDatabase( db )

        
        #Regexes
        self.nick_reg = re.compile("^" + nick + "[:,](?iu)")
        
        #Message Cache
        self.message_cache = []        #messages are stored here before getting pushed to the db
        
        #Disconnect Countdown
        self.disconnect_countdown = 5
        
        self._connect()
        
        self.last_ping = time.time()
        
        self.ping_callback = pc = ioloop.PeriodicCallback(self._no_ping, 60000, self.loop)
        pc.start()
        
        self.connect_callback = cc = ioloop.PeriodicCallback(self._check_connect, 30000, self.loop)
        cc.start()
        
    
    def _check_connect(self):
        """Connect to a new server, possibly disconnecting from the current.

        The bot will skip to next server in the server_list each time
        jump_server is called.
        """
        
        logging.debug("checking connection")
        if not self.connection.is_connected():
            self._connect()
    
    def _connect(self):
        logging.info("IRC:connecting to %s:%i %s as %s...", self.server, self.port, self.channel, self.nick)
        irclib.SimpleIRCClient.connect(self, self.server, self.port, self.nick)
        self.loop.add_handler(self.connection.socket.fileno(), self._handle_message, self.loop.READ)
    
    def _handle_message(self, fd, events):
        logging.debug("dispatching message")
        self.connection.process_data()
    
    def _no_ping(self):
        elapsed = time.time() - self.last_ping
        logging.debug("last ping: %is ago", elapsed)
        if elapsed >= 1200:
            logging.critical("No ping in %is: reconnecting", elapsed)
            self.loop.stop()

    def _dispatcher(self, c, e):
        """dispatch events"""
        etype = e.eventtype()
        logging.debug("dispatch: %s", etype)
        if etype in ('topic', 'part', 'join', 'action', 'quit', 'nick', 'pubmsg'):
            try: 
                source = cast_unicode(e.source().split("!")[0])
            except IndexError:
                source = u''
            try:
                text = cast_unicode(e.arguments()[0])
            except IndexError:
                text = u''
            
            # Prepare a message for the buffer
            message_dict = {"channel": self.channel,
                            "name": source,
                            "message": text,
                            "type": e.eventtype(),
                            "time": datetime.datetime.utcnow() } 
                            
            if etype == "nick":
                message_dict["message"] = e.target()
            
            # Most of the events are pushed to the buffer. 
            self.message_cache.append( message_dict )
        
        m = "on_" + etype
        if hasattr(self, m):
            getattr(self, m)(c, e)

    def on_nicknameinuse(self, c, e):
        logging.error("nick in use: %s", c.get_nickname())
        
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, connection, event):
        logging.info("welcome")
        if irclib.is_channel(self.target):
            connection.join(self.target)

    def on_disconnect(self, connection, event):
        logging.warn("disconnect")
        self.on_ping(connection, event)
        ioloop.IOLoop.instance().add_timeout(time.time()+30, self._connect)

    def on_ping(self, connection, event):
        logging.info("ping")
        self.last_ping = time.time()
        self.save_messages()
    
    def save_messages(self):
        if not self.message_cache:
            logging.debug("no messages to save")
            return
        else:
            logging.info("saving %i messages" % len(self.message_cache))
        
        try:
            for message in self.message_cache:
                self.db.insert_line(message["channel"], message["name"], message["time"], message["message"], message["type"] )
            
            self.db.commit()
            if self.disconnect_countdown < 5:
                self.disconnect_countdown = self.disconnect_countdown + 1
            
            # clear the cache
            self.message_cache = []
                
        except Exception:
            logging.error("Couldn't commit to db: %s", self.db.fname, exc_info=True)
            if self.disconnect_countdown <= 0:
                self.loop.stop()
            # connection.privmsg(self.channel, "Database connection lost! " + str(self.disconnect_countdown) + " retries until I give up entirely!" )
            self.disconnect_countdown = self.disconnect_countdown - 1
            

    def on_pubmsg(self, connection, event):
        try:
            text = cast_unicode(event.arguments()[0])
        except IndexError:
            text = u''
        
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
    
    def start_saving(self, interval=5000):
        pc = ioloop.PeriodicCallback(self.save_messages, interval, self.loop)
        pc.start()
    
    def start(self):
        self.start_saving()
        self.loop.start()

def main(settings):
    logging.basicConfig(level=settings.get('loglevel', logging.INFO))
    c = IRCLogger(
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
            pass
        print "Server Not Connected! Let's try again!"
        time.sleep(float(reconnect_interval))
            

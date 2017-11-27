## !/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import logging.config

import tornado.ioloop
import tornado.web
from tornado.options import options

from app.config import settings
from app.handlers import IndexHandler
from app.handlers import GameHandler, GameSocketHandler
from app.game_managers import OthelloGameManager

def main():

	options.parse_command_line()

	#Open a logger
	logger = logging.getLogger('app')
	logger.setLevel(logging.INFO)

	FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
	logging.basicConfig(format=FORMAT)

	othello_game_manager = OthelloGameManager()

	urls = [
		(r"/$", IndexHandler),
		#(r"/auth/login", AuthLoginHandler),
        #(r"/auth/logout", AuthLogoutHandler),
     	(r"/othello$",GameHandler),
		(r"/othello/ws$",GameSocketHandler, dict(game_manager=othello_game_manager))
	]

	application = tornado.web.Application(
		urls,
		debug=options.debug,
		autoreload=options.debug,
		**settings)

	logger.info("Starting App on port: {} with Debug mode: {}".format(options.port, options.debug))
	application.listen(options.port)
	tornado.ioloop.IOLoop.current().start()

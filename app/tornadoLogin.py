#/usr/bin/env python
#
#
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import tornado.escape
import tornado.ioloop
import tornado.web
import os.path
import uuid
from app import server
from tornado.concurrent import Future
from tornado import gen
from tornado.options import define, options, parse_command_line
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
import motor.motor_tornado

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")
logger = logging.getLogger('app')
logger.setLevel(logging.INFO)
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=FORMAT)
client = motor.motor_tornado.MotorClient('mongodb://animeshjn:<>@cluster0-shard-00-00-1wwjj.mongodb.net:27017,cluster0-shard-00-01-1wwjj.mongodb.net:27017,cluster0-shard-00-02-1wwjj.mongodb.net:27017/test?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin')
#client = motor.motor_tornado.MotorClient('mongodb://192.168.78.1:27017')
db = client.auth
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        #this is '/'
        #login page if secure cookie has no user
        #else let them play the game
        #and Check on every step
        if self.get_secure_cookie("user"):
            self.redirect("/othello")
        else:
            self.render("login.html")
class AuthLoginHandler(tornado.web.RequestHandler):

    @gen.coroutine
    def post(self):
        user = self.get_argument('usr', 'No data received')
        pwd = self.get_argument('pwd', 'No data received')
        # db = self.settings['db']
        logger.info("Login the Username {} Method=post".format(user))
        # do_find_one(Username=user,Password=pwd,isValid)
        document = yield db.col.find_one({'user': user,'password': pwd })
        logger.info("data found {}".format(document))
        # s elf.redirect("/")
        user = None
        if document:
            user = document['user']
            self.set_secure_cookie("user", user)
            self.redirect("/othello")
        else:
            logger.info("Redirecting to failed {} ".format(user))
            self.redirect("/")


    def get(self):
        self.redirect("/")

class AuthLogoutHandler(tornado.web.RequestHandler):
    def post(self):
        user = self.get_argument('usr', 'No data received')
        pwd = self.get_argument('pwd', 'No data received')
        logger.info("Logout the Username {} Method=post".format(user))
        self.clear_cookie("user")
        logger.info("Self current user {} ".format(self.get_secure_cookie("user")))
        self.redirect("/")

    def get(self):
        self.redirect("/")


class OthelloHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def post(self):
        if __name__ == "__main__":
             server.main()


def main():
    parse_command_line()
    options.parse_command_line()
        #Open a logger
    othello_game_manager = OthelloGameManager()

    urls = [
    	    (r"/$", MainHandler),
    	    (r"/auth/login", AuthLoginHandler),
            (r"/auth/logout", AuthLogoutHandler),
            (r"/othello$",GameHandler),
    	    (r"/othello/ws$",GameSocketHandler, dict(game_manager=othello_game_manager))
    ]
    app = tornado.web.Application(
            urls,
            #template_path=os.path.join(os.path.dirname(__file__), "templates"),
            #static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            cookie_secret="Othello9876%$",
            debug=options.debug,

            autoreload=options.debug,
            **settings
            )
    ssl_options={"certfile": "./certs/domain.crt", "keyfile": "./certs/domain.key"}
    app.listen(options.port, ssl_options=ssl_options)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

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
from app.config import client
from app.handlers import IndexHandler
from app.handlers import AuthRegistrationHandler, GameHandler, GameSocketHandler, GameShowHandler
from app.game_managers import OthelloGameManager
import motor.motor_tornado
import bcrypt
import base64
import os
define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")
logger = logging.getLogger('app')
logger.setLevel(logging.INFO)
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=FORMAT)
client = motor.motor_tornado.MotorClient()
db = client.othello

class MainHandler(tornado.web.RequestHandler):
    """Main handler for the application """
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
    """Login Authorization Handler
    Requires: Request Handler with Username and Password"""
    @gen.coroutine
    def post(self):
        """Handles the POST request for the Login to Othello"""
        user = self.get_argument('usr', 'No data received')
        pwd = self.get_argument('pwd', 'No data received')
        #Find the object for given username
        logger.info("Login the Username {} Method=post".format(user))
        # do_find_one(Username=user,Password=pwd,isValid)
        document = yield db.user.find_one({'user': user })
        #find the salt

        logger.info("data found {}".format(document))
        
        user = None
        if document:
            user = document['user']
            salt = document['salt']
            newhash = bcrypt.hashpw(pwd.encode('utf8'),salt)
            if newhash == document['hash']:
                logger.info("Authenticated")
                self.set_secure_cookie("user", user)
                self.redirect("/othello")               
            
        else:
            logger.info("Redirecting to failed {} ".format(user))
            self.redirect("/")


    def get(self):
        """Handles the Get Request for Login to Othello"""
        self.redirect("/")

class AuthLogoutHandler(tornado.web.RequestHandler):
    def post(self):
        user = self.get_argument('usr', 'No data received')
        
        logger.info("Logout the Username {} Method=post".format(user))
        self.clear_cookie("user")
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
            (r"/auth/register", AuthRegistrationHandler),
            (r"/othello$",GameHandler),
            (r"/allgames",GameShowHandler),
    	    (r"/othello/ws$",GameSocketHandler, dict(game_manager=othello_game_manager))
    ]
    secure_csrf_secret=base64.b64encode(os.urandom(50)).decode('ascii')
    app = tornado.web.Application(
            urls,
            #template_path=os.path.join(os.path.dirname(__file__), "templates"),
            #static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            cookie_secret=secure_csrf_secret,
            debug=options.debug,
            autoreload=options.debug,
            **settings
            )
    ssl_options={"certfile": "./certs/domain.crt", "keyfile": "./certs/domain.key"}
    app.listen(options.port, ssl_options=ssl_options)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

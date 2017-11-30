from builtins import super
import logging
import json

from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler, WebSocketClosedError

from app.game_managers import InvalidGameError
import re

logger = logging.getLogger("app")

class BaseHandler(RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class IndexHandler(RequestHandler):
	def get(self):
		self.redirect('login')



class AuthRegistrationHandler(RequestHandler):
    def get(self):
        if self.get_secure_cookie("user"):
            self.redirect("/")
        else:
            self.render("register.html")
    @coroutine
    def post(self):
    #Server side Input vaildation here
             user = self.get_argument('usr', '')
        #if user valid proceed
             pwd = self.get_argument('pwd', '')
             rpwd = self.get_argument('rpwd', '')
             email =self.get_argument('email', '')
        #if password regex True
             passwordRegex = re.compile("[A-Za-z0-9@#!$%^&+=]{8,20}")
             nameRegex = re.compile("[A-Za-z0-9]{3,20}")
             emailRegex= re.compile("[^@]+@[^@]+\.[^@]+")
             if re.match(passwordRegex, pwd, flags=0) and pwd == rpwd:
                 logger.info("Password Pattern matched")
                 if re.match(nameRegex,user):
                     logger.info("User Pattern matched")
                     if re.match(emailRegex,email):
                         logger.info("Email Pattern matched")
                         logger.info("All Patterns matched")
                         logger.info("Securing password")
                         #Check if username exists if not then:
                         
                         #create salted hash
                         #create SHA256 salt and datastructure
                         #used the initialized connection to MongoDB
                         #Redirect to login
                     else:
                         logger.info("Empty or Invalid email!")
                 else:
                     logger.info("User validation Failed!")
             else:
                 logger.info("password Failed!")
                      #username too long or too short


                 #fail message not a valid password or A


             #if re.match()



        #if re-enter password is same

        #if email is valid and has valid length

        #check if username already exists in database

        #in case of error sendMessage action = regHandler, data = message


        #push to database with empty game objects




class GameHandler(RequestHandler):
	def get(self):
		if self.get_secure_cookie("user"):
		    self.render("othello.html")
		else:
			self.redirect("/")


    # def post(self):
    # user = self.get_argument('usr', 'No data received')
    # #pwd = self.get_argument('pwd', 'No data received')


class GameSocketHandler(WebSocketHandler):

    def initialize(self, game_manager, *args, **kwargs):
        """Initialize game parameters.  Use Game Manager to register game
        """
        if self.get_secure_cookie("user"):
            self.game_manager = game_manager
            self.game_id = None
            super().initialize(*args, **kwargs)
        else:
            self.redirect("/")




    def open(self):
        """Opens a Socket Connection to client
        """
        user = self.get_secure_cookie("user").decode("utf-8")
        message = "Hello "+user+" , you are connected to Game Server"
        self.send_message(action="open", message=message)


    def on_message(self, message):
        """Respond to messages from connected client.
        Messages are of form -
        {
            action: <action>,
            <data>
        }
        Valid Actions: new, join, abort, move.
        new - Request for new game
        join - Join an existing game (but that's not been paired)
        abort - Abort the game currently on
        move - Record a move
        """
        user = self.get_secure_cookie("user").decode("utf-8")
        data = json.loads(message)
        action = data.get("action", "")
        if action == "move":
            # Game is going on
            # Set turn to False and send message to opponent
            player_selection = data.get("player_move")
            player_move = (int(player_selection[0]), int(player_selection[2])) # Gives x,y coordinates
            if player_move:
                (handler, player_choices, opp_choices, opp_unlock) = self.game_manager.record_move(self.game_id, player_move, self)
            self.send_message(action="opp-move", my_handler=handler, my_move=list(player_choices), opp_move=list(opp_choices))
            self.send_pair_message(action="move", opp_handler=handler, opp_move=list(player_choices), my_move=list(opp_choices), unlock=list(opp_unlock))

            # Check if the game is still ON
            if self.game_manager.has_game_ended(self.game_id):
                game_result = self.game_manager.get_game_result(self.game_id, self)
                self.send_message(action="end", result=game_result)
                opp_result = "L" if game_result == "W" else game_result
                self.send_pair_message(action="end", result=opp_result)
                self.game_manager.end_game(self.game_id)

        elif action == "join":
            # Get the game id
            try:
                game_id = int(data.get("game_id"))
                self.game_manager.join_game(game_id, self)
            except (ValueError, TypeError, InvalidGameError):
                self.send_message(action="error", message="Invalid Game Id: {}".format(data.get("game_id")))
            else:
                # Joined the game.
                self.game_id = game_id
                # Tell both players that they have been paired, so reset the pieces
                self.game_manager.register_player(self.game_id,2,user)
                player1 = self.game_manager.get_player_name(self.game_id, "A")
                player2 = self.game_manager.get_player_name(self.game_id, "B")
                self.send_message(action="paired", game_id=game_id, player1=player1, player2=player2)
                self.send_pair_message(action="paired", game_id=game_id, player1=player1, player2 = player2)
                # One to wait, other to move
                opp_choices = set([(3,3), (4,4)])
                my_choices = set([(3,4), (4,3)])
                self.send_message(action="opp-move", my_move=list(my_choices), opp_move=list(opp_choices))
                opp_open = set([(3,5), (5,3), (2,4), (4,2)])
                self.send_pair_message(action="move", opp_move=list(my_choices), my_move=list(opp_choices), unlock=list(opp_open))

        elif action == "new":
            # Create a new game id and respond the game id
            self.game_id = self.game_manager.new_game(self)
            self.game_manager.register_player(self.game_id,1,user)
            self.send_message(action="wait-pair", game_id=self.game_id)

        elif action == "abort":
            self.game_manager.abort_game(self.game_id)
            self.send_message(action="end", game_id=self.game_id, result="A")
            self.send_pair_message(action="end", game_id=self.game_id, result="A")
            self.game_manager.end_game(self.game_id)
        else:
            self.send_message(action="error", message="Unknown Action: {}".format(action))


    def on_close(self):
        """Overwrites WebSocketHandler.close.
        Close Game, send message to Paired client that game has ended
        """
        self.send_pair_message(action="end", game_id=self.game_id, result="A")
        self.game_manager.end_game(self.game_id)

    def send_pair_message(self, action, **data):
        """Send Message to paired Handler
        """
        if not self.game_id:
            return
        try:
            paired_handler = self.game_manager.get_pair(self.game_id, self)
        except InvalidGameError:
            logging.error("Invalid Game: {0}. Cannot send pair msg: {1}".format(self.game_id, data))
        else:
            if paired_handler:
                paired_handler.send_message(action, **data)


    def send_message(self, action, **data):
        """Sends the message to the connected client
        """
        message = {
            "action": action,
            "data": data
        }
        try:
            self.write_message(json.dumps(message))
        except WebSocketClosedError:
            logger.warning("WS_CLOSED", "Could Not send Message: " + json.dumps(message))
            # Send Websocket Closed Error to Paired Opponent
            self.send_pair_message(action="pair-closed")
            self.close()

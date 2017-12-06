from builtins import super
import logging
import json
from tornado import gen
import motor.motor_tornado
import tornado.escape
import bcrypt
from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler, WebSocketClosedError
from app.game_managers import InvalidGameError
from app.config import client
import re

logger = logging.getLogger("app")
#client = motor.motor_tornado.MotorClient()
db = client.othello

class BaseHandler(RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class IndexHandler(RequestHandler):
	def get(self):
		self.redirect('login')

class GameShowHandler(RequestHandler):
    '''Requires: Tornado Request Handler
    Modifies: Current View State
    Effects: Show all the past games and their moves to authenticated user'''
    @gen.coroutine
    def get(self):
        '''Display the data to Authenticated user'''
        if self.get_secure_cookie("user"):
            #Then Retrieve from existing connections
            game_cursor= db.game.find() # creates cursor for multiple documents
            doc=[]
            data_to_send=[]
            i = 0
            while (yield game_cursor.fetch_next):
                # data_row = {'ga'}
                document = game_cursor.next_object()
                if (document['status']!="InProgress"):
                    doc.append(document)
                
            
            self.render('trail.html',data=doc)
        else :
            self.redirect("/")
    
    # @gen.coroutine
    # def post(self):
        # if self.get_secure_cookie("user"):
            
            
        
class AuthRegistrationHandler(RequestHandler):
    '''Handler for Registration 
    Requires: Request Handler
    Modifies: Application State
    Effects: Validates data and redirects to login page if valid data 
            redirects to Registration page with error in case of unsuccessful registration'''
    def send_message(self, action, **data):
        """Sends the message to the connected client
        """
        message = {
            "action": action,
            "data": data
        }
        self.write_message(json.dumps(message))

    def get(self):
        if self.get_secure_cookie("user"):
            self.redirect("/")
        else:
            try:
                errormessage = self.get_argument("error_message")
            except:
                errormessage = ""
            self.render("register.html",error_message=errormessage)
    @gen.coroutine
    def post(self):
             '''Requires: Self
             Modifies: Application State
             Effects:
             Input validation of the Registration form and then the Registration 
             Sends Error Message in case of invalid input Redirects to Registration Page in case of error
             Redirects to Login Page in case of Successful Login'''
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
                         logger.info("All Patterns matched")                         
                         #Check if username exists
                         document = yield db.user.find_one({'user': user})
                         if bool(document):
                             logger.info("User already exists")
                             #self.send_message(action="invalidUser",data="")
                             self.render("register.html",error_message="User already exists")
                         else:
                             logger.info("User does not exist")
                             logger.info("Securing password")
                             logger.info("Attempting secure connection")
                             yield register_user(user,email,pwd)
                             self.redirect("/")
                  
                     else:
                        self.render("register.html",error_message="Empty or invalid e-mail")
                        self.finish()
                 else:
                     logger.info("User validation Failed!")
                     self.render("register.html",error_message="Not a valid user name: Must be at-least 4 characters long and should contain only characters a-z A-Z")
                     self.finish()
             else:
                 logger.info("password Failed!")
                 password_message="Invalid Password or passwords don't match, should be minimum 8 characters, Maximum 20 characters, Must contain uppercase, lowercase and special characters"
                 self.render("register.html",error_message=password_message)
                 self.finish()
        #push to database with empty game objects
        


@gen.coroutine
def alreadyExists(newUser):
    doc = yield db.user.find_one({'user': newUser})
    logger.info("{}".format(doc))
    return bool(not type(doc)==None.__class__)

@gen.coroutine
def register_user(user,email,password):
    '''Register the given user with the system by persistence into Database
    with the hashed salt and initialize game states'''
    logger.info("Registering")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf8'),salt)
    data={
        'user':user,
        'email':email,
        'salt':salt,
        'hash':hashed,
        'stats':{'win':0,'lose':0,'draw':0}
    }
    db.user.insert(data)



class GameHandler(RequestHandler):
    ''''Game Handler'''
    @gen.coroutine
    def get(self):
        if self.get_secure_cookie("user"):
            user = self.get_secure_cookie("user")
            user = user.decode("utf-8")
            
            doc = yield db.user.find_one({'user':user}) # creates cursor for multiple documents
            data_to_send =""
            if doc:
                data_to_send = doc['stats']
            else :
                data_to_send =""
                
            
            self.render("othello.html",db_data=data_to_send)
            
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

    def search_games(self, user=None):
        games = self.game_manager.games
        open_games = list()
        resume_gameid=None
        player=None
        for game_id in games.keys():
            try:
                handler=games[game_id]["handler_b"]
                if(self.game_manager.get_player_name(game_id, "B")==user):
                    resume_gameid=game_id
                    player = "B"
                elif(self.game_manager.get_player_name(game_id, "A")==user):
                    resume_gameid=game_id
                    player = "A"
            except KeyError:
                if(self.game_manager.get_player_name(game_id, "A")!=user):
                    open_games.append(game_id)
        logger.info(open_games)
        return (open_games, resume_gameid, player)

    def open(self):
        """Opens a Socket Connection to client
        """
        user = self.get_secure_cookie("user").decode("utf-8")
        message = "Hello "+user+" , you are connected to Game Server"
        (open_games, resume_gameid, player)=self.search_games(user)
        if(resume_gameid==None):
            self.send_message(action="open", message=message, open_games=open_games, user=user)
        else:
            self.resume_game(resume_gameid, player)    


    def resume_game(self, resume_gameid, player):
        self.game_manager.rejoin_game(resume_gameid, player, self)
        self.game_id = resume_gameid
        player1 = self.game_manager.get_player_name(self.game_id, "A")
        player2 = self.game_manager.get_player_name(self.game_id, "B")
        self.send_message(action="paired", game_id=self.game_id, player1=player1, player2=player2)
        self.send_pair_message(action="paired", game_id=self.game_id, player1=player1, player2 = player2)
        player_a_choices = self.game_manager.get_player_choices(self.game_id, "A")
        player_b_choices = self.game_manager.get_player_choices(self.game_id, "B")
        player_a_open = self.game_manager.get_player_choices(self.game_id, "A", "open")
        player_b_open = self.game_manager.get_player_choices(self.game_id, "B", "open")
        player_turn = self.game_manager.get_player_turn(self.game_id)
        if (player=="A"): 
            if (player_turn == "A"): # Player A resumed, player A's turn
                handler = "B"
                self.send_message(action="move", opp_handler=handler, my_move=list(player_a_choices), opp_move=list(player_b_choices), unlock=list(player_a_open)) #Message to Player A
                self.send_pair_message(action="opp-move", my_handler=handler, opp_move=list(player_a_choices), my_move=list(player_b_choices)) # Message to PLayer B       
            else: # Player A resumed, player B turn
                handler = "A"
                self.send_message(action="opp-move", my_handler=handler, my_move=list(player_a_choices), opp_move=list(player_b_choices)) #Message to Player A
                self.send_pair_message(action="move", opp_handler=handler, opp_move=list(player_a_choices), my_move=list(player_b_choices), unlock=list(player_b_open)) # Message to PLayer B       
        else: # Player B resumed
            if (player_turn == "A"): # Player B resumed, player A's turn
                handler = "B"
                self.send_message(action="opp-move", my_handler=handler, my_move=list(player_b_choices), opp_move=list(player_a_choices)) #Message to Player B
                self.send_pair_message(action="move", opp_handler=handler, opp_move=list(player_b_choices), my_move=list(player_a_choices), unlock=list(player_a_open)) # Message to PLayer A       
            else: # Player B resumed, player B turn
                handler = "A"
                self.send_message(action="move", opp_handler=handler, my_move=list(player_b_choices), opp_move=list(player_a_choices), unlock=list(player_b_open)) #Message to Player B
                self.send_pair_message(action="opp-move", my_handler=handler, opp_move=list(player_b_choices), my_move=list(player_a_choices)) # Message to PLayer A       

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
                self.game_manager.set_game_status(self.game_id,"InProgress")
                # Tell both players that they have been paired, so reset the pieces
                player1 = self.game_manager.get_player_name(self.game_id, "A")
                player2 = user
                self.game_manager.register_players(self.game_id, player1, player2)
                self.send_message(action="paired", game_id=game_id, player1=player1, player2=player2)
                self.send_pair_message(action="paired", game_id=game_id, player1=player1, player2 = player2)
                # One to wait, other to move
                opp_choices = set([(3,4), (4,3)])
                my_choices = set([(3,3), (4,4)])
                handler="B"
                self.send_message(action="opp-move", my_handler=handler, my_move=list(my_choices), opp_move=list(opp_choices))
                opp_open = set([(2,3), (3,2), (4,5), (5,4)])
                self.send_pair_message(action="move", my_handler=handler, opp_move=list(my_choices), my_move=list(opp_choices), unlock=list(opp_open))

        elif action == "new":
            # Create a new game id and respond the game id
            self.game_id = self.game_manager.new_game(self)
            self.game_manager.set_game_status(self.game_id,"Open")
            self.game_manager.register_players(self.game_id, user)
            self.send_message(action="wait-pair", game_id=self.game_id)

        elif action == "abort":
            self.game_manager.abort_game(self.game_id, self)
            self.game_manager.set_game_status(self.game_id,"Aborted")
            self.send_message(action="end", game_id=self.game_id, result="L")
            self.send_pair_message(action="end", game_id=self.game_id, result="W")
            self.game_manager.end_game(self.game_id)
        elif action == "paused":
            self.game_manager.set_game_status(self.game_id,"Paused")
            self.game_manager.audit_trail(self.game_id, "Paused")
        elif action == "forfeit":
            self.game_manager.forfeit_game(self.game_id, self)
            self.game_manager.set_game_status(self.game_id,"Error")
            self.send_message(action="end", game_id=self.game_id, result="F")
            self.game_manager.end_game(self.game_id)
        else:
            self.send_message(action="error", message="Unknown Action: {}".format(action))


    def on_close(self):
        """Overwrites WebSocketHandler.close.
        Close Game, send message to Paired client that game has ended
        """
        self.send_pair_message(action="conn_error", game_id=self.game_id)#, result="A")
        

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

from app.othello import Othello, InvalidMoveError
from tornado.concurrent import Future
from tornado import gen
import time
import motor.motor_tornado
import logging
import logging.config

#client = motor.motor_tornado.MotorClient('mongodb://animeshjn:<>@cluster0-shard-00-00-1wwjj.mongodb.net:27017,cluster0-shard-00-01-1wwjj.mongodb.net:27017,cluster0-shard-00-02-1wwjj.mongodb.net:27017/test?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin')
client = motor.motor_tornado.MotorClient()
db = client.games
LOG = logging.getLogger('app')
LOG.setLevel(logging.INFO)
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=FORMAT)

class InvalidGameError(Exception):
    """Raised when Game is not in registry
    """
    pass


class GameManager(object):

    def __init__(self):
        """Records All Games in a Dictionary and create a sequence of game ids
        """
        self.games = {}
        #self.max_game_id = 100

    def _get_next_game_id(self):
        """Returns next game id
        """
        # if self.max_game_id > 100000:
        #     self.max_game_id = 100
        # self.max_game_id += 1
        return int(time.time())

    def new_game(self, handler):
        """Creates a new Game and returns the game id
        """
        game_id = self._get_next_game_id()
        self.games[game_id] = {
            "handler_a": handler
        }
        return game_id

    def join_game(self, game_id, handler):
        """Returns game_id if join is successful.
        Raises InvalidGame when it could not join the game
        """
        game = self.get_game(game_id)
        if game.get("handler_b") is None:
            game["handler_b"] = handler
            return game_id
        # Game ID not found.
        raise InvalidGameError

    def end_game(self, game_id):
        """Removes the Game from the games registry
        """
        if game_id in self.games:
            del self.games[game_id]


    def get_pair(self, game_id, handler):
        """Returns the paired Handler
        """
        game = self.get_game(game_id)
        if handler == game.get("handler_a"):
            return game.get("handler_b")
        elif handler == game.get("handler_b"):
            return game.get("handler_a")
        else:
            raise InvalidGameError


    def get_game(self, game_id):
        """Returns the game instance.  Raises Error when game not found
        """
        game = self.games.get(game_id)
        if game:
            return game
        raise InvalidGameError

    def rejoin_game(self, game_id, player, handler):
        game = self.get_game(game_id)
        if(player=="A"):
            game["handler_a"] = handler
        else:
            game["handler_b"] = handler
        
class OthelloGameManager(GameManager):
    """Extends Game Manager to add methods specific to Othello Game
    """

    def new_game(self, handler):
        """Extend new_game with othello instance.
        """
        game_id = super().new_game(handler)
        game = self.get_game(game_id)

        game["othello"] = Othello()
        return game_id


    def record_move(self, game_id, selection, handler):
        """Record the move onto othello instance
        """
        game = self.get_game(game_id)
        if handler == game.get("handler_a"):
            game["othello"].record_player_a_move(selection)
            return ("A", game["othello"].player_a_choices, game["othello"].player_b_choices, game["othello"].player_b_open) 
        elif handler == game.get("handler_b"):
            game["othello"].record_player_b_move(selection)
            return ("B", game["othello"].player_b_choices, game["othello"].player_a_choices, game["othello"].player_a_open)

    def abort_game(self, game_id):
        """Aborts the game
        """
        game = self.get_game(game_id)
        othello = game["othello"]
        othello.abort_game()
        self.audit_trail(game_id, "Aborted")

    def has_game_ended(self, game_id):
        """Returns True if the game has ended.
        Game could end at win or draw or no more open positions.
        """
        game = self.get_game(game_id)
        othello = game["othello"]
        if othello.has_ended():
            game["result"] = othello.game_result
            self.audit_trail(game_id,"Completed")
            return True
        return False

    def get_game_result(self, game_id, handler):
        """Returns game result with a "W", "L", "D" or "E"
        """
        game = self.get_game(game_id)
        if not game.get("result"):
            # Compute game result
            self.has_game_ended(game_id)

        if game["result"] == "D" or game["result"] == "E":
            return game["result"]
                   
        elif (game["result"] == "A" and game["handler_a"] == handler) or \
                (game["result"] == "B" and game["handler_b"] == handler):
            return "W"
        elif game["result"]:
            return "L"
        else:
            return ""  # Game is still ON.

    def get_player_name(self, game_id, handler):
        game = self.get_game(game_id)
        if(handler=="A"):
            return game["othello"].player_a
        else:
            return game["othello"].player_b

    def get_player_turn(self, game_id):
        game = self.get_game(game_id)
        if(game["othello"].player_a_turn):
            return "A"
        else:
            return "B"

    def get_player_choices(self, game_id, player, choiceType=None):
        game = self.get_game(game_id)
        if(choiceType=="open"):
            if (player=="A"):
                return game["othello"].player_a_open
            else:
                return game["othello"].player_b_open
        else:
            if (player=="A"):
                return game["othello"].player_a_choices
            else:
                return game["othello"].player_b_choices


    @gen.coroutine
    def audit_trail(self, game_id, status=None):
        game = self.get_game(game_id)
        if (game["othello"].game_result==""):
            result="NA"
        else:
            result=game["othello"].game_result
        db.game.update_one({'_id':game_id},{'$set': {'status':status, 'result':result, 'score': (len(game["othello"].player_a_choices),len(game["othello"].player_b_choices)), 'p1moves': list(game["othello"].player_a_moves), 'p2moves': list(game["othello"].player_b_moves)}})
        if not status == "Completed":
            db.game.update_one({'_id':game_id},{'$set': {'status':status, 'result':result, 'score': (len(game["othello"].player_a_choices),len(game["othello"].player_b_choices)), 'p1moves': list(game["othello"].player_a_moves), 'p2moves': list(game["othello"].player_b_moves)}})
            LOG.info("Trail update called once {} {}".format(game["othello"].player_a,game["othello"].player_b))
            yield update_stats(self,game,result)
    @gen.coroutine
    def update_stats(self, game,result):

        '''Update Win or lose stats of the game 
        Requires: game is finished
        Modifies: Persistence
        '''
        #game = self.get_game(game_id)
        #If status is not already completed
        if result=='W':
            yield db.col.update({'user':game["othello"].player_a},{'$inc':{'stats.win':1}})
            yield db.col.update({'user':game["othello"].player_b},{'$inc':{'stats.lose':1}})
        if result=='L':
            yield db.col.update({'user':game["othello"].player_a},{'$inc':{'stats.lose':1}})
            yield db.col.update({'user':game["othello"].player_b},{'$inc':{'stats.win':1}})
        if result=='D':
            yield db.col.update({'user':game["othello"].player_a},{'$inc':{'stats.draw':1}})
            yield db.col.update({'user':game["othello"].player_b},{'$inc':{'stats.draw':1}})
        if result=='E':
            yield db.col.update({'user':game["othello"].player_a},{'$inc':{'stats.lose':1}})
            yield db.col.update({'user':game["othello"].player_b},{'$inc':{'stats.win':1}})
            
        #if document1

        #document2=yield db.col.find_one({'user':game["othello"].player_b})


        
        #db.game.update_one({'_id':game_id},{'$set': {'status':status, 'result':result, 'score': (len(game["othello"].player_a_choices),len(game["othello"].player_b_choices)), 'p1moves': list(game["othello"].player_a_moves), 'p2moves': list(game["othello"].player_b_moves)}})    

@gen.coroutine
def register_player(self, game_id, player_id, user):
        game = self.get_game(game_id)
        if (player_id==1):
            game["othello"].player_a=user
            db.game.insert_one({'_id':game_id, 'player1':user,'status':'Open'})
        else:
            game["othello"].player_b=user
            db.game.update_one({'_id':game_id},{'$set': {'status':'InProgress','player2':user}})
            #db.game.insert_one({'_id':game_id, 'player1':user, 'status':'Open'})
            db.game.insert_one({'_id':game_id, 'player1':user, 'status':'Open'})
        else:
            game["othello"].player_b=user
            #db.game.update_one({'_id':game_id},{'$set': {'status':'InProgress','player2':user}})            db.game.update_one({'_id':game_id},{'$set': {'player2':user}})

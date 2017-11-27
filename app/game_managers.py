from app.othello import Othello, InvalidMoveError


class InvalidGameError(Exception):
    """Raised when Game is not in registry
    """
    pass


class GameManager(object):

    def __init__(self):
        """Records All Games in a Dictionary and create a sequence of game ids
        """
        self.games = {}
        self.max_game_id = 100

    def _get_next_game_id(self):
        """Returns next game id
        """
        if self.max_game_id > 100000:
            self.max_game_id = 100
        self.max_game_id += 1
        return self.max_game_id

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
            return (game["othello"].player_a_choices, game["othello"].player_b_choices, game["othello"].player_b_open) 
        elif handler == game.get("handler_b"):
            game["othello"].record_player_b_move(selection)
            return (game["othello"].player_b_choices, game["othello"].player_a_choices, game["othello"].player_a_open)


    def abort_game(self, game_id):
        """Aborts the game
        """
        game = self.get_game(game_id)
        othello = game["othello"]
        othello.abort_game()

    def has_game_ended(self, game_id):
        """Returns True if the game has ended.
        Game cound end because of them won or it's a draw or no more open positions.
        """
        game = self.get_game(game_id)
        othello = game["othello"]
        if othello.has_ended():
            game["result"] = othello.game_result
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

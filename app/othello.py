#! /usr/bin/env python
from __future__ import print_function
from builtins import super

from collections import defaultdict
import random


class InvalidMoveError(Exception):
    """Exception Raised when Game move is not Allowed
    """
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class Othello(object):
    """Defines the Rules and maintains the State of the Othello App.
    """
    def __init__(self, player_a_marker="A", player_b_marker="B"):
        """Initializes Game States.
        """
        self.player_a_marker = player_a_marker
        self.player_b_marker = player_b_marker
        self.reset_game()

    def reset_game(self):
        """Returns None.  Resets Game states
        """
        # Set board positions
        self.game_choices = self._generate_all_game_positions()

        self.game_result = ""
        self.player_a=""
        self.player_b=""
        self.player_a_choices = set([(3,3), (4,4)])
        self.player_b_choices = set([(3,4), (4,3)])
        self.player_a_open = set([(3,5), (5,3), (2,4), (4,2)])
        self.player_b_open = set()
        self.player_a_moves = set()
        self.player_b_moves = set()
        self.player_a_turn = True

    @property
    def game_result(self):
        """Returns Game results.
        Values -
        A (Player A Won),
        B (Player B Won),
        D (Draw),
        E (Aborted),
        Empty String when game is still On
        """
        return self._game_result

    @game_result.setter
    def game_result(self, value):
        self._game_result = value

    def get_valid_choices(self):
        """Returns list of Open game positions
        """
        return list(self.game_choices)

    def has_ended(self):
        """Returns True if game has a game_result.  Otherwise False
        """
        return self.game_result != ""

    def abort_game(self):
        """Returns None.  Set Game Result to Aborted.  Removes all open Game positions.
        """
        self.game_choices = []  # Reset Game Choices
        

    def _generate_all_game_positions(self):
        """Returns a list of possible open opitions on new game
        """
        game_choices = []
        for row in range(8):
            for col in range(8):
                game_choices.append((row,col))
        game_choices.remove((3,3))
        game_choices.remove((3,4))
        game_choices.remove((4,3))
        game_choices.remove((4,4))        
        return game_choices

    def check_win_condition(self, player_marker):
        """Returns True if Player has a winning combination
        """
        if ((len(self.player_a_open)==0) or (len(self.player_b_open)==0)):
            if player_marker==self.player_a_marker:
                if(len(self.player_a_choices)>len(self.player_a_choices)):
                    return True
                else:
                    return False
            else:
                if(len(self.player_b_choices)>len(self.player_a_choices)):
                    return True
                else:
                    return False
        else:
            return False

    def check_game_draw(self):
        """Returns True if game has no open positions and has not reached a result of Win yet.
        """
        if self.game_result == "" and self.game_choices:
            return False
        return True

    def _get_player_choices(self, player_marker):
        """Returns a list of player selections made so far in the game.
        """
        if player_marker == self.player_a_marker:
            return self.player_a_choices
        else:
            return self.player_b_choices

    def validate_move(self, my_choices, opp_choices, selected_item, test_open=False):
        (ysel, xsel) = selected_item
        add_choices = set()
        for mychoice in my_choices:
            (y_my, x_my) = mychoice
            if ((xsel-x_my)==0):
                if (ysel > y_my):
                    y_range = range(y_my+1, ysel)
                elif (ysel < y_my):
                    y_range = range(ysel+1, y_my)    
                test_set = set()
                for y in y_range:
                    test_choice = (y, xsel)
                    if test_choice in opp_choices:
                        test_set.add(test_choice)
                if (len(test_set)==(abs(ysel-y_my)-1)):
                    for choice in test_set:
                        add_choices.add(choice)
                
            elif ((ysel - y_my)== 0):
                if (xsel > x_my):
                    x_range = range(x_my+1, xsel)
                elif (xsel < x_my):
                    x_range = range(xsel+1, x_my)
                test_set = set()
                for x in x_range:
                    test_choice = (ysel, x)
                    if test_choice in opp_choices:
                        test_set.add(test_choice)
                if (len(test_set)==(abs(xsel-x_my)-1)):
                    for choice in test_set:
                        add_choices.add(choice)    
                
            elif (abs(xsel-x_my)==abs(ysel-y_my)):
                if ((xsel>x_my) and (ysel>y_my)):
                    x_range= range(x_my+1, xsel)
                    y_range= range(y_my+1, ysel)
                elif ((xsel>x_my) and (ysel<y_my)):
                    x_range= range(x_my+1, xsel)
                    y_range= range(ysel+1, y_my)
                elif ((xsel<x_my) and (ysel>y_my)):
                    x_range= range(xsel+1, x_my)
                    y_range= range(y_my+1, ysel)
                elif ((xsel<x_my) and (ysel<y_my)):
                    x_range= range(xsel+1, x_my)
                    y_range= range(ysel+1, y_my)
                test_set = set()
                for x in x_range:
                    for y in y_range:
                        if (abs(xsel-x)==abs(ysel-y)):
                            test_choice = (y,x)
                            if test_choice in opp_choices:
                                test_set.add(test_choice)
                if (len(test_set)==(abs(xsel-x_my)-1)):
                    for choice in test_set:
                        add_choices.add(choice)    
        if (test_open):
            if(len(add_choices)>0):
                return True
            else:
                return False
        else:
            for choice in add_choices:
                my_choices.add(choice)
                opp_choices.remove(choice)    
            return (my_choices, opp_choices)

    def generate_positions(self, choices):
        gen_set = set()
        for choice in choices:
            (y, x)=choice
            if (y==0):
                y_range = range(y, y+2)
            elif(y==7):
                y_range = range(y-1, y+1)
            else:
                y_range = range(y-1, y+2)

            if (x==0):
                x_range = range(x, x+2)
            elif(x==7):
                x_range = range(x-1, x+1)
            else:
                x_range = range(x-1, x+2)
            for x in x_range:
                for y in y_range:
                    if ((y,x) not in gen_set) and ((y,x) in self.game_choices):
                        gen_set.add((y, x))
        return gen_set                

    def open_positions(self, my_choices, opp_choices):
        open_set = set()
        test_set = self.generate_positions(opp_choices)
        for test_choice in test_set:
            if(self.validate_move(my_choices, opp_choices, test_choice, True)):
                open_set.add(test_choice)
        return open_set

    def record_player_a_move(self, selected_item):
        
        if self.has_ended():
            raise InvalidMoveError("Game is not On.  Cannot record a move.")

        # Verify that selected item is a valid selection
        if selected_item not in self.game_choices:
            raise InvalidMoveError("Not one of the valid open positions")

        player_choices = self._get_player_choices(self.player_a_marker)
        opp_choices = self._get_player_choices(self.player_b_marker)
        (player_choices, opp_choices) = self.validate_move(player_choices, opp_choices, selected_item)
        player_choices.add(selected_item)
        self.player_a_moves.add(selected_item)
        self.player_a_choices = player_choices
        self.player_b_choices = opp_choices

        item_idx = self.game_choices.index(selected_item)
        self.game_choices = self.game_choices[:item_idx] + self.game_choices[item_idx+1:] # Removes index position

        self.player_b_open = self.open_positions(opp_choices, player_choices)
        self.player_a_turn=False
        if self.check_win_condition(self.player_a_marker):
            self.game_result = self.player_a_marker

        elif self.check_game_draw():
            self.game_result = "D"
      


    def record_player_b_move(self, selected_item):
        
        """Records Player B Move
        """
        if self.has_ended():
            raise InvalidMoveError("Game is not On.  Cannot record a move.")

        # Verify that selected item is a valid selection
        if selected_item not in self.game_choices:
            raise InvalidMoveError("Not one of the valid open positions")

        player_choices = self._get_player_choices(self.player_b_marker)
        opp_choices = self._get_player_choices(self.player_a_marker)
        (player_choices, opp_choices) = self.validate_move(player_choices, opp_choices, selected_item)
        player_choices.add(selected_item)
        self.player_b_moves.add(selected_item)
        self.player_b_choices = player_choices
        self.player_a_choices = opp_choices

        item_idx = self.game_choices.index(selected_item)
        self.game_choices = self.game_choices[:item_idx] + self.game_choices[item_idx+1:] # Removes index position

        self.player_a_open = self.open_positions(opp_choices, player_choices)
        self.player_a_turn=True
        if self.check_win_condition(self.player_b_marker):
            self.game_result = self.player_b_marker

        elif self.check_game_draw():
            self.game_result = "D"

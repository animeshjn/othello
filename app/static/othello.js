// Create a new WebSocket.
var APP = {
  wsURL: 'wss://' + window.location.host + window.location.pathname + '/ws',
  connected: false,
  myTurn: false,
  gameOn: false,
  gameId: null,

  sendMessage: function(data) {
    APP.socket.send(JSON.stringify(data));
    console.log(data);
  },

  setButtonState: function(button, value) {

    var content = button.find(".content");
    if (content) {
      // set the game matrix
      content.text(value);  // O for opponent
      button.prop("disabled", true);
    }
  },

  messageUpdate: function(message) {
    console.log(APP.gameId)
    if (APP.gameId) {
      message = "Game: " + APP.gameId + " " + message;
      console.log(message);
    }
    $("#message").text(message);
  },

  initialize: function() {

    APP.socket = new WebSocket(APP.wsURL);

    // Show a connected message when the WebSocket is opened.
    APP.socket.onopen = function(event) {
      APP.connected = true;
      APP.messageUpdate('Connected to Game Server');
    };

    // Show a disconnected message when the WebSocket is closed.
    APP.socket.onclose = function(event) {
      APP.connected = false;
      APP.messageUpdate('Disconnected from Game Server');
      APP.gameEnded();  // Game Ended - Disconnected from Server

    };

    // Handle any errors that occur.
    APP.socket.onerror = function(error) {
      APP.connected = false;
      APP.gameOn = false;
      APP.messageUpdate('Connection Error');
    };

    // Handle messages sent by the server.
    APP.socket.onmessage = function(event) {
      var payload = JSON.parse(event.data);
      var action = payload.action;
      var data = payload.data;
      APP.serverMessage(action, data);
    };
  },

  resetBoard: function() {

    $("button.btn-marker")
      .prop("disabled", false);
    $("button.btn-marker > span")
      .text("");
  },

  gameStarted: function(gameId) {
    APP.gameOn = true;
    APP.gameId = gameId;
    APP.resetBoard();
    $("#game-submit")[0].style.backgroundColor = "red";
    $("#message").attr('class','alert alert-warning col-sm-3');
    $("#game-submit").val("End Game");

  },

  gameEnded: function() {
    $("#game-room").val("");
    $("#game-submit")[0].style.backgroundColor = "";
    $("#message").attr('class','alert alert-danger col-sm-3');
    $("#game-submit").val("New Game");

    APP.gameOn = false;
    APP.myTurn = false;
    APP.gameId = null;
  },

  abortGame: function() {
    // End Game Selected
    var data = {
      action: "abort",
      game_id: APP.gameId
    };
    APP.sendMessage(data);
  },

  newGame: function() {
    if (!APP.connected) {
      APP.initialize();
    }
    var data = {
      action: "new"
    };
    APP.sendMessage(data);
  },

  joinGame: function(gameId) {
    if (!APP.connected) {
      APP.initialize();
    }

    var data = {
      action: "join",
      game_id: gameId
    };
    APP.sendMessage(data);
  },

  opponentMove: function(data) {
    APP.myTurn = true;

    var myButton = "";
    var oppButton = "";
    var oppMove = data.opp_move;
    var unlockTiles = data.unlock;
    var myMove = data.my_move;

    if(data.opp_handler=="A")
    {
      myButton = String.fromCharCode(9679);
      oppButton =  String.fromCharCode(9675);
      $("td.p1score").text(oppMove.length);
      $("td.p2score").text(myMove.length);
    }
    else
    {
     myButton = String.fromCharCode(9675);
     oppButton =  String.fromCharCode(9679);
     $("td.p1score").text(myMove.length);
     $("td.p2score").text(oppMove.length);
    }

    
    for(i=0, len=oppMove.length;i<len;i++) {
     var selectedItem = $("button").filter(function() {
       return this.value == (oppMove[i].toString());
     });
     APP.setButtonState(selectedItem, oppButton);
   }
    $("button.btn-marker")
      .prop("disabled", true);
    for(i=0, len=unlockTiles.length;i<len;i++) {
     var selectedItem = $("button").filter(function() {
       return this.value == (unlockTiles[i].toString());
     });
     selectedItem.prop("disabled", false);
   }

    
    for(i=0, len=myMove.length;i<len;i++) {
     var selectedItem = $("button").filter(function() {
       return this.value == (myMove[i].toString());
     });
     APP.setButtonState(selectedItem, myButton);
   }

  },

  myMove: function(data) {
    var myMove = data.my_move;
    var myButton = "";
    var oppButton = "";
    var oppMove = data.opp_move;

    if(data.my_handler=="A")
    {
      myButton = String.fromCharCode(9675);
      oppButton =  String.fromCharCode(9679);
      $("td.p1score").text(myMove.length);
      $("td.p2score").text(oppMove.length);
    }
    else
    {
     myButton = String.fromCharCode(9679);
     oppButton =  String.fromCharCode(9675);
     $("td.p1score").text(oppMove.length);
     $("td.p2score").text(myMove.length);
    }

    for(i=0, len=myMove.length;i<len;i++) {
     var selectedItem = $("button").filter(function() {
       return this.value == (myMove[i].toString());
     });
     APP.setButtonState(selectedItem, myButton);
   }

    
    for(i=0, len=oppMove.length;i<len;i++) {
     var selectedItem = $("button").filter(function() {
       return this.value == (oppMove[i].toString());
     });
     APP.setButtonState(selectedItem, oppButton);
   }

  },

  serverMessage: function(action, data) {
    switch (action) {
      case "open":
        var open_games=data.open_games;
        if(open_games.length==0){
          $(".collection-item").eq(0).text("There are currently no games available to join");
          for (j=1; j<10;j++){
          $(".collection-item").eq(j).hide();
        }
        }
        else
        {
        for (i=0, len=open_games.length; i<len && i<10;i++){
          var gameid = open_games[i];
          $(".collection-item").eq(i).text(gameid);
        }
        for (j=i; j<10;j++){
          $(".collection-item").eq(j).hide();
        }
        }
        APP.messageUpdate(data.message);
        break;
      case "wait-pair":
        APP.gameStarted(data.game_id);
        APP.messageUpdate("Waiting for Pair to Join..");
        break;
      case "paired":
        $("#gamesTable").hide();
        APP.gameStarted(data.game_id);
        $("td.p1name").text(data.player1);
        $("td.p2name").text(data.player2);
        APP.messageUpdate("Game Started...");
        break;
      case "move":
        APP.opponentMove(data);
        APP.messageUpdate("Your Move...")
        break;
      case "opp-move":
        APP.myTurn = false;
        APP.myMove(data);
        APP.messageUpdate("Waiting for pair to Move...")
        break;
      case "invalidUser":
        $("#user_message").text("Invalid user id or user already exists")
        break;
      case "end":
        APP.gameEnded();
        if (data.result == "W") {
          APP.messageUpdate("You Won. Congrats!")
        } else if (data.result == "L") {
          APP.messageUpdate("You Lost.  Better luck next time.")
        } else if (data.result == "D") {
          APP.messageUpdate("Draw.  Good game.");
        } else if (data.result == "A") {
          APP.messageUpdate("Game Aborted.")
        } else {
          APP.messageUpdate("Game Ended.");
        }
        break;
      case "conn_error":
      //  APP.gameOn = false
        APP.myTurn = false
        APP.messageUpdate("Connection Error. Waiting for pair to reconnect!")
        var data = {
          action: "paused",
          game_id: data.game_id
          };
        APP.sendMessage(data)
        break;
      case "error":
        if (data.message) {
          APP.messageUpdate(data.message)
        } else {
          APP.messageUpdate("Error Occured")
        }
        break;
       default:
        APP.messageUpdate("Unknown Action: " + action);
    }
  },

  buttonSelected: function(button) {
    APP.setButtonState(button, String.fromCharCode(9675));
    // send the button value to server
    var data = {
      action: "move",
      "player_move": button.val()
    };
    APP.sendMessage(data);
  }
};

$("#game-room").on("change paste keyup", function() {
  var value = $(this).val();
  if (value) {
    $("#game-submit").val("Join Game");
  } else {
    $("#game-submit").val("New Game");
  }
});

// Initialize App
APP.initialize();

$("#game-submit").click(function() {

  if (APP.gameOn) {
    // End Game Selected
    APP.abortGame();
  } else {
    // New Game / Join Game
    var gameId = $("#game-room").val();
    if (gameId) {
      APP.joinGame(gameId);
    } else {
      APP.newGame();
    }
  }
});

$("ul.row button").on("click", function(event) {
  event.preventDefault();
  if (APP.gameOn && APP.myTurn) {
    var button = $(this);
    var my_move = button.val();
    APP.buttonSelected(button);
  }
});

$("li.collection-item").on("click", function(event) {
  event.preventDefault();
  $("#gamesTable").hide();
  APP.joinGame($(this).text())
});

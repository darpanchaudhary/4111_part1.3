#!/usr/bin/env python2.7

import os
import json, ast
import pgn
import chess
import logging
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

DATABASEURI = "postgresql://kq2129:3782@35.196.90.148/proj1part2"
NEW_PLAYER_ID = -1
NEW_GAME_ID = -1

pieces = {'R':1,
         'N':2,
         'B':3,
         'Q':4,
         'K':5,
         'P':6,
         'r':7,
         'n':8,
         'b':9,
         'q':10,
         'k':11,
         'p':12,
         }

def get_positions(str_board):

    position_str = ''
    splitted_position = str_board.split('\n')
    for line in reversed(splitted_position):
        for piece in line:
            if piece in pieces:
                position_str = position_str + ',' + str(pieces[piece])
            elif piece =='.':
                position_str = position_str + ',' + '0'

    return position_str[1:]

def get_move(pre_position, curr_position):
    prev = 0
    next = 0
    piece =0


    pre_position = pre_position.split(',')
    curr_position = curr_position.split(',')


    for i in range(len(pre_position)):
        count_check = 0
        if pre_position[i] != curr_position[i]:
            count_check += 1
            if curr_position[i] != '0':

                piece = curr_position[i]
                next = i+1
            else:
                prev = i+1

    if  count_check > 2:
         raise ValueError
    return prev,next, piece


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#

@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT name FROM test")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
'''
@app.route('/another')
def another():
  return render_template("another.html")
'''

@app.route('/error')
def error():
  return render_template("error.html")

@app.route('/success')
def success():
  return render_template("success.html")

@app.route('/games')
def games():
  get_id_query = "SELECT max(gameid) AS max_id FROM games;"
  gameid = g.conn.execute(get_id_query)
  for result in gameid:
    n_id =result['max_id']
  global NEW_GAME_ID 
  NEW_GAME_ID = n_id + 1
  print(n_id)
  players = []
  tournaments = []
  games =[]
  players_list = g.conn.execute("SELECT playerid, name FROM players;")
  for result in players_list:
    players.append({"name": result['name'], "playerid": result['playerid'] })

  tournament_list = g.conn.execute("SELECT tournamentid, name FROM tournaments;")
  for result in tournament_list:
    tournaments.append({"name": result['name'], "tournamentid": result['tournamentid'] })
  
  game_list = g.conn.execute("SELECT G.gameid, (select P.name from players P where P.playerid = G.wplayer) as wplayer, (select P2.name from players P2 where P2.playerid = G.bplayer) as bplayer, G.played_on as played_on FROM games G;")
  for result in game_list:
    games.append({"gameid": result['gameid'], "wplayer": result['wplayer'], "bplayer": result['wplayer'], "played_on": str(result['played_on'])})

  return render_template("games.html", gameid = NEW_GAME_ID, player_list=players, tournament_list=tournaments, game_list=games)

@app.route('/deletegames', methods=['GET', 'POST'])
def deletegames():
  gameid = request.form.get("option_gd")
  print ("++++++++++")
  print(gameid)
  g.conn.execute("DELETE FROM games WHERE gameid =" + str(gameid) + ";")
  return redirect('/success')

@app.route('/querygames1', methods=['GET', 'POST'])
def querygames1():
  gameid = request.form.get("option_g")
  print ("++++++++++")
  print(gameid)

  game_detail =g.conn.execute("SELECT pgn FROM games where gameid=" + str(gameid)+ ";")
  for result in game_detail:
    game_pgn = result['pgn']
  return render_template("games.html", pgn = game_pgn)

@app.route('/querygames2', methods=['GET', 'POST'])
def querygames2():
  gameid = request.form.get("")
  pos_array = "'" +request.form['position_array']+ "'"

  print ("++++++++++")
  print(pos_array)

  position_detail = g.conn.execute("select positionid from positions where pos =" + pos_array + ";")
  for result in position_detail:
    position_id = result['positionid']
  print(str(position_id))
  num_games_result = g.conn.execute("select distinct(p1.name, p2.name, g.played_on) as game " + 
    " from games as g, moves as m, players as p1, players as p2 where g.gameid = m.gameid " + 
    " and m.position = "+str(position_id)+ " and g.wplayer = p1.playerid and g.bplayer = p2.playerid; ")
  games = []
  for result in num_games_result:
    game_detail = result['game']
    print(game_detail)
    games.append(str(game_detail))
  print(games[0])
  return render_template("games.html", q2_game = games)



@app.route('/tournaments')
def tournaments():
  get_id_query = "SELECT max(tournamentid) AS max_id FROM tournaments;"
  tournamentid = g.conn.execute(get_id_query)
  for result in tournamentid:
    n2_id =result['max_id']
  global NEW_TOURNAMENT_ID 
  NEW_TOURNAMENT_ID = n2_id + 1
  print(n2_id)
  tournaments = []
  tournament_list = g.conn.execute("SELECT tournamentid, name FROM tournaments;")
  for result in tournament_list:
    tournaments.append({"name": result['name'], "tournamentid": result['tournamentid'] })
  return render_template("tournaments.html", id = n2_id+1, tournament_list = tournaments)

@app.route('/inserttournaments', methods=['GET', 'POST'])
def inserttournaments():
  tournamentid = NEW_TOURNAMENT_ID
  name = "'" +request.form['name']+ "'"
  if name == "":
        return redirect('/error')
  start_date = "'" + request.form['start_date']+ "'"
  end_date = "'" + request.form['end_date']+ "'"
  prize = "'" + request.form['prize']+ "'"

  g.conn.execute("INSERT INTO tournaments VALUES(" + str(tournamentid) + "," + name + "," + start_date + "," + end_date + "," + prize + ");")
  return redirect('/success')

@app.route('/querytournaments', methods=['GET', 'POST'])
def querytournaments():
  tournamentid = request.form.get("option2")
  print ("++++++++++")
  print(tournamentid)

  tournament_detail =g.conn.execute("SELECT name, start_date, end_date, prize FROM tournaments where tournamentid=" + str(tournamentid)+ ";")
  for result in tournament_detail:
    tournament_name = result['name']
    tournament_start = result['start_date']
    tournament_end = result['end_date']
    tournament_prize = result['prize']
  num_games_result = g.conn.execute("SELECT COUNT(*) as num_games from games where tournament =" +  str(tournamentid) + ";")
  for result in num_games_result:
    num_games = result["num_games"]
  
  player_details = g.conn.execute("select distinct(p.name) from players as p, games as g where (p.playerid = g.wplayer or p.playerid = g.bplayer) and g.tournament =  " + str(tournamentid)+ ";")
  players = []
  for result in player_details:
    player_names = str(result["name"])
    players.append(player_names)

  return render_template("tournaments.html", t_id = tournamentid, t_name=tournament_name, t_start=tournament_start, t_end=tournament_end, t_num_games=num_games, t_players=players)


@app.route('/deletetournament', methods=['GET', 'POST'])
def deletetournament():
  tournamentid = request.form.get("option")
  print ("++++++++++")
  print(tournamentid)
  g.conn.execute("DELETE FROM tournaments WHERE tournamentid =" + str(tournamentid) + ";")
  return redirect('/success')


@app.route('/organizers')
def organizers():
  get_id_query = "SELECT max(organizerid) AS max_id FROM organizers;"
  organizerid = g.conn.execute(get_id_query)
  for result in organizerid:
    n3_id =result['max_id']
  global NEW_ORGANIZER_ID 
  NEW_ORGANIZER_ID = n3_id + 1
  print(n3_id)
  organizers = []
  organizer_list = g.conn.execute("SELECT organizerid, name FROM organizers;")
  for result in organizer_list:
    organizers.append({"name": result['name'], "organizerid": result['organizerid'] })
  return render_template("organizers.html", id = n3_id+1, organizer_list = organizers)

@app.route('/insertorganizers', methods=['GET', 'POST'])
def insertorganizers():
  organizerid = NEW_ORGANIZER_ID
  name = "'" +request.form['name']+ "'"
  if name == "":
        return redirect('/error')
  endowment = "'" + request.form['endowment']+ "'"

  g.conn.execute("INSERT INTO organizers VALUES(" + str(organizerid) + "," + name + "," + endowment + ");")
  return redirect('/success')

@app.route('/queryorganizers', methods=['GET', 'POST'])
def queryorganizers():
  organizerid = request.form.get("option2")
  print ("++++++++++")
  print(organizerid)

  organizer_detail =g.conn.execute("SELECT name, endowment FROM organizers where organizerid=" + str(organizerid)+ ";")
  for result in organizer_detail:
    organizer_name = result['name']
    organizer_endowment = result['endowment']
  num_tourn_result = g.conn.execute("SELECT COUNT(*) as num_tourn from organize_tournament where organizerid =" +  str(organizerid) + ";")
  for result in num_tourn_result:
    num_tourn = result["num_tourn"]
  
  tournament_details = g.conn.execute("select t.name from tournaments as t, organize_tournament as o where o.tournamentid = t.tournamentid and o.organizerid= " + str(organizerid)+ ";")
  tournaments = []
  for result in tournament_details:
    tournament_names = str(result["name"])
    tournaments.append(tournament_names)
  return render_template("organizers.html", o_id = organizerid, o_name=organizer_name, o_endowment=organizer_endowment, o_num_tourn=num_tourn, o_tourns = tournaments)

@app.route('/deleteorganizer', methods=['GET', 'POST'])
def deleteorganizer():
  organizerid = request.form.get("option")
  print ("++++++++++")
  print(organizerid)
  g.conn.execute("DELETE FROM organizers WHERE organizerid =" + str(organizerid) + ";")
  return redirect('/success')

@app.route('/players')
def players():
  get_id_query = "SELECT max(playerid) AS max_id FROM players;"
  playerid = g.conn.execute(get_id_query)
  for result in playerid:
    n_id =result['max_id']
  global NEW_PLAYER_ID 
  NEW_PLAYER_ID = n_id + 1
  players = []
  players_list = g.conn.execute("SELECT playerid, name FROM players;")
  for result in players_list:
    players.append({"name": result['name'], "playerid": result['playerid'] })
  return render_template("players.html", id = n_id+1, player_list=players)


#@app.route('/insertmoves', methods=['GET', 'POST'])
def insertmoves( pgn, gameid ):
  board = chess.Board()
  moves = pgn
  positions_list = []
  moves_info =[]
  splitted_move =moves.split('\n')
  pre_position = get_positions(str(board))
  for line in splitted_move:

    for move  in line[1:-1].split(' '):
      #print (i+1)
      #try:
      if move[-1] != '.':
 
        board.push_san(str(move))
        str_board = str(board)
        curr_position = get_positions(str_board)
        positions_list.append(curr_position)
        prev, next, piece = get_move(pre_position, curr_position)
        moves_info.append(str(prev)+ ', ' + str(next) + ', ' + str(piece))
        pre_position = curr_position 


  position_query = []

  moves_query = []


  print(len(positions_list))
  print(len(moves_info))

  if (len(positions_list) != len(moves_info)):
    raise ValueError

  for i in range(len(positions_list)):
    position_id = g.conn.execute("SELECT MAX(positionid) as max_pos from positions;")
    for result in position_id:
      pos_id = result["max_pos"] + 1


    position_row = "(" + str(pos_id) + ", " + "'{" + positions_list[i] + "}')"
    #position_list[i]=[str(i) for i in position_list[i]]
    g.conn.execute("INSERT INTO positions VALUES" + position_row + ";")
    #position_query.append(position_row)
    
    #print (position_row)

  for i in range(len(moves_info)):
    move_id = -1
    moves_id = g.conn.execute("SELECT MAX(moveid) as max_mov from moves;")
    for result in position_id:
      mov_id = result["max_pos"] + 1

    if move_id == -1:
      return redirect('/error')
    moves_row = "(" +  str(mov_id) + ", " + str(gameid) + ", " + str(i+1) + ", " + [str(x) for x in moves_info[i]] + ", "+ str(i+100) + "),"
    g.conn.execute("INSERT INTO moves VALUES" + moves_row + ";")

    #moves_info.append(moves_row)
    #print (moves_row)



@app.route('/insertgames', methods=['GET', 'POST'])
def insertgames():
  #gameid = request.form['gameid']
  get_id_query = "SELECT max(gameid) AS max_id FROM games;"
  gameid = -1 
  gameids = g.conn.execute(get_id_query)
  for result in gameids:
    gameid =result['max_id'] + 1
  if gameid == -1:
    return redirect('/errors')
  wplayer = request.form.get("w_option")
  if wplayer == "":
        return redirect('/error')
  bplayer = request.form.get("b_option")
  if bplayer == "":
        return redirect('/error')
  pgn_text = "'" +request.form['pgn']+ "'"
  played_on = "'" + request.form['played_on']+ "'"
  tournament = request.form.get("t_option")
  print("INSERT INTO games VALUES(" + str(gameid) + "," + str(wplayer) + "," + str(bplayer) + "," + pgn_text + "," + played_on + "," + str(tournament)+ ");")
  g.conn.execute("INSERT INTO games VALUES(" + str(gameid) + "," + str(wplayer) + "," + str(bplayer) + "," + pgn_text + "," + played_on + "," + str(tournament)+ ");")
  try:
    insertmoves(pgn_text, gameid)
  except:
    return redirect('/error')
  return redirect('/success')


@app.route('/insertplayers', methods=['GET', 'POST'])
def insertplayers():
  playerid = NEW_PLAYER_ID
  name = "'" +request.form['name']+ "'"
  if name == "":
        return redirect('/error')
  joined = "'" + request.form['joined']+ "'"
  
  rating = request.form['rating']
  g.conn.execute("INSERT INTO players VALUES(" + str(playerid) + "," + name + "," + joined + "," + str(rating)+ ");")
  return redirect('/success')


@app.route('/deleteplayers', methods=['GET', 'POST'])
def deleteplayers():
  playerid = request.form.get("option")
 
  g.conn.execute("DELETE FROM players WHERE playerid =" + str(playerid) +";")
  return redirect('/success')

@app.route('/queryplayers', methods=['GET', 'POST'])
def queryplayers():
  # player_name = ""
  # player_joined = 0
  # playerid = 0
  # player_rating=0

  playerid = request.form.get("option2")
  print ("++++++++++")
  print(playerid)

  player_detail =g.conn.execute("SELECT name, joined, rating FROM players where playerid=" + str(playerid)+ ";")
  for result in player_detail:
    player_name = result['name']
    player_joined = result['joined']
    player_rating = result['rating']
  no_games_result =g.conn.execute("SELECT COUNT(*) as no_games from games where wplayer =" +  str(playerid) + " OR bplayer = " + str(playerid)+ ";")
  for result in no_games_result:
    no_games = result["no_games"]
  
  win_no_result = g.conn.execute("SELECT COUNT(*) as no_win from games, results where ((wplayer =" +  str(playerid) + "AND wpoints=1) OR (bplayer = " + str(playerid)+ " AND bpoints=1)) and games.gameid=results.gameid")
  for result in win_no_result:
    no_win = result["no_win"]
  print(no_games)
  print(no_win)
  if (no_games==0):
    win_percentage = 0
  else:
    win_percentage = (no_win/no_games) * 100


  return render_template("players.html", player_id = playerid, name=player_name, rating=player_rating, no_played=no_games, no_won=no_win, win_percentage=win_percentage)




# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test VALUES (NULL, ?)', name)
  return redirect('/')


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()

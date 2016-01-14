import time
import os
import sys
import json
#Parser written to take parse games from .pgn into a better json format
 #also parses stockfish moves into a file

#I'm going to have 35,000 Games for my training set, and 15,000 for my validation set

def rError(expected,found):
	print("ERROR, expected "+ str(expected), ", found "+ str(found))
	exit()

IDK = "None"
WHITE = 0
BLACK = 1
DRAW = 2

class Move:
	#Moves need
	#UCI description of the move
	#stockfish rating of the move
	#whether it was white or black who moved
	 #will probably be changed to include more features (such as piece moved, etc)
	def __init__(self, uci, color):
		self.color = color
		if uci == None:
			self.uci = 0
		else:
			self.uci = self.parseMove(uci)
		self.rating = 0

	def LtN(self,st):
		if st == "a":
			return "1"
		elif st == "b":
			return "2"
		elif st == "c":
			return "3"
		elif st == "d":
			return "4"
		elif st == "e":
			return "5"
		elif st == "f":
			return "6"
		elif st == "g":
			return "7"
		elif st == "h":
			return "8"
		else:
			raise Exception("Unexpected String " + st)

	def parseMove(self,uci):
		newstr = self.LtN(uci[0])+uci[1]+self.LtN(uci[2])+uci[3]
		return int(newstr)

	def setRating(self,rating):
		try:
			self.rating = int(rating)
		except:
			self.rating = 0

class Turn:
	#intermediary that has two moves and the number turn it is
	def __init__(self,turn, white, black):
		self.turn = turn
		self.moves = []
		self.addMove(WHITE,white)
		self.addMove(BLACK,black)

	def addMove(self, color, uci):
		self.moves.append(Move(uci,color))

class Game:
	#following fields
	#Event Number ("Just for recordkeeping, no valuable data can be gleaned from this")
	#Result
	#WhiteELO
	#BlackELO
	##numMoves
	#Moves
	def __init__(self,num):
		self.number = num
		self.result = IDK
		self.whiteELO = None
		self.blackELO = None
		self.turns = []

	def addResult(self,result):
		if result == "1/2-1/2":
			self.result = DRAW
		elif result == "1-0":
			self.result = WHITE
		elif result == "0-1":
			self.result = BLACK
		else:
			raise Exception("Invalid Winner " + result)

	def setWhiteELO(self,elo):
		self.whiteELO = int(elo)

	def setBlackELO(self,elo):
		self.blackELO = int(elo)

	def addTurn(self,white,black):
		self.turns.append(Turn(len(self.turns)+1,white,black))

	def addNumMoves(self,num):
		self.numMoves = num

class Parser:
	#contains functions to parse the different files, data_uci, data, and stockfish

	def parseStockfish(self,games,fn):
		#parses stockfish for the movescores
		f = open(fn,"r")
		if len(games) == 0:
			raise Exception("no games")
		#print(len(games))
		counter = 0
		for line in f:
			if line[0] == "E":
				continue

			line = line.strip();
			l = line.split(",")
			if (int(counter) % 1000 == 0):
				print(counter)
			if (counter+1 != games[counter].number):
				rError(games[counter].number,counter)
			else:
				white = None
				black = None

				scores = l[1].split(" ")
				for m in range(len(scores)):
					move = scores[m]
					if (m % 2) == 0:
						turn = WHITE
					else:
						turn = BLACK
					games[counter].turns[m//2].moves[turn].setRating(move)
			counter+=1
		f.close()
		#print("all done parsing")
		return games


	def parseValue(self,st):
		#Parses strings of the form [xxx "yyyyy"] into a list [xxx,yyyyy]
		s = st.split("[")
		t = s[1].split("]")
		r = t[0].split(" ")
		i = r[1].split("\"")
		g = [r[0],i[1]]
		return g

		
	def read_uci(self,fn):
		f = open(fn, "r")
		rgame = 0 #currently looking at a game, helps with exception handling
		i = 0 #if this gets too big something broke
		games = []
		game = None
		gamenum = 0
		for line in f:
			line = line.strip()
			if line == "":
				if (rgame == 5) or (rgame == 2):
					if i == 0:
						i = 1
						rgame = 5
					else:
						rgame = 0
						i = 0
						games.append(game)
						game = None
			elif rgame == 0:
				if line[1] != "E":
					rError("start of game",line)
				else:
					rgame = 1
					i = 0
					gamenum+=1
					if ((gamenum % 1000) == 0):
						print(gamenum)
					game = Game(gamenum)
			elif rgame == 1:
				#next I need to parse the result

				l = self.parseValue(line)
				if l[0] == "Result":
					i = 0
					rgame = 2
					game.addResult(l[1])
				else:
					i+=1
					if (i > 10):
						rERROR("Result",l)
			elif rgame == 2:
				#next whiteELO

				l = self.parseValue(line)
				if l[0] == "WhiteElo":
					rgame = 4
					game.setWhiteELO(l[1])
				else:
					rError("WhiteElo",line)
			elif rgame == 4:
				#bxlackelo time
				l = self.parseValue(line)
				if l[0] == "BlackElo":
					rgame = 5
					game.setBlackELO(l[1])
				else:
					rError("BlackElo",line)
			elif rgame == 5:
				#now looking at moves,
				l = line.split(" ")
				l.pop() #get rid of the last value, which is just a rehash of the score
				white = None
				black = None
				for move in l:
					if white == None:
						white = move
						if l[-1] == move:
							#ends on whites turn
							game.addTurn(white,None)
							white = None
							black = None
					elif black == None:
						black = move
						game.addTurn(white,black)
						white = None
						black = None
					else:
						print("ERROR, MOVE NOT RIGHT")
						exit()
		f.close()
		return games #a list of Game instances for every game found in the file, can be used later to go into json format


'''parser = Parser()
games = parser.read_uci(sys.argv[1])
scored = parser.parseStockfish(games,sys.argv[2])
output = dict()
gam = []
k = 0
for game in scored:
	k+=1
	if k % 1000 == 0:
		print(k)
	g = dict()
	g['number'] = game.number
	g['whiteELO'] = game.whiteELO
	g['blackELO'] = game.blackELO
	g['result'] = game.result
	tur = []
	for turn in game.turns:
		t = dict()
		white = dict()
		t['turn'] = turn.turn
		white['move'] = turn.moves[0].uci
		white['score'] = turn.moves[0].rating
		black = dict()
		black['move'] = turn.moves[1].uci
		black['score'] = turn.moves[1].rating
		t['white'] = white
		t['black'] = black
		tur.append(t)
	g['turns'] = tur
	gam.append(g)
out = []
for i in range(5):
	out.append(gam[i])
output['Games'] = out
f = open(sys.argv[3],"w")
json.dump(output,f,indent=4)
f.close()

print("Calcing num games where loser has a higher elo")
count = 0
for i in range(len(scored)-1):
	if scored[i].result == BLACK:
		if scored[i].blackELO < scored[i].whiteELO:
			count+=1
	elif scored[i].result == WHITE:
		if scored[i].blackELO > scored[i].whiteELO:
			count+=1
print(count)'''
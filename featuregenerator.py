from parser import Move, Turn, Game, Parser
from models import knn, lr,tree,forest,knnO,treeO,forestO,svm,nb,perceptron, ensemble1, ensemble2, ensemble3
from models import ensemble4,ensemble5
import sys
import json
import os

OPENING = 0.1
MIDGAME = 0.8
ENDGAME = 0.1

WHITE = 0
BLACK = 1
DRAW = 2

def toKaggle(y_w_w,y_b_w,y_w_b,y_b_b,y_w_d,y_b_d,ww_n,bw_n,d_n):
	#Given a list of y_ predictions, make the kaggle file
	print("ww "+str(len(y_w_w)) + " "+str(len(y_b_w))+" "+str(len(ww_n)))
	print("bw "+str(len(y_w_b)) + " "+str(len(y_b_b))+" "+str(len(bw_n)))
	print("d " +str(len(y_w_d)) +" " +str(len(y_b_d)) +" "+str(len(d_n)))
	out = open("submission.csv","w")
	out.write("Event,WhiteElo,BlackElo")
	for i in range(len(y_w_w)):
		out.write("\n")
		out.write(str(25000+ww_n[i]))
		out.write(",")
		out.write(str(y_w_w[i]))
		out.write(",")
		out.write(str(y_b_w[i]))
	for j in range(len(y_w_b)):
		out.write("\n")
		out.write(str(25000+bw_n[j]))
		out.write(",")
		out.write(str(y_w_b[j]))
		out.write(",")
		out.write(str(y_b_b[j]))
	for k in range(len(y_w_d)):
		out.write("\n")
		out.write(str(25000+d_n[k]))
		out.write(",")
		out.write(str(y_w_d[k]))
		out.write(",")
		out.write(str(y_b_d[k]))
	out.close()
	pass

def getPartitions(numturns, part):
	#parts 1,2,3
	part1 = int(numturns*OPENING)
	part2 = int(numturns*MIDGAME)
	part3 = numturns - part1 - part2
	if part == OPENING:
		return part1
	elif part == MIDGAME:
		return part2
	else:
		return part3

def scoreswitch(game):
	#counts number of times who is ahead changes
	positive = True 
	count = 0
	for i in game.turns:
		if positive == True:
			if i.moves[0].rating < 0:
				count+=1
				positive = False
		if positive == False:
			if i.moves[0].rating > 0:
				count+=1
				positive = False
		if positive == True:
			if i.moves[1].rating < 0:
				count+= 1
				positive = False
		if positive == False:
			if i.moves[1].rating > 0:
				count+=1
				positive = False
	return count

def maximumscore(game):
	#maximum score in the game
	mx = -100000
	for i in game.turns:
		if i.moves[0].rating > mx:
			mx = i.moves[0].rating
		if i.moves[1].rating > mx:
			mx = i.moves[1].rating
	return mx*-1

def minimumscore(game):
	#minimum score in the game
	mn = 10000
	for i in game.turns:
		if i.moves[0].rating < mn:
			mn = i.moves[0].rating
		if i.moves[1].rating < mn:
			mn = i.moves[1].rating
	return mn*-1

def averagescorechange(game):
	#average amount the score changes per move
	#Doing absolute value but I think it might just work how I want without it
	score = 0
	for i in range(len(game.turns)):
		if i == 0:
			#base case
			pass
		else:
			score+=abs(game.turns[i].moves[0].rating-game.turns[i-1].moves[1].rating)
		score+=abs(game.turns[i].moves[1].rating-game.turns[i].moves[0].rating)
	return score/(len(game.turns)*2)

def totalscore(game):
	#gets total change in score
	score = 0
	for i in game.turns:
		score += i.moves[0].rating
		score += i.moves[1].rating
	return score*-1
	
def numturns(game):
	#number of turns in the game
	return len(game.turns)

def averagescore(game):
	#3)average score 
	score = 0
	for j in game.turns:
		score+= j.moves[0].rating
		score+= j.moves[1].rating
	return (score/(len(game.turns)*2))*-1

def numlosingturns(game):
	#% of game where white is ahead
	numlosingturns = 0
	for j in game.turns:
		if j.moves[0].rating < 0:
			numlosingturns+=1
		if j.moves[1].rating < 0:
			numlosingturns+=1
	return (numlosingturns)/(len(game.turns))

def averageopening(game):
	#average score in opening
	o = getPartitions(len(game.turns),OPENING)
	score = 0
	for k in range(int(o)):
		score+=game.turns[k].moves[0].rating
		score+=game.turns[k].moves[1].rating
	score = score / max(1,(int(o)*2))
	return score*-1

def scoreopening(game):
	#score at end of opening
	o = int(getPartitions(len(game.turns),OPENING))
	return game.turns[o-1].moves[0].rating*-1

def averagemidgame(game):
	#average score in midgame
	m = getPartitions(len(game.turns),MIDGAME)
	o = getPartitions(len(game.turns),OPENING)
	score = 0
	for k in range(int(m)+int(o)):
		if k < o:
			continue
		score+= game.turns[k].moves[0].rating
		score+= game.turns[k].moves[1].rating
	score = score / max(1,(m*2))
	return score*-1

def scoremidgame(game):
	#score at/near end of midgame
	m = getPartitions(len(game.turns),MIDGAME)
	return game.turns[m-1].moves[0].rating*-1

def averageendgame(game):
	#average score in endgame
	score = 0
	for k in range(len(game.turns)):
		if k < (getPartitions(len(game.turns),OPENING)+getPartitions(len(game.turns),MIDGAME)):
			continue
		score+= game.turns[k].moves[0].rating
		score+= game.turns[k].moves[1].rating
	return (score / max(1,(getPartitions(len(game.turns),ENDGAME)*2)))*-1

def lastscore(game):
	#score of last white move in the game
	return game.turns[-1].moves[0].rating*-1

def getLabels(games, color):
	#makes a y array for all the games labels
	arr = []
	for i in games:
		if color == BLACK:
			arr.append(i.blackELO)
		else:
			arr.append(i.whiteELO)
	return arr

def set1(scored):
	arr = []
	for i in scored:
		game = []
		#decided on 10 featueres
		game.append(numturns(i))
		game.append(averagescore(i))
		game.append(numlosingturns(i))
		game.append(averageopening(i))
		game.append(scoreopening(i))
		game.append(averagemidgame(i))
		game.append(scoremidgame(i))
		game.append(averageendgame(i))
		game.append(lastscore(i))
		arr.append(game)
	return arr

def set2(scored):
	arr = []
	for i in scored:
		game = []
		game.append(numturns(i)) #number of turns in the game
		game.append(averagescore(i)) #average score
		game.append(numlosingturns(i)) #% of game where white is ahead
		game.append(averageopening(i)) # average score in opening
		game.append(scoreopening(i)) #score at end of opening
		game.append(averagemidgame(i)) #average score in midgame
		game.append(scoremidgame(i)) #score at/near end of midgame
		game.append(averageendgame(i)) #average score in endgame
		game.append(lastscore(i)) #score of last white move at end of the game

		game.append(totalscore(i)) #gets total change in score

		game.append(averagescorechange(i)) #average amount the score changes per move
		game.append(minimumscore(i)) #minimum score in the game
		game.append(maximumscore(i)) #maximum score in the game
		game.append(scoreswitch(i)) #counts number of times who is ahead changes
		arr.append(game)
	return arr

def meanError(y,y_):
	#Average absolute mean error between y and y_
	error = 0
	for i in range(len(y)):
		error += abs(y[i]-y_[i])
	return error/len(y)

def knnScoresAll():
	#use knn using scores and other features
	parser = Parser()
	print("PARSING")
	games = parser.read_uci(sys.argv[1])
	scored = parser.parseStockfish(games,sys.argv[2])

	validationgames = parser.read_uci(sys.argv[3])
	validationscored = parser.parseStockfish(validationgames,sys.argv[4])

	print("Building Features/Labels")
	#Now I'm going to run KNN which is going to return y_
	training_features = []
	#finding longest game
	longest = 0
	for i in scored:
		if len(i.turns) > longest:
			longest = len(i.turns)
	for i in validationscored:
		if len(i.turns) > longest:
			longest = len(i.turns)
	#have longest game
	for i in scored:
		game = []
		for j in range(len(i.turns)):
			game.append(i.turns[j].moves[0].rating)
			game.append(i.turns[j].moves[1].rating)
		for k in range(longest):
			if k < j:
				continue
			game.append(0)
			game.append(0)
		game.append(numturns(i)) #number of turns in the game
		game.append(averagescore(i)) #average score
		game.append(numlosingturns(i)) #% of game where white is ahead
		game.append(averageopening(i)) # average score in opening
		game.append(scoreopening(i)) #score at end of opening
		game.append(averagemidgame(i)) #average score in midgame
		game.append(scoremidgame(i)) #score at/near end of midgame
		game.append(averageendgame(i)) #average score in endgame
		game.append(lastscore(i)) #score of last white move at end of the game

		game.append(totalscore(i)) #gets total change in score

		game.append(averagescorechange(i)) #average amount the score changes per move
		game.append(minimumscore(i)) #minimum score in the game
		game.append(maximumscore(i)) #maximum score in the game
		game.append(scoreswitch(i)) #counts number of times who is ahead changes
		training_features.append(game)



	training_labels_w = getLabels(scored,WHITE)
	training_labels_b = getLabels(scored,BLACK)

	validation_features = []

	for i in validationscored:
		game = []
		for j in range(len(i.turns)):
			game.append(i.turns[j].moves[0].rating)
			game.append(i.turns[j].moves[1].rating)
		for k in range(longest):
			if k < j:
				continue
			game.append(0)
			game.append(0)
		game.append(numturns(i)) #number of turns in the game
		game.append(averagescore(i)) #average score
		game.append(numlosingturns(i)) #% of game where white is ahead
		game.append(averageopening(i)) # average score in opening
		game.append(scoreopening(i)) #score at end of opening
		game.append(averagemidgame(i)) #average score in midgame
		game.append(scoremidgame(i)) #score at/near end of midgame
		game.append(averageendgame(i)) #average score in endgame
		game.append(lastscore(i)) #score of last white move at end of the game

		game.append(totalscore(i)) #gets total change in score

		game.append(averagescorechange(i)) #average amount the score changes per move
		game.append(minimumscore(i)) #minimum score in the game
		game.append(maximumscore(i)) #maximum score in the game
		game.append(scoreswitch(i)) #counts number of times who is ahead changes
		validation_features.append(game)
	validation_labels_w = getLabels(validationscored,WHITE)
	validation_labels_b = getLabels(validationscored,BLACK)

	print("Running KNN")
	y_w = forest(training_features,training_labels_w,validation_features)
	y_b = forest(training_features,training_labels_b,validation_features)

	print("Calculating Error")
	error_w = meanError(validation_labels_w,y_w)
	error_b = meanError(validation_labels_b,y_b)
	error_t = (error_b+error_w)/2 #mean

	print(str(error_w) + " White error")
	print(str(error_b) + " Black error")
	print(str(error_t) + " Total error")
	return

def knnScores():
	#use knn using the scores as features
	#parses into 2 groups, training data, validation data
	#PARSING TIME
	
	parser = Parser()
	print("PARSING")
	games = parser.read_uci(sys.argv[1])
	scored = parser.parseStockfish(games,sys.argv[2])

	validationgames = parser.read_uci(sys.argv[3])
	validationscored = parser.parseStockfish(validationgames,sys.argv[4])

	print("Building Features/Labels")
	#Now I'm going to run KNN which is going to return y_
	training_features = []
	#finding longest game
	longest = 0
	for i in scored:
		if len(i.turns) > longest:
			longest = len(i.turns)
	for i in validationscored:
		if len(i.turns) > longest:
			longest = len(i.turns)
	#have longest game
	for i in scored:
		game = []
		for j in range(len(i.turns)):
			game.append(i.turns[j].moves[0].rating)
			game.append(i.turns[j].moves[1].rating)
		for k in range(longest):
			if k < j:
				continue
			game.append(0)
			game.append(0)
		training_features.append(game)

	training_labels_w = getLabels(scored,WHITE)
	training_labels_b = getLabels(scored,BLACK)

	validation_features = []

	for i in validationscored:
		game = []
		for j in range(len(i.turns)):
			game.append(i.turns[j].moves[0].rating)
			game.append(i.turns[j].moves[1].rating)
		for k in range(longest):
			if k < j:
				continue
			game.append(0)
			game.append(0)
		validation_features.append(game)
	validation_labels_w = getLabels(validationscored,WHITE)
	validation_labels_b = getLabels(validationscored,BLACK)

	print("Running KNN")
	y_w = knn(training_features,training_labels_w,validation_features)
	y_b = knn(training_features,training_labels_b,validation_features)

	print("Calculating Error")
	error_w = meanError(validation_labels_w,y_w)
	error_b = meanError(validation_labels_b,y_b)
	error_t = (error_b+error_w)/2 #mean

	print(str(error_w) + " White error")
	print(str(error_b) + " Black error")
	print(str(error_t) + " Total error")
	return

def knnMovesAll():
	#use knn using the moves and other features
	#parses into 2 groups, training data, validation data
	#PARSING TIME
	
	parser = Parser()
	print("PARSING")
	games = parser.read_uci(sys.argv[1])
	scored = parser.parseStockfish(games,sys.argv[2])

	validationgames = parser.read_uci(sys.argv[3])
	validationscored = parser.parseStockfish(validationgames,sys.argv[4])

	print("Building Features/Labels")
	#Now I'm going to run KNN which is going to return y_
	training_features = []
	#finding longest game
	longest = 0
	for i in scored:
		if len(i.turns) > longest:
			longest = len(i.turns)
	for i in validationscored:
		if len(i.turns) > longest:
			longest = len(i.turns)
	#have longest game
	for i in scored:
		game = []
		for j in range(len(i.turns)):
			game.append(i.turns[j].moves[0].uci)
			game.append(i.turns[j].moves[1].uci)
		for k in range(longest):
			if k < j:
				continue
			game.append(0)
			game.append(0)
		game.append(numturns(i)) #number of turns in the game
		game.append(averagescore(i)) #average score
		game.append(numlosingturns(i)) #% of game where white is ahead
		game.append(averageopening(i)) # average score in opening
		game.append(scoreopening(i)) #score at end of opening
		game.append(averagemidgame(i)) #average score in midgame
		game.append(scoremidgame(i)) #score at/near end of midgame
		game.append(averageendgame(i)) #average score in endgame
		game.append(lastscore(i)) #score of last white move at end of the game

		game.append(totalscore(i)) #gets total change in score

		game.append(averagescorechange(i)) #average amount the score changes per move
		game.append(minimumscore(i)) #minimum score in the game
		game.append(maximumscore(i)) #maximum score in the game
		game.append(scoreswitch(i)) #counts number of times who is ahead changes
		training_features.append(game)

	training_labels_w = getLabels(scored,WHITE)
	training_labels_b = getLabels(scored,BLACK)

	validation_features = []

	for i in validationscored:
		game = []
		for j in range(len(i.turns)):
			game.append(i.turns[j].moves[0].uci)
			game.append(i.turns[j].moves[1].uci)
		for k in range(longest):
			if k < j:
				continue
			game.append(0)
			game.append(0)
		game.append(numturns(i)) #number of turns in the game
		game.append(averagescore(i)) #average score
		game.append(numlosingturns(i)) #% of game where white is ahead
		game.append(averageopening(i)) # average score in opening
		game.append(scoreopening(i)) #score at end of opening
		game.append(averagemidgame(i)) #average score in midgame
		game.append(scoremidgame(i)) #score at/near end of midgame
		game.append(averageendgame(i)) #average score in endgame
		game.append(lastscore(i)) #score of last white move at end of the game

		game.append(totalscore(i)) #gets total change in score

		game.append(averagescorechange(i)) #average amount the score changes per move
		game.append(minimumscore(i)) #minimum score in the game
		game.append(maximumscore(i)) #maximum score in the game
		game.append(scoreswitch(i)) #counts number of times who is ahead changes
		validation_features.append(game)
	validation_labels_w = getLabels(validationscored,WHITE)
	validation_labels_b = getLabels(validationscored,BLACK)

	print("Running KNN")
	y_w = knn(training_features,training_labels_w,validation_features)
	y_b = knn(training_features,training_labels_b,validation_features)

	print("Calculating Error")
	error_w = meanError(validation_labels_w,y_w)
	error_b = meanError(validation_labels_b,y_b)
	error_t = (error_b+error_w)/2 #mean

	print(str(error_w) + " White error")
	print(str(error_b) + " Black error")
	print(str(error_t) + " Total error")
	return

def knnMoves():
	#use knn using just the moves as features
	#parses into 2 groups, training data, validation data
	#PARSING TIME
	
	parser = Parser()
	print("PARSING")
	games = parser.read_uci(sys.argv[1])
	scored = parser.parseStockfish(games,sys.argv[2])

	validationgames = parser.read_uci(sys.argv[3])
	validationscored = parser.parseStockfish(validationgames,sys.argv[4])

	print("Building Features/Labels")
	#Now I'm going to run KNN which is going to return y_
	training_features = []
	#finding longest game
	longest = 0
	for i in scored:
		if len(i.turns) > longest:
			longest = len(i.turns)
	for i in validationscored:
		if len(i.turns) > longest:
			longest = len(i.turns)
	#have longest game
	for i in scored:
		game = []
		for j in range(len(i.turns)):
			game.append(i.turns[j].moves[0].uci)
			game.append(i.turns[j].moves[1].uci)
		for k in range(longest):
			if k < j:
				continue
			game.append(0)
			game.append(0)
		training_features.append(game)

	training_labels_w = getLabels(scored,WHITE)
	training_labels_b = getLabels(scored,BLACK)

	validation_features = []

	for i in validationscored:
		game = []
		for j in range(len(i.turns)):
			game.append(i.turns[j].moves[0].uci)
			game.append(i.turns[j].moves[1].uci)
		for k in range(longest):
			if k < j:
				continue
			game.append(0)
			game.append(0)
		validation_features.append(game)
	validation_labels_w = getLabels(validationscored,WHITE)
	validation_labels_b = getLabels(validationscored,BLACK)

	print("Running KNN")
	y_w = knn(training_features,training_labels_w,validation_features)
	y_b = knn(training_features,training_labels_b,validation_features)

	print("Calculating Error")
	error_w = meanError(validation_labels_w,y_w)
	error_b = meanError(validation_labels_b,y_b)
	error_t = (error_b+error_w)/2 #mean

	print(str(error_w) + " White error")
	print(str(error_b) + " Black error")
	print(str(error_t) + " Total error")
	return

def findPartitions():
	#main function to find optimal splits for opening/midgame/endgame
	global ENDGAME
	global MIDGAME
	global OPENING

	parser = Parser()
	print("PARSING")
	games = parser.read_uci(sys.argv[1])
	scored = parser.parseStockfish(games,sys.argv[2])

	validationgames = parser.read_uci(sys.argv[3])
	validationscored = parser.parseStockfish(validationgames,sys.argv[4])

	#Now I'm going to run KNN which is going to return y_
	training_labels_w = getLabels(scored,WHITE)
	training_labels_b = getLabels(scored,BLACK)

	validation_labels_w = getLabels(validationscored,WHITE)
	validation_labels_b = getLabels(validationscored,BLACK)

	minscore = 10000
	for i in range(10):
		for j in range(10-i):
			OPENING = float(i)/10
			MIDGAME = float(j)/10
			ENDGAME = float(10 - i - j)/10
			print(OPENING,MIDGAME,ENDGAME)
			training_features = set1(scored)
			validation_features = set1(validationscored)


			y_w = knn(training_features,training_labels_w,validation_features)
			y_b = knn(training_features,training_labels_b,validation_features)


			error_w = meanError(validation_labels_w,y_w)
			error_b = meanError(validation_labels_b,y_b)
			error_t = (error_b+error_w)/2 #mean
			st = "Got score of " + str(error_t) + " with " + str(i) + " " + str(j) + " " + str(10-i-j)
			if error_t < minscore:
				minscore = error_t
				print(st)
			o.write(st+"\n")
	o.close()

def testFeatures():
	parser = Parser()
	games = parser.read_uci(sys.argv[3])
	validationscored = parser.parseStockfish(games,sys.argv[4])
	print('num turns '+str(numturns(validationscored[0])))
	averageopening(validationscored[0])
	averagemidgame(validationscored[0])
	averageendgame(validationscored[0])


def benchmark():
	parser = Parser()
	games = parser.read_uci(sys.argv[3])
	scored = parser.parseStockfish(games,sys.argv[4])

	labels = getLabels(scored,WHITE)
	labels2 = getLabels(scored,BLACK)


	y_ = []
	for i in labels:
		y_.append(1000)

	print("BENCHMARK VALIDATION DATA: " + str((meanError(labels,y_)+meanError(labels2,y_))/2))


def overnight():
	global OPENING
	global ENDGAME
	global MIDGAME
	costofthisprogrambecomingskynet = 999999999999999999999
	parser = Parser()
	games = parser.read_uci(sys.argv[1])
	scored = parser.parseStockfish(games,sys.argv[2])

	validationgames = parser.read_uci(sys.argv[3])
	validationscored = parser.parseStockfish(validationgames,sys.argv[4])

	training_features = set2(scored)
	training_labels_w = getLabels(scored,WHITE)
	training_labels_b = getLabels(scored,BLACK)

	validation_features = set2(validationscored)
	validation_labels_w = getLabels(validationscored,WHITE)
	validation_labels_b = getLabels(validationscored,BLACK)

	f = open("knnpartition","w")
	try:
		#opening/endgame/midgame for each model
		minscore = 10000
		for i in range(10):
			for j in range(10-i):
				OPENING = float(i)/10
				MIDGAME = float(j)/10
				ENDGAME = float(10 - i - j)/10
				print(OPENING,MIDGAME,ENDGAME)
				training_features = set2(scored)
				validation_features = set2(validationscored)


				y_w = knn(training_features,training_labels_w,validation_features)
				y_b = knn(training_features,training_labels_b,validation_features)


				error_w = meanError(validation_labels_w,y_w)
				error_b = meanError(validation_labels_b,y_b)
				error_t = (error_b+error_w)/2 #mean
				st = "Got score of " + str(error_t) + " with " + str(i) + " " + str(j) + " " + str(10-i-j)
				if error_t < minscore:
					minscore = error_t
					print(st)
				f.write(st+"\n")
		f.close()
	except:
		f.close()

	f = open("lrpartition","w")
	try:
		#opening/endgame/midgame for each model
		minscore = 10000
		for i in range(10):
			for j in range(10-i):
				OPENING = float(i)/10
				MIDGAME = float(j)/10
				ENDGAME = float(10 - i - j)/10
				print(OPENING,MIDGAME,ENDGAME)
				training_features = set2(scored)
				validation_features = set2(validationscored)


				y_w = lr(training_features,training_labels_w,validation_features)
				y_b = lr(training_features,training_labels_b,validation_features)


				error_w = meanError(validation_labels_w,y_w)
				error_b = meanError(validation_labels_b,y_b)
				error_t = (error_b+error_w)/2 #mean
				st = "Got score of " + str(error_t) + " with " + str(i) + " " + str(j) + " " + str(10-i-j)
				if error_t < minscore:
					minscore = error_t
					print(st)
				f.write(st+"\n")
		f.close()
	except:
		f.close()

	f = open("treepartition","w")
	try:
		#opening/endgame/midgame for each model
		minscore = 10000
		for i in range(10):
			for j in range(10-i):
				OPENING = float(i)/10
				MIDGAME = float(j)/10
				ENDGAME = float(10 - i - j)/10
				print(OPENING,MIDGAME,ENDGAME)
				training_features = set2(scored)
				validation_features = set2(validationscored)


				y_w = tree(training_features,training_labels_w,validation_features)
				y_b = tree(training_features,training_labels_b,validation_features)


				error_w = meanError(validation_labels_w,y_w)
				error_b = meanError(validation_labels_b,y_b)
				error_t = (error_b+error_w)/2 #mean
				st = "Got score of " + str(error_t) + " with " + str(i) + " " + str(j) + " " + str(10-i-j)
				if error_t < minscore:
					minscore = error_t
					print(st)
				f.write(st+"\n")
		f.close()
	except:
		f.close()

	f = open("forestpartition","w")
	try:
		#opening/endgame/midgame for each model
		minscore = 10000
		for i in range(10):
			for j in range(10-i):
				OPENING = float(i)/10
				MIDGAME = float(j)/10
				ENDGAME = float(10 - i - j)/10
				print(OPENING,MIDGAME,ENDGAME)
				training_features = set2(scored)
				validation_features = set2(validationscored)


				y_w = forest(training_features,training_labels_w,validation_features)
				y_b = forest(training_features,training_labels_b,validation_features)


				error_w = meanError(validation_labels_w,y_w)
				error_b = meanError(validation_labels_b,y_b)
				error_t = (error_b+error_w)/2 #mean
				st = "Got score of " + str(error_t) + " with " + str(i) + " " + str(j) + " " + str(10-i-j)
				if error_t < minscore:
					minscore = error_t
					print(st)
				f.write(st+"\n")
		f.close()
	except:
		f.close()


	OPENING = 0.4
	MIDGAME = 0.3
	ENDGAME = 0.3
	training_features = set2(scored)
	validation_features = set2(validationscored)

	f = open("knnoverfit","w")
	for i in range(100):
		try:
			y_w = knnO(training_features,training_labels_w,validation_features,i)
			y_b = knnO(training_features,training_labels_b,validation_features,i)


			error_w = meanError(validation_labels_w,y_w)
			error_b = meanError(validation_labels_b,y_b)
			error_t = (error_b+error_w)/2 #mean
			st = "Got score of " + str(error_t) + " with " + str(i)
			f.write(st+"\n")
		except:
			pass
	f.close()

	f = open("treeoverfit","w")
	for i in range(100):
		try:
			y_w = treeO(training_features,training_labels_w,validation_features,i)
			y_b = treeO(training_features,training_labels_b,validation_features,i)


			error_w = meanError(validation_labels_w,y_w)
			error_b = meanError(validation_labels_b,y_b)
			error_t = (error_b+error_w)/2 #mean
			st = "Got score of " + str(error_t) + " with " + str(i)
			f.write(st+"\n")
		except:
			pass
	f.close()			

	f = open("forestoverfit","w")
	for i in range(100):
		try:
			y_w = forestO(training_features,training_labels_w,validation_features,i)
			y_b = forestO(training_features,training_labels_b,validation_features,i)

			error_w = meanError(validation_labels_w,y_w)
			error_b = meanError(validation_labels_b,y_b)
			error_t = (error_b+error_w)/2 #mean
			st = "Got score of " + str(error_t) + " with " + str(i)
			f.write(st+"\n")
		except:
			pass
	f.close()	

	f = open("knnoverfit2","w")
	try:
		i = 500

		y_w = knnO(training_features,training_labels_w,validation_features,i)
		y_b = knnO(training_features,training_labels_b,validation_features,i)


		error_w = meanError(validation_labels_w,y_w)
		error_b = meanError(validation_labels_b,y_b)
		error_t = (error_b+error_w)/2 #mean
		st = "Got score of " + str(error_t) + " with " + str(i)
		f.write(st+"\n")

		i = 1000

		y_w = knnO(training_features,training_labels_w,validation_features,i)
		y_b = knnO(training_features,training_labels_b,validation_features,i)


		error_w = meanError(validation_labels_w,y_w)
		error_b = meanError(validation_labels_b,y_b)
		error_t = (error_b+error_w)/2 #mean
		st = "Got score of " + str(error_t) + " with " + str(i)
		f.write(st+"\n")

		i = 3000

		y_w = knnO(training_features,training_labels_w,validation_features,i)
		y_b = knnO(training_features,training_labels_b,validation_features,i)


		error_w = meanError(validation_labels_w,y_w)
		error_b = meanError(validation_labels_b,y_b)
		error_t = (error_b+error_w)/2 #mean
		st = "Got score of " + str(error_t) + " with " + str(i)
		f.write(st+"\n")

		i = 4500

		y_w = knnO(training_features,training_labels_w,validation_features,i)
		y_b = knnO(training_features,training_labels_b,validation_features,i)


		error_w = meanError(validation_labels_w,y_w)
		error_b = meanError(validation_labels_b,y_b)
		error_t = (error_b+error_w)/2 #mean
		st = "Got score of " + str(error_t) + " with " + str(i)
		f.write(st+"\n")
	except:
		pass
	f.close()	

	f = open("forestoverfit2","w")
	try:
		i = 500

		y_w = forestO(training_features,training_labels_w,validation_features,i)
		y_b = forestO(training_features,training_labels_b,validation_features,i)


		error_w = meanError(validation_labels_w,y_w)
		error_b = meanError(validation_labels_b,y_b)
		error_t = (error_b+error_w)/2 #mean
		st = "Got score of " + str(error_t) + " with " + str(i)
		f.write(st+"\n")

		i = 1000

		y_w = forestO(training_features,training_labels_w,validation_features,i)
		y_b = forestO(training_features,training_labels_b,validation_features,i)


		error_w = meanError(validation_labels_w,y_w)
		error_b = meanError(validation_labels_b,y_b)
		error_t = (error_b+error_w)/2 #mean
		st = "Got score of " + str(error_t) + " with " + str(i)
		f.write(st+"\n")

		i = 3000

		y_w = forestO(training_features,training_labels_w,validation_features,i)
		y_b = forestO(training_features,training_labels_b,validation_features,i)


		error_w = meanError(validation_labels_w,y_w)
		error_b = meanError(validation_labels_b,y_b)
		error_t = (error_b+error_w)/2 #mean
		st = "Got score of " + str(error_t) + " with " + str(i)
		f.write(st+"\n")

		i = 4500

		y_w = forestO(training_features,training_labels_w,validation_features,i)
		y_b = forestO(training_features,training_labels_b,validation_features,i)


		error_w = meanError(validation_labels_w,y_w)
		error_b = meanError(validation_labels_b,y_b)
		error_t = (error_b+error_w)/2 #mean
		st = "Got score of " + str(error_t) + " with " + str(i)
		f.write(st+"\n")
	except:
		pass
	f.close()	

	f = open("treeoverfit2","w")
	try:
		i = 500

		y_w = treeO(training_features,training_labels_w,validation_features,i)
		y_b = treeO(training_features,training_labels_b,validation_features,i)


		error_w = meanError(validation_labels_w,y_w)
		error_b = meanError(validation_labels_b,y_b)
		error_t = (error_b+error_w)/2 #mean
		st = "Got score of " + str(error_t) + " with " + str(i)
		f.write(st+"\n")

		i = 1000

		y_w = treeO(training_features,training_labels_w,validation_features,i)
		y_b = treeO(training_features,training_labels_b,validation_features,i)


		error_w = meanError(validation_labels_w,y_w)
		error_b = meanError(validation_labels_b,y_b)
		error_t = (error_b+error_w)/2 #mean
		st = "Got score of " + str(error_t) + " with " + str(i)
		f.write(st+"\n")

		i = 3000

		y_w = treeO(training_features,training_labels_w,validation_features,i)
		y_b = treeO(training_features,training_labels_b,validation_features,i)


		error_w = meanError(validation_labels_w,y_w)
		error_b = meanError(validation_labels_b,y_b)
		error_t = (error_b+error_w)/2 #mean
		st = "Got score of " + str(error_t) + " with " + str(i)
		f.write(st+"\n")

		i = 4500

		y_w = treeO(training_features,training_labels_w,validation_features,i)
		y_b = treeO(training_features,training_labels_b,validation_features,i)


		error_w = meanError(validation_labels_w,y_w)
		error_b = meanError(validation_labels_b,y_b)
		error_t = (error_b+error_w)/2 #mean
		st = "Got score of " + str(error_t) + " with " + str(i)
		f.write(st+"\n")
	except:
		pass
	f.close()	

	i = 101

	f = open("lastoverfits","w")
	while 1:
		i+=2
		try:
			y_w = knnO(training_features,training_labels_w,validation_features,i)
			y_b = knnO(training_features,training_labels_b,validation_features,i)


			error_w = meanError(validation_labels_w,y_w)
			error_b = meanError(validation_labels_b,y_b)
			error_t = (error_b+error_w)/2 #mean
			st = "Got score of " + str(error_t) + " with " + str(i) + " knn"
			f.write(st+"\n")

			y_w = forestO(training_features,training_labels_w,validation_features,i)
			y_b = forestO(training_features,training_labels_b,validation_features,i)


			error_w = meanError(validation_labels_w,y_w)
			error_b = meanError(validation_labels_b,y_b)
			error_t = (error_b+error_w)/2 #mean
			st = "Got score of " + str(error_t) + " with " + str(i) + " tree"
			f.write(st+"\n")

			y_w = forestO(training_features,training_labels_w,validation_features,i)
			y_b = forestO(training_features,training_labels_b,validation_features,i)


			error_w = meanError(validation_labels_w,y_w)
			error_b = meanError(validation_labels_b,y_b)
			error_t = (error_b+error_w)/2 #mean
			st = "Got score of " + str(error_t) + " with " + str(i) + " forest"
			f.write(st+"\n")
		except:
			pass
	f.close


def knnOverfit():
	global OPENING
	global ENDGAME
	global MIDGAME
	costofthisprogrambecomingskynet = 999999999999999999999
	parser = Parser()
	games = parser.read_uci(sys.argv[1])
	scored = parser.parseStockfish(games,sys.argv[2])

	validationgames = parser.read_uci(sys.argv[3])
	validationscored = parser.parseStockfish(validationgames,sys.argv[4])

	training_features = set2(scored)
	training_labels_w = getLabels(scored,WHITE)
	training_labels_b = getLabels(scored,BLACK)

	validation_features = set2(validationscored)
	validation_labels_w = getLabels(validationscored,WHITE)
	validation_labels_b = getLabels(validationscored,BLACK)


	f = open("forestoverfit3","w")
	for i in range(500):
		try:
			if i < 90:
				continue
			if i % 100 == 0:
				continue

			y_w = forestO(training_features,training_labels_w,validation_features,i)
			y_b = forestO(training_features,training_labels_b,validation_features,i)


			error_w = meanError(validation_labels_w,y_w)
			error_b = meanError(validation_labels_b,y_b)
			error_t = (error_b+error_w)/2 #mean
			st = "Got score of " + str(error_t) + " with " + str(i)
			f.write(st+"\n")

		except:
			pass
	f.close()	


def main():
	#I guess this can be my main thing
	
	#parses into 2 groups, training data, validation data
	#PARSING TIME
	
	parser = Parser()
	print("PARSING")
	games = parser.read_uci(sys.argv[1])
	scored = parser.parseStockfish(games,sys.argv[2])

	validationgames = parser.read_uci(sys.argv[3])
	validationscored = parser.parseStockfish(validationgames,sys.argv[4])

	print("Building Features/Labels")
	#Now I'm going to run KNN which is going to return y_
	training_features = set2(scored)
	training_labels_w = getLabels(scored,WHITE)
	training_labels_b = getLabels(scored,BLACK)

	validation_features = set2(validationscored)
	validation_labels_w = getLabels(validationscored,WHITE)
	validation_labels_b = getLabels(validationscored,BLACK)

	print("Running LR")
	y_w = knn(training_features,training_labels_w,validation_features)
	y_b = knn(training_features,training_labels_b,validation_features)

	print("Calculating Error")
	error_w = meanError(validation_labels_w,y_w)
	error_b = meanError(validation_labels_b,y_b)
	error_t = (error_b+error_w)/2 #mean

	print(str(error_w) + " White error")
	print(str(error_b) + " Black error")
	print(str(error_t) + " Total error")

def main6Scores():
	#6 models, all trained separately, use the right one based on the result, with the scores inc
	#P White ELO white wins
	#P White ELO black wins
	#P Black ELO white wins
	#P Black ELO black wins
	#P White ELO draw
	#P Black ELO draw
	#
	parser = Parser()
	print("Parsing")
	games = parser.read_uci(sys.argv[1])
	scored = parser.parseStockfish(games,sys.argv[2])

	validationgames = parser.read_uci(sys.argv[3])
	validationscored = parser.parseStockfish(validationgames,sys.argv[4])

	whitewins = []
	ww_n = []
	blackwins = []
	bw_n = []
	draw = []
	d_n = []
	for z in scored:
		if z.result == WHITE:
			whitewins.append(z)
			ww_n.append(z.number)
		elif z.result == BLACK:
			blackwins.append(z)
			bw_n.append(z.number)
		else:
			draw.append(z)
			d_n.append(z.number)
	if (len(whitewins)+len(blackwins)+len(draw)) != len(scored):
		raise Exception("We Have a Problem")

	v_whitewins = []
	v_ww_n = []
	v_blackwins = []
	v_bw_n = []
	v_draw = []
	v_d_n = []
	for x in validationscored:
		if x.result == WHITE:
			v_whitewins.append(x)
			v_ww_n.append(x.number)
		elif x.result == BLACK:
			v_blackwins.append(x)
			v_bw_n.append(x.number)
		else:
			v_draw.append(x)
			v_d_n.append(x.number)
	if (len(v_whitewins)+len(v_blackwins)+len(v_draw))  != len(validationscored):
		raise Exception("VAlidation problem")


	print("Getting Features")
	#finding longest game
	longest_w = 0
	for i in whitewins:
		if len(i.turns) > longest_w:
			longest_w = len(i.turns)
	for i in v_whitewins:
		if len(i.turns) > longest_w:
			longest_w = len(i.turns)
	training_features_w = [] #white wins
	for i in whitewins:
		game = []
		for j in range(len(i.turns)):
			try:
				game.append(i.turns[j].moves[0].rating)
			except:
				pass
			try:
				game.append(i.turns[j].moves[1].rating)
			except:
				pass
		for k in range(longest_w):
			if k < j:
				continue
			game.append(0)
			game.append(0)

		game.append(numturns(i)) #number of turns in the game
		game.append(averagescore(i)) #average score
		game.append(numlosingturns(i)) #% of game where white is ahead
		game.append(averageopening(i)) # average score in opening
		game.append(scoreopening(i)) #score at end of opening
		game.append(averagemidgame(i)) #average score in midgame
		game.append(scoremidgame(i)) #score at/near end of midgame
		game.append(averageendgame(i)) #average score in endgame
		game.append(lastscore(i)) #score of last white move at end of the game

		game.append(totalscore(i)) #gets total change in score

		game.append(averagescorechange(i)) #average amount the score changes per move
		game.append(minimumscore(i)) #minimum score in the game
		game.append(maximumscore(i)) #maximum score in the game
		game.append(scoreswitch(i)) #counts number of times who is ahead changes
		training_features_w.append(game)
	#finding longest game
	longest_b = 0
	for i in blackwins:
		if len(i.turns) > longest_b:
			longest_b = len(i.turns)
	for i in v_blackwins:
		if len(i.turns) > longest_b:
			longest_b = len(i.turns)
	training_features_b = []
	for i in blackwins:
		game = []
		for j in range(len(i.turns)):
			try:
				game.append(i.turns[j].moves[0].rating)*-1
			except:
				pass
			try:
				game.append(i.turns[j].moves[1].rating)*-1
			except:
				pass
		for k in range(longest_b):
			if k < j:
				continue
			game.append(0)
			game.append(0)
		game.append(numturns(i)) #number of turns in the game
		game.append(averagescore(i)) #average score
		game.append(numlosingturns(i)) #% of game where white is ahead
		game.append(averageopening(i)) # average score in opening
		game.append(scoreopening(i)) #score at end of opening
		game.append(averagemidgame(i)) #average score in midgame
		game.append(scoremidgame(i)) #score at/near end of midgame
		game.append(averageendgame(i)) #average score in endgame
		game.append(lastscore(i)) #score of last white move at end of the game

		game.append(totalscore(i)) #gets total change in score

		game.append(averagescorechange(i)) #average amount the score changes per move
		game.append(minimumscore(i)) #minimum score in the game
		game.append(maximumscore(i)) #maximum score in the game
		game.append(scoreswitch(i)) #counts number of times who is ahead changes
		training_features_b.append(game)
	#finding longest game
	longest_d = 0
	for i in draw:
		if len(i.turns) > longest_d:
			longest_d = len(i.turns)
	for i in v_draw:
		if len(i.turns) > longest_d:
			longest_d = len(i.turns)
	training_features_d = []
	for i in draw:
		game = []
		for j in range(len(i.turns)):
			try:
				game.append(i.turns[j].moves[0].rating)*-1
			except:
				pass
			try:
				game.append(i.turns[j].moves[1].rating)*-1
			except:
				pass
		for k in range(longest_d):
			if k < j:
				continue
			game.append(0)
			game.append(0)
		game.append(numturns(i)) #number of turns in the game
		game.append(averagescore(i)) #average score
		game.append(numlosingturns(i)) #% of game where white is ahead
		game.append(averageopening(i)) # average score in opening
		game.append(scoreopening(i)) #score at end of opening
		game.append(averagemidgame(i)) #average score in midgame
		game.append(scoremidgame(i)) #score at/near end of midgame
		game.append(averageendgame(i)) #average score in endgame
		game.append(lastscore(i)) #score of last white move at end of the game

		game.append(totalscore(i)) #gets total change in score

		game.append(averagescorechange(i)) #average amount the score changes per move
		game.append(minimumscore(i)) #minimum score in the game
		game.append(maximumscore(i)) #maximum score in the game
		game.append(scoreswitch(i)) #counts number of times who is ahead changes
		training_features_d.append(game)

	training_labels_w_w = getLabels(whitewins,WHITE)
	training_labels_b_w = getLabels(whitewins,BLACK)
	training_labels_w_b = getLabels(blackwins,WHITE)
	training_labels_b_b = getLabels(blackwins,BLACK)
	training_labels_w_d = getLabels(draw,WHITE)
	training_labels_b_d = getLabels(draw,BLACK)

	v_features_w = []
	for i in v_whitewins:
		game = []
		for j in range(len(i.turns)):
			try:
				game.append(i.turns[j].moves[0].rating)*-1
			except:
				pass
			try:
				game.append(i.turns[j].moves[1].rating)*-1
			except:
				pass
		for k in range(longest_w):
			if k < j:
				continue
			game.append(0)
			game.append(0)
		game.append(numturns(i)) #number of turns in the game
		game.append(averagescore(i)) #average score
		game.append(numlosingturns(i)) #% of game where white is ahead
		game.append(averageopening(i)) # average score in opening
		game.append(scoreopening(i)) #score at end of opening
		game.append(averagemidgame(i)) #average score in midgame
		game.append(scoremidgame(i)) #score at/near end of midgame
		game.append(averageendgame(i)) #average score in endgame
		game.append(lastscore(i)) #score of last white move at end of the game

		game.append(totalscore(i)) #gets total change in score

		game.append(averagescorechange(i)) #average amount the score changes per move
		game.append(minimumscore(i)) #minimum score in the game
		game.append(maximumscore(i)) #maximum score in the game
		game.append(scoreswitch(i)) #counts number of times who is ahead changes
		v_features_w.append(game)
	v_features_b = []
	for i in v_blackwins:
		game = []
		for j in range(len(i.turns)):
			try:
				game.append(i.turns[j].moves[0].rating)*-1
			except:
				pass
			try:
				game.append(i.turns[j].moves[1].rating)*-1
			except:
				pass
		for k in range(longest_b):
			if k < j:
				continue
			game.append(0)
			game.append(0)
		game.append(numturns(i)) #number of turns in the game
		game.append(averagescore(i)) #average score
		game.append(numlosingturns(i)) #% of game where white is ahead
		game.append(averageopening(i)) # average score in opening
		game.append(scoreopening(i)) #score at end of opening
		game.append(averagemidgame(i)) #average score in midgame
		game.append(scoremidgame(i)) #score at/near end of midgame
		game.append(averageendgame(i)) #average score in endgame
		game.append(lastscore(i)) #score of last white move at end of the game

		game.append(totalscore(i)) #gets total change in score

		game.append(averagescorechange(i)) #average amount the score changes per move
		game.append(minimumscore(i)) #minimum score in the game
		game.append(maximumscore(i)) #maximum score in the game
		game.append(scoreswitch(i)) #counts number of times who is ahead changes
		v_features_b.append(game)
	v_features_d = []
	for i in v_draw:
		game = []
		for j in range(len(i.turns)):
			try:
				game.append(i.turns[j].moves[0].rating)*-1
			except:
				pass
			try:
				game.append(i.turns[j].moves[1].rating)*-1
			except:
				pass
		for k in range(longest_d):
			if k < j:
				continue
			game.append(0)
			game.append(0)
		game.append(numturns(i)) #number of turns in the game
		game.append(averagescore(i)) #average score
		game.append(numlosingturns(i)) #% of game where white is ahead
		game.append(averageopening(i)) # average score in opening
		game.append(scoreopening(i)) #score at end of opening
		game.append(averagemidgame(i)) #average score in midgame
		game.append(scoremidgame(i)) #score at/near end of midgame
		game.append(averageendgame(i)) #average score in endgame
		game.append(lastscore(i)) #score of last white move at end of the game

		game.append(totalscore(i)) #gets total change in score

		game.append(averagescorechange(i)) #average amount the score changes per move
		game.append(minimumscore(i)) #minimum score in the game
		game.append(maximumscore(i)) #maximum score in the game
		game.append(scoreswitch(i)) #counts number of times who is ahead changes
		v_features_d.append(game)

	if (len(whitewins)+len(blackwins)+len(draw)) != len(scored):
		raise Exception("We Have a Problem")
	if (len(v_whitewins)+len(v_blackwins)+len(v_draw))  != len(validationscored):
		raise Exception("VAlidation problem")

	v_labels_w_w = getLabels(v_whitewins,WHITE)
	v_labels_b_w = getLabels(v_whitewins,BLACK)
	v_labels_w_b = getLabels(v_blackwins,WHITE)
	v_labels_b_b = getLabels(v_blackwins,BLACK)
	v_labels_w_d = getLabels(v_draw,WHITE)
	v_labels_b_d = getLabels(v_draw,BLACK)

	print("Running Alg")
	y_w_w = ensemble5(training_features_w,training_labels_w_w,v_features_w)
	print("ww")
	y_b_w = ensemble5(training_features_w,training_labels_b_w,v_features_w)
	print("bw")
	y_w_b = ensemble5(training_features_b,training_labels_w_b,v_features_b)
	print("wb")
	y_b_b = ensemble5(training_features_b,training_labels_b_b,v_features_b)
	print("bb")
	y_w_d = ensemble5(training_features_d,training_labels_w_d,v_features_d)
	print("wd")
	y_b_d = ensemble5(training_features_d,training_labels_b_d,v_features_d)
	print("bd")

	#toKaggle(y_w_w,y_b_w,y_w_b,y_b_b,y_w_d,y_b_d,v_ww_n,v_bw_n,v_d_n)

	print("Calculating Error")
	error_w_w = meanError(v_labels_w_w,y_w_w)
	error_b_w = meanError(v_labels_b_w,y_b_w)
	error_w_b = meanError(v_labels_w_b,y_w_b)
	error_b_b = meanError(v_labels_b_b,y_b_b)
	error_w_d = meanError(v_labels_w_d,y_w_d)
	error_b_d = meanError(v_labels_b_d,y_b_d)
	error_t = error_w_w+error_b_w+error_w_b+error_b_b+error_w_d+error_b_d
	error_a = error_t/6

	print(str(error_w_w) + " White Wins White error")
	print(str(error_b_w) + " White Wins Black error")
	print(str(error_w_b) + " Black Wins White error")
	print(str(error_b_b) + " Black Wins Black error")
	print(str(error_w_d) + " Draw White error")
	print(str(error_b_d) + " Draw Black error")

	print(str(error_a) + " Mean error")

def main6():
	#6 models, all trained separately, use the right one based on the result
	#P White ELO white wins
	#P White ELO black wins
	#P Black ELO white wins
	#P Black ELO black wins
	#P White ELO draw
	#P Black ELO draw
	#
	parser = Parser()
	print("Parsing")
	games = parser.read_uci(sys.argv[1])
	scored = parser.parseStockfish(games,sys.argv[2])

	validationgames = parser.read_uci(sys.argv[3])
	validationscored = parser.parseStockfish(validationgames,sys.argv[4])

	whitewins = []
	blackwins = []
	draw = []
	for z in scored:
		if z.result == WHITE:
			whitewins.append(z)
		elif z.result == BLACK:
			blackwins.append(z)
		else:
			draw.append(z)
	if (len(whitewins)+len(blackwins)+len(draw)) != len(scored):
		raise Exception("We Have a Problem")

	v_whitewins = []
	v_blackwins = []
	v_draw = []
	for x in validationscored:
		if x.result == WHITE:
			v_whitewins.append(x)
		elif x.result == BLACK:
			v_blackwins.append(x)
		else:
			v_draw.append(x)
	if (len(v_whitewins)+len(v_blackwins)+len(v_draw))  != len(validationscored):
		raise Exception("VAlidation problem")

	print("Getting Features")
	training_features_w = set2(whitewins) #white wins
	training_features_b = set2(blackwins)
	training_features_d = set2(draw)

	training_labels_w_w = getLabels(whitewins,WHITE)
	training_labels_b_w = getLabels(whitewins,BLACK)
	training_labels_w_b = getLabels(blackwins,WHITE)
	training_labels_b_b = getLabels(blackwins,BLACK)
	training_labels_w_d = getLabels(draw,WHITE)
	training_labels_b_d = getLabels(draw,BLACK)

	v_features_w = set2(v_whitewins)
	v_features_b = set2(v_blackwins)
	v_features_d = set2(v_draw)

	v_labels_w_w = getLabels(v_whitewins,WHITE)
	v_labels_b_w = getLabels(v_whitewins,BLACK)
	v_labels_w_b = getLabels(v_blackwins,WHITE)
	v_labels_b_b = getLabels(v_blackwins,BLACK)
	v_labels_w_d = getLabels(v_draw,WHITE)
	v_labels_b_d = getLabels(v_draw,BLACK)

	print("Running Alg")
	y_w_w = ensemble3(training_features_w,training_labels_w_w,v_features_w)
	print("ww")
	y_b_w = ensemble3(training_features_w,training_labels_b_w,v_features_w)
	print("bw")
	y_w_b = ensemble3(training_features_b,training_labels_w_b,v_features_b)
	print("wb")
	y_b_b = ensemble3(training_features_b,training_labels_b_b,v_features_b)
	print("bb")
	y_w_d = ensemble3(training_features_d,training_labels_w_d,v_features_d)
	print("wd")
	y_b_d = ensemble3(training_features_d,training_labels_b_d,v_features_d)
	print("bd")

	print("Calculating Error")
	error_w_w = meanError(v_labels_w_w,y_w_w)
	error_b_w = meanError(v_labels_b_w,y_b_w)
	error_w_b = meanError(v_labels_w_b,y_w_b)
	error_b_b = meanError(v_labels_b_b,y_b_b)
	error_w_d = meanError(v_labels_w_d,y_w_d)
	error_b_d = meanError(v_labels_b_d,y_b_d)
	error_t = error_w_w+error_b_w+error_w_b+error_b_b+error_w_d+error_b_d
	error_a = error_t/6

	print(str(error_w_w) + " White Wins White error")
	print(str(error_b_w) + " White Wins Black error")
	print(str(error_w_b) + " Black Wins White error")
	print(str(error_b_b) + " Black Wins Black error")
	print(str(error_w_d) + " Draw White error")
	print(str(error_b_d) + " Draw Black error")

	print(str(error_a) + " Mean error")

#python featuregenerator.py <uci fn> <stockfish fn> <validation-uci> <validation-stockfish>
main6Scores()
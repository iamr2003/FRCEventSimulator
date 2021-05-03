import random

#implemented using dictionaries for use of writing/reading, is slow computewise
#Can rewrite in numpy/cpp using matrices if more speed is needed


#Ranges for randomly generated teams, new ones can be passed to teams that are generated

#can write multiple ranges, this seems reasonable for week one
weekOneRanges = {
	'auto':{'avgCrossLine':[0,1],'avgLowerBallsScored':[0,3],'avgOuterBallsScored':[0,3],'avgInnerBallsScored':[0,2],'avgMissedBalls':[0,3]},
	'teleop':{'avgLowerBallsScored':[0,3],'avgOuterBallsScored':[0,3],'avgInnerBallsScored':[0,2],'avgMissedBalls':[0,3],'avgControlPanelRot':[0,1],'avgControlPanelPos':[0,1]},
	'endgame':{'avgClimbState':[0,2],'avgBalanced':[0,1]}
	#dont worry about other subjective stats yet 
	}
#use decimals to increase weighting
worldsRanges = {
	'auto':{'avgCrossLine':[0.5,1],'avgLowerBallsScored':[0,0],'avgOuterBallsScored':[1,5],'avgInnerBallsScored':[1,5],'avgMissedBalls':[0,3]},
	'teleop':{'avgLowerBallsScored':[0,0],'avgOuterBallsScored':[3,20],'avgInnerBallsScored':[3,20],'avgMissedBalls':[0,3],'avgControlPanelRot':[1,1],'avgControlPanelPos':[1,1]},
	'endgame':{'avgClimbState':[1.5,2],'avgBalanced':[0.5,1]}
	#assumes world folk won't score in low goal 
	}


#used a lot, probably a lib version
def randOnRange(range = [0,1]):
	#issue with random function repeating, goal is to help with increased randomization 
	random.seed(a=None,version=2)
	return random.uniform(range[0],range[1])

#represents a team, composed of "real averages" to represent ability and how much they vary from those
#LIMITATIONS: assumes that all aspects are independent, which they aren't(only a certain amount of balls, etc.); doesn't account for improvements in performance over time;
# variances are implemented in a set fashion, could be done differently
class team:
	def __init__(self,attrRanges=weekOneRanges,number= 0,name = ' '):#maybe add option to set definite averages
		self.attributeStDevs = {'auto':{},'teleop':{},'endgame':{}}
		self.attributeAverages = {'auto':{},'teleop':{},'endgame':{}}
		self.number = number
		self.name = name
		for attrType,attrs in attrRanges.items():
			for attr,val in attrs.items():
				#randomizes things in range
				self.attributeStDevs[attrType][attr] = randOnRange([0,0.5]) #currently used porportionally off values, could be bounded by other things
				self.attributeAverages[attrType][attr] =randOnRange(val)
	def getMatchStats(self):
		matchStats = {'auto':{},'teleop':{},'endgame':{}}
		for attrType,attrs in self.attributeAverages.items():
			for attr,val in attrs.items():
				deviation = self.attributeStDevs[attrType][attr]*self.attributeAverages[attrType][attr] #that proportional encoding
				#cuts off avg tag as we collapse to real data
				#hard capped at 0, probably skews distribution a bit
				matchStats[attrType][(attr,attr[3:])[attr[0:3]=='avg']] = max(round(randOnRange([-deviation,deviation])+self.attributeAverages[attrType][attr]),0)
		return matchStats
	def getAttributeAverages(self):
		return self.attributeAverages
	def __str__(self):
		return str(self.number)#could add name at some point, doesn't really matter

#Represents an alliance of three teams, calculates their total score in a match
#Limitations: Doesn't account for defense, also assumes all actions are indpendent, which they're not
class alliance:
	def __init__(self,teams=[team(),team(),team()]):
		self.teams = teams #note this allows more or less than 3 teams
	def getScoring(self):
			#many flags, but I can't think of easier way to check for RP
			balls = 0
			ControlPanelRot = False
			ControlPanelPos = False
			pts = 0
			endgamePts = 0
			Balanced = False
			#calc points with each team, add to total counts
			for team in self.teams:
				performance = team.getMatchStats()
				#Balls
				for mode in ["auto","teleop"]:
					for goal in ["Lower","Outer","Inner"]:
						#using the benefits of the dictionary structure to parse all balls
						pts += (["Lower","Outer","Inner"].index(goal)+1)*(1,2)[mode == 'auto']*performance[mode][goal+"BallsScored"] #could potentially add penalty for missing to increase realism through ball starving
						balls += performance[mode][goal+"BallsScored"]

				#aspects that only count once
				#ControlPanel
				if(not ControlPanelRot and performance['teleop']['ControlPanelRot']):
					pts+=10
					ControlPanelRot = True
				if(not ControlPanelPos and performance['teleop']['ControlPanelPos']):
					pts+=20
					ControlPanelPos = True
				#Balance
				if(not Balanced and performance['endgame']['Balanced']):
					pts+=15
					endgamePts+=15
					Balanced = True

				#Climb Pos
				posPoints = ((0,5)[performance['endgame']['ClimbState']==1],25)[performance['endgame']['ClimbState']==2]
				pts+=posPoints
				endgamePts+=posPoints
			#calc extra RPs
			extraRPs=0
			if(balls>=49 and ControlPanelPos and ControlPanelRot):#yes its possible they didn't get it, but we assume they know what they're doing
				extraRPs+=1
			if(endgamePts>=65):
				extraRPs+=1
			#return full dict to imitate whats published by FIRST
			return {'points':pts,'extraRPs':extraRPs,'balls':balls,'endgamePoints':endgamePts,'ControlPanelRot':ControlPanelRot,'ControlPanelPos':ControlPanelPos}
	def __str__(self):
		output = ''
		for team in self.teams:
			output += str(team) + ' '
		return output

#Runs a match between two alliances, calculates RP based on extra RPs + winRPs
#Limitations: only returns normal points rn, might need to return more for ranking purposes
class match:
	def __init__(self,red=alliance(),blue=alliance()):
		self.redAlliance = red
		self.blueAlliance = blue
	def getScoring(self):
		redScoring = self.redAlliance.getScoring()
		blueScoring = self.blueAlliance.getScoring()
		winner = (('blue','red')[redScoring['points']>blueScoring['points']],'tie')[redScoring['points']==blueScoring['points']]
		redWinRPs = ((0,1)[winner == 'tie'],2)[winner == 'red']
		blueWinRPs = 2 - redWinRPs #only 2 win RPs to go around in general
		return {
		'winner':winner, 'redPoints':redScoring['points'],'bluePoints':blueScoring['points'],
		'redRP':(redScoring['extraRPs']+ redWinRPs),'blueRP':(blueScoring['extraRPs']+blueWinRPs),
		'redAlliance':self.redAlliance, 'blueAlliance':self.blueAlliance
		}

#Ranks all teams based on match performance
#Limitations: Only ranks by avgRP rn, doesn't try tiebreakers
class ranking:
	def __init__(self, matchResults = [], teamList = []):
		self.ranking = []
		self.matchResults = matchResults
		i = 0
		for team in teamList:
			self.ranking.append({'team':teamList[i],'RPs':0,'matchesPlayed':0}) #not including the other ranking attributes yet
			i+=1 
	def setNewMatchResults(self, matchResults = []):
		self.matchResults = matchResults
	def avgRP(rank = {'RPs':0,'MatchesPlayed':0}):
		return rank['RPs']/rank['matchesPlayed']
	def calcRanking(self):
		for rank in self.ranking:
			rank['RPs']=rank['matchesPlayed']=0 #init ranking things to 0
		#go through each match and add RPs and match counts
		for result in self.matchResults:
			for alliance in ['red','blue']:
				for team in result[alliance + 'Alliance'].teams:
					for rank in self.ranking:#linear search, could be binary if we sort by team num first
						if(team.number == rank['team'].number):
							rank['RPs']+=result[alliance+'RP']
							rank['matchesPlayed']+=1
		#sort by avgRP, as they do for competition
		self.ranking.sort(key=lambda x: x['RPs'] if x['matchesPlayed']==0 else x['RPs']/x['matchesPlayed'],reverse= True)
	def __str__(self):
		output=''
		counter = 1
		for rank in self.ranking:
			#wish this wasn't just one line, but py is dumb about those things, maybe switch to proper formatted output with python equivalent of printf
			output += str(counter) + ' ' + str(rank['team']) + ' avgRP:' +str(round(rank['RPs'] if rank['matchesPlayed']==0 else rank['RPs']/rank['matchesPlayed'],2))+' RPs: ' + str(rank['RPs']) + ' MatchesPlayed: ' + str(rank['matchesPlayed']) + '\n'
			counter += 1
		return output

#Runs an event from a teamlist, generates matches and ranking
#Limitations: Scheduler is just random picking atm, potentially even multiples of a team in a match, perhaps make more like field match maker
class event:
	eventRanks = ranking()
	numTeams = 0
	teamList = []
	matchResults = []
	def __init__(self, teamList = [], numTeams = 0):#this logic might not work
		if(len(teamList) == 0):
			for i in range(0,numTeams):
				#could identify differently if you wanted random team numbers that are 4 digits
				self.teamList.append(team(number = i,name = ('Random Spawned Team #'+str(i))))
		else:
			print("This extra case happened")
			self.teamList = teamList
			numTeams = len(teamList)
	def getTeamList(self):
		return self.teamList
	def playMatches(self,numMatches = 0):
		if(numMatches == 0):
			numMatches = int(10*len(self.teamList)/6) #default to assume each team might get 10 matches
		for i in range(1,numMatches+1):#match scheduler, currently just random
			selectedTeams = []#reinit each time
			for x in range(0,6):
				selectedTeams.append(self.teamList[int(randOnRange([0,len(self.teamList)]))])
			thisMatch = match(alliance(selectedTeams[0:3]),alliance(selectedTeams[3:6]))
			self.matchResults.append(thisMatch.getScoring()) # might want to make more caches in matches themselves
	def updateRanking(self):
		self.eventRanks = ranking(self.matchResults,self.teamList)
		self.eventRanks.calcRanking()
#datetime for labeling files
from datetime import datetime
now = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")

#writes a list of dictionaries to rows in a csv file, with a header row up top with the keys(determined by list of names)
import csv
def dictToCSV(header = [],dict_data=[],fileName=''):
	csv_file = str(now)+fileName+".csv"
	try:
		with open(csv_file, 'w+',newline='') as csvfile:
			writer = csv.DictWriter(csvfile, fieldnames=header)
			writer.writeheader()
			for data in dict_data:
				writer.writerow(data)
	except IOError:
		print("I/O error")
#turns a nested dictionary into a single one with keys concatenated, maybe make recursive at some point
def flatten2dDict(dictionary = {}):
	newDict = {}
	for outerkey, innerdict in dictionary.items():
		for innerkey, val in innerdict.items():
			newDict[outerkey+innerkey]=val
	return newDict


palmetto = event(numTeams=60)
palmetto.playMatches(100)
palmetto.updateRanking()
#outputs to csv files, could be configured with whatever you want

#could maybe use .keys() method for header, but its not working properly atm
dictToCSV(['winner','redPoints','bluePoints','redRP','blueRP','redAlliance','blueAlliance'],palmetto.matchResults,'matchResults')
dictToCSV(['team','RPs','matchesPlayed'],palmetto.eventRanks.ranking,'ranking')

#things to parse team data is a nice format, maybe can be done in the team class if wanted
nameAndDataList = []
for team in palmetto.teamList:
	nameAndData = {}
	nameAndData=flatten2dDict(team.attributeAverages)
	nameAndData['team']=str(team)
	nameAndDataList.append(nameAndData)
header = [] # this is really long so I'm making it instead of writing explicitly
for key,val in nameAndData.items():#team at the end, but its annoying to format
	header.append(key)
	
dictToCSV(header,nameAndDataList,'teamDataReal')
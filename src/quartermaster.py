#!/usr/bin/python

from datetime import datetime
import json
import os
import server
import sys
import threading #used for the locks and communication threads
from time import gmtime, strftime, sleep

class QuarterMaster:
	def printEnd(self, text, start="", end="\n"):
		currTime = strftime("%Y-%m-%d %H:%M:%S.", gmtime()) + str(datetime.now().microsecond)
		sys.stdout.write(start+ "(" + currTime + ") QM: " + text + end)
		sys.stdout.flush()

	def __init__(self):
		i = 1
		self.pirateIds = []
		self.mapCounter = 0
		self.clues = []
		self.missedClueIds = []
		self.cluesCount = 0
		self.cluesLock = threading.RLock()
		self.missedCluesLock = threading.RLock()
		self.clueIndex = (-1,-1)
		self.solvedClues = []
		self.solvedCluesCount = 0
		self.solvedCluesLock = threading.RLock()
		self.commserver = None
		self.stop = False
		host = "localhost"
		port = 40000

		while i < len(sys.argv):
			if sys.argv[i] == "--first" or sys.argv[i] == "-f":
				self.printEnd("Quarter Master created!")
				self.prepare()
				self.getPirates()
				self.shipout()
				self.getClues()
			elif sys.argv[i] == "--host":
				i = i + 1
				host = sys.argv[i]
			elif sys.argv[i] == "--port":
				i = i + 1
				port = int(sys.argv[i])
			elif sys.argv[i] == "--clues":
				i = i + 1
				tmp = ""

				with open(sys.argv[i], 'r') as cluesFile:
					tmp = cluesFile.read().replace('\n', '')

				self.clues = json.loads(tmp)

				for j in self.clues:
					self.pirateIds.append(j["id"])
					self.cluesCount += len(j["data"])

				self.printEnd("Found " + str(self.cluesCount) + " clues.")
				self.printEnd("Found " + str(len(self.pirateIds)) + " pirates.")

			elif sys.argv[i] == "--solved-clues":
				i = i + 1
				tmp = ""

				with open(sys.argv[i], 'r') as cluesFile:
					tmp = cluesFile.read().replace('\n', '')

				self.solvedClues = json.loads(tmp)
				
				for j in self.solvedClues:
					self.solvedCluesCount += len(j["data"])

				self.calculateMissingClues()
				self.printEnd("Found " + str(self.solvedCluesCount) + " solved clues.")
				self.printEnd("Found " + str(len(self.missedClueIds)) + " missing clues.")
			else:
				self.printEnd("Argument " + str(i) + "(" + sys.argv[i] + ") is unknown.")

			i = i + 1

		self.commserver = server.Server(self, host, port)
		self.commserver.run() # change to start to run in seperate thread and uncomment below

		# while not self.stop:
		# 	try:
		# 		sleep(5)
		# 	except KeyboardInterrupt:
		# 		self.printEnd("Caught CTRL-C. Shutting down.")
		# 		self.shutdown()
		# 		self.commserver.shutdown()

	def shutdown(self):
		self.stop = True

######################################################################################
#				CLUE OPERTIONS
######################################################################################
	def getNextClueId(self):
		with self.cluesLock:
			returnClueIndex = self.getMissingClue()

			if returnClueIndex != None:
				pass
			elif self.clueIndex[0] == -1:
				return None
			elif self.clueIndex[1] < len(self.clues[self.clueIndex[0]]["data"]) - 1:
				self.clueIndex = (self.clueIndex[0], self.clueIndex[1] + 1)
				returnClueIndex = self.clueIndex
			elif self.clueIndex[0] < len(self.clues) - 1: # move to next pirate's clues
				self.clueIndex = (self.clueIndex[0] + 1, 0)
				returnClueIndex = self.clueIndex
			else: # no more clues left
				return None # tell clue solver to retry

			return returnClueIndex

	def addSolvedClue(self, clue):
		with self.solvedCluesLock:
			found = False

			for i in self.solvedClues:
				for j in i["data"]:
					if j["id"] == clue["data"][0]["id"]:
						self.printEnd("FOUND DUPLICATE!!!!")
						return False

			for i in self.solvedClues:
				if i["id"] == clue["id"]:
					i["data"].extend(clue["data"])
					found = True
					break

			if not found:
				self.solvedClues.append(clue)

			self.solvedCluesCount += 1
			self.printEnd("Received " + str(self.solvedCluesCount) + " solved clue(s) so far.", "\r", "")
			self.commserver.broadcastToClientSockets("solved-clue:" + json.dumps(clue))

			if self.solvedCluesCount == self.cluesCount:
				return self.validateClues()

		return False

	def addMissedClue(self, clue):
		with self.cluesLock:
			self.missedClueIds.append(clue)
	
	def getMissingClue(self):
		with self.cluesLock:
			if len(self.missedClueIds) > 0:
				self.printEnd("Picking up missed clue: " + str(self.missedClueIds[0]))
				return self.missedClueIds.pop(0)
			else:
				return None

	def calculateMissingClues(self):
		if self.solvedCluesCount == 0:
			self.clueIndex = (0,-1)
			return

		missing = []
		tmpMissing = []
		tmpIndex = None
		self.clueIndex = (0, -1)
		self.clueIndex = self.getNextClueId() 

		while self.clueIndex != None:
			foundPirate = False

			for i in self.solvedClues:
				if self.clues[self.clueIndex[0]]["id"] == i["id"]:
					foundPirate = True
					foundClue = False

					for j in i["data"]:
						if self.clues[self.clueIndex[0]]["data"][self.clueIndex[1]]["id"] == j["id"]:
							self.printEnd("FOUND CLUE " + str(self.clueIndex))
							foundClue = True
							tmpIndex = self.clueIndex
							missing.extend(tmpMissing)
							tmpMissing = []

					if not foundClue:
						# self.printEnd("DIDNT FIND CLUE " + str(self.clueIndex))
						tmpMissing.append(self.clueIndex)

			if not foundPirate:
				# self.printEnd("DIDNT FIND PIRATE " + str(self.clueIndex))
				tmpMissing.append(self.clueIndex)

			self.clueIndex = self.getNextClueId()

		self.clueIndex = tmpIndex
		self.missedClueIds = missing
		self.printEnd("clueIndex: " + str(self.clueIndex))

######################################################################################
#				RUMMY SECTION
######################################################################################

	def tellRummy(self, message):
		returnMsg = os.popen("python rummy.pyc " + message).read()
		return returnMsg

	def prepare(self):
		self.printEnd("Rummy is preparing...", "", "")
		response = self.tellRummy("-prepare")
		# self.printEnd(json.dumps(response))
		self.printEnd("Rummy is prepared.       ", "\r")

	def getPirates(self, num = 10):
		self.printEnd("Getting pirates...", "", "")
		pirateData = json.loads(self.tellRummy("-add " + str(num)))
		self.pirateIds.extend(pirateData["data"])
		self.printEnd("Got " + str(num) + " pirates.            ", "\r")

	def shipout(self):
		self.printEnd("Shipping out...", "", "")
		response = self.tellRummy("-shipout")
		# self.printEnd(json.dumps(response))
		self.printEnd("Shipped out.       ", "\r")

	getclue = 0
	def getClues(self):
		removePirates = []

		for i in self.missedClueIds:
			if i[1] > 1000 / len(self.pirateIds) * 0.1: #10%+ wrong clues
				removePirates.append(i[0])

		if len(removePirates) > 0:
			for i in removePirates:
				self.printEnd("Removing pirate: " + i)
				self.pirateIds.remove(i)

			self.tellRummy("-remove '" + json.dumps(removePirates) + "'")

			if len(self.pirateIds) == 0:
				self.getPirates()

		with self.cluesLock:
			self.printEnd("Getting clues...", "", "")
			clueData = json.loads(self.tellRummy("-clues"))
			# cluesFile = open("all" + str(self.getclue) + ".clue", "w")
			# cluesFile.write(json.dumps(clueData))
			# cluesFile.close()
			self.clues = clueData["data"]
			self.printEnd("Got clues for " + str(len(self.clues)) + " pirates for map #" + str(self.mapCounter) + ".         ", "\r")
			self.mapCounter += 1
			self.cluesCount = 0
			self.clueIndex = (0,-1)

			for i in self.clues:
				self.cluesCount += len(i["data"])

		self.getclue += 1 # debug

	getsolvedclue = 0
	def validateClues(self):
		# cluesFile = open("solved-" + str(self.getsolvedclue) + ".clue", "w")
		# cluesFile.write("-verify '" + json.dumps(self.solvedClues) + "'")
		# cluesFile.close()
		firstRunForMap = self.cluesCount == 1000
		self.getsolvedclue += 1
		self.clueIndex = (-1,-1)
		# self.clues = []
		result = self.tellRummy("-verify '" + json.dumps(self.solvedClues) + "'")
		result = json.loads(result)
		# cluesFile = open("all" + str(self.getclue) + ".clue", "w")
		# cluesFile.write(json.dumps(result))
		# cluesFile.close()
		self.getclue += 1

		if result["status"] == "success":
			if "finished" in result:
				self.printEnd("All clues for all the maps were solved!", "\r")
				return True
			else:
				self.printEnd(str(result))
				self.printEnd("All clues for map #" + str(self.mapCounter) + " was solved.", "\r")
				self.getClues()
				self.solvedCluesCount = 0
				self.solvedClues = []
				self.commserver.broadcastToClientSockets("clues:" + json.dumps(self.clues))
				self.commserver.broadcastToClientSockets("ship-file:" + self.commserver.getFileContent("./data/crew/ship.dat"))
				self.commserver.broadcastToClientSockets("pass")
		else:
			self.clues = result["data"]
			self.clueIndex = (0,-1)
			self.cluesCount = 0
			self.solvedCluesCount = 0
			self.solvedClues = []
			self.commserver.broadcastToClientSockets("clues:" + json.dumps(self.clues))
			self.commserver.broadcastToClientSockets("ship-file:" + self.commserver.getFileContent("./data/crew/ship.dat"))
			self.commserver.broadcastToClientSockets("pass")

			if firstRunForMap:
				self.wrongClueCount = []
			
			for i in self.clues:
				if firstRunForMap:
					self.wrongClueCount.append((i["id"], len(i["data"])))

				self.cluesCount += len(i["data"])

			self.printEnd(str(self.cluesCount) + " clues were wrong.", "\r")

		return False

######################################################################################
#				RUN OPERTIONS
######################################################################################
qm = QuarterMaster()
qm.printEnd("Done.")
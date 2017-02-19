#!/usr/bin/python

import os
import sys
import time
import json
import multiprocessing # for getting number of cores
from time import gmtime, strftime
from datetime import datetime

def printEnd(text, start="", end="\n"):
	currTime = strftime("%Y-%m-%d %H:%M:%S.", gmtime()) + str(datetime.now().microsecond)
	sys.stdout.write(start+ "(" + currTime + ") " + text + end)
	sys.stdout.flush()

def cleanChats():
	os.system("rm *.chat *.chat.lock *.log *.err 2> /dev/null")
	pass

class QuarterMaster:
	pirateIds = []
	clues = []
	currentClueId = 0

	def __init__(self):
		printEnd("Quarter Master created!")
		printEnd("Waking Rummy...", "", "")
		self.tellRummy("-wake")
		printEnd("Rummy is awake.     ", "\r")
		printEnd("Rummy is preparing...", "", "")
		self.tellRummy("-prepare")
		printEnd("Rummy is prepared.       ", "\r")

	def createPirates(self):
		printEnd("Getting pirates...", "", "")
		numCpus = multiprocessing.cpu_count()
		numCpus = 1
		pirateData = json.loads(self.tellRummy("-add " + str(numCpus)))
		self.pirateIds = pirateData["data"]

		for x in xrange(0, numCpus):
			# os.spawnl(os.P_NOWAIT, "./pirate.py --id " + self.pirateIds[x] + " > " + self.pirateIds[x] + ".log " + " 2> " + self.pirateIds[x] + ".err")
			# os.system("./pirate.py --id " + self.pirateIds[x] + " > " + self.pirateIds[x] + ".log " + " 2> " + self.pirateIds[x] + ".err")
			# os.system("./pirate.py --id " + self.pirateIds[x])
			os.system("./pirate.py --id " + self.pirateIds[x] + " &")
			open("quartermaster_" + self.pirateIds[x] + ".chat", 'a').close()

		printEnd("Got " + str(numCpus) + " pirates.            ", "\r")

	def shipout(self):
		printEnd("Shipping out...", "", "")
		self.tellRummy("-shipout")
		printEnd("Shipped out.       ", "\r")

	def getClues(self):
		printEnd("Getting clues...", "", "")
		clueData = json.loads(self.tellRummy("-clues"))
		clueData = clueData["data"]

		for x in xrange(0,len(clueData)):
			pirateId = clueData[x]["id"]
			oldLength = len(self.clues)
			self.clues.extend(clueData[x]["data"])

			for y in xrange(oldLength,len(self.clues)):
				self.clues[y]["pirateId"] = pirateId

		printEnd("Got " + str(len(self.clues)) + " clues.         ", "\r")

	def tellPirate(self, pirateId, message):
		sentmessage = False
		filename = "pirate_" + str(pirateId) + ".chat"
		filenameLock = filename + ".lock"

		while os.path.exists(filenameLock):
			pass

		while not sentmessage:
			try:
				os.rename(filename, filenameLock)
				piratechat = open(filenameLock, "a+")
				piratechat.write(message)
				sentmessage = True
				piratechat.close()
				os.rename(filenameLock, filename)
				printEnd("QM: Sent message to pirate " + pirateId + ".")
			except OSError as e:
				if os.path.exists(filenameLock):
					# printEnd("QM: '" + filename + "' is locked.")
					pass
				else:
					printEnd("QM: '" + filename + "' does not exist.")
					raise e
			finally:
				pass
				#printEnd("QM: Message sent to pirate " + str(pirateId) + ".")

	def tellRummy(self, message):
		returnMsg = os.popen("./rummy.pyc " + message).read()
		rummyResponse = json.loads(returnMsg)
		return json.dumps(rummyResponse)

	def listen(self):
		done = False
		response = {
			"proceed": True
		}

		while not done:
			for x in xrange(0,len(self.pirateIds)):
				filename = "quartermaster_" + str(self.pirateIds[x]) + ".chat"
				filenameLock = filename + ".lock"
				readmessage = False

				if os.path.exists(filename):
					while not readmessage:
						try:
							os.rename(filename, filenameLock)
							piratechat = open(filenameLock, "a+")
							message = piratechat.read()
							readmessage = True

							if message != "":
								message = json.loads(message)
								response = self.respondToPirateRequest(message)
								piratechat.close()
								open(filename, 'w').close()

								while not os.path.exists(filename):
									pass
									
								os.remove(filenameLock)
							else:
								piratechat.close()
								os.rename(filenameLock, filename)
						except OSError as e:
							if os.path.exists(filenameLock):
								# printEnd("QM: '" + filename + "' is locked.")
								pass
							else:
								printEnd("QM: '" + filename + "' does not exist.")
								raise e
						finally:
							pass

				if response["proceed"] == False:
					done = True

	def respondToPirateRequest(self, message):
		response = {
			"proceed": True
		}

		if message["status"] == "idle":
			if message["request"] == "clue":
				sendMessage = {
					"status": "success",
					"command": "solveclue",
					"clue": self.clues[self.currentClueId]
				}
				self.currentClueId = self.currentClueId + 1
				self.tellPirate(message["pirateId"], json.dumps(sendMessage))
				# printEnd("QM: Sent clue[" + str(self.currentClueId - 1) + "] to pirate " + message["pirateId"] + ".")
			else:
				sendMessage = {
					"status": "error",
					"code": 401,
					"message": "Unknown idle message."
				}
				self.tellPirate(message["pirateId"], json.dumps(sendMessage))
				printEnd("QM: Unknown idle message '" + message["request"] + "' received form pirate " + message["pirateId"])
		elif message["status"] == "success":
			if message["request"] == "validate":
				response["proceed"] = False # debug
				printEnd("QM: Received validation code: " + message["clue"]["data"])
			else:
				sendMessage = {
					"status": "error",
					"code": 402,
					"message": "Unknown success message."
				}
				self.tellPirate(message["pirateId"], json.dumps(sendMessage))
				printEnd("QM: Unknown idle message '" + message["request"] + "' received form pirate " + message["pirateId"])
		else:
			sendMessage = {
				"status": "error",
				"code": 410,
				"message": "Unknown status"
			}
			self.tellPirate(message["pirateId"], json.dumps(sendMessage))
			printEnd("QM: Unknown status '" + message["status"] + "' received form pirate " + message["pirateId"])

		return response

try:
	cleanChats()
	printEnd("Let's find that treasure!\n")
	qm = QuarterMaster()
	qm.createPirates()
	qm.shipout()
	qm.getClues()
	qm.listen()
finally:
	# cleanChats() # must always be the last statement
	pass
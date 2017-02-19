#!/usr/bin/python

import os
import time
import sys
import json
from time import gmtime, strftime
from datetime import datetime
import hashlib

def printEnd(text, start="", end="\n"):
	currTime = strftime("%Y-%m-%d %H:%M:%S.", gmtime()) + str(datetime.now().microsecond)
	sys.stdout.write(start+ "(" + currTime + ") " + text + end)
	sys.stdout.flush()

class Pirate:
	myId = 0

	def __init__(self):
		i = 1

		while i < len(sys.argv):
			if sys.argv[i] == "--id" or sys.argv[i] == "-i":
				i = i + 1
				self.myId = sys.argv[i]
			else:
				printEnd("P: Argument " + str(i) + "(" + sys.argv[i] + ") is unknown.")

			i = i + 1

		open("pirate_" + self.myId + ".chat", 'a').close()

	def tellQuarterMaster(self, message):
		sentmessage = False
		filename = "quartermaster_" + str(self.myId) + ".chat"
		filenameLock = filename + ".lock"

		while os.path.exists(filenameLock):
			pass

		while not sentmessage:
			try:
				os.rename(filename, filenameLock)
				qmchat = open(filenameLock, "a+")
				qmchat.write(message)
				sentmessage = True
				qmchat.close()
				os.rename(filenameLock, filename)
				sentmessage = True
				printEnd("P(" + str(self.myId) + "): Sent message to quarter master.")
			except OSError as e:
				if os.path.exists(filenameLock):
					# printEnd("P(" + str(self.myId) + "): " + filename + "' is locked.")
					pass
				else:
					printEnd("P(" + str(self.myId) + "): '" + filename + "' does not exist.")
					raise e
			finally:
				pass

	def listen(self):
		filename = "pirate_" + str(self.myId) + ".chat"
		filenameLock = filename + ".lock"
		readmessage = False

		while not readmessage:
			try:
				os.rename(filename, filenameLock)
				qmchat = open(filenameLock, "a+")
				message = qmchat.read()
				readmessage = True

				if message != "":
					message = json.loads(message)
					qmchat.close()
					open(filename, 'w').close()

					while not os.path.exists(filename):
						pass
						
					os.remove(filenameLock)
				else:
					message = {}
					qmchat.close()
					os.rename(filenameLock, filename)
			except OSError as e:
				if os.path.exists(filenameLock):
					# printEnd("P(" + str(self.myId) + "): '" + filename + "' is locked.")
					pass
				else:
					printEnd("P(" + str(self.myId) + "): '" + filename + "' does not exist.")
					raise e
			finally:
				pass

		return message

	def analyseMessage(self, message):
		if message["status"] == "success":
			if message["command"] == "solveclue":
				result = self.solveClue(message["clue"])
				result = {
					"pirateId": p.myId,
					"status": "success",
					"request": "validate",
					"clue": result
				}
				self.tellQuarterMaster(json.dumps(result))
			else:
				printEnd("P(" + str(self.myId) + ": Unknown command " + message["command"] + " message received form pirate " + message["pirateId"])
		elif message["status"] == "error":
			printEnd("P(" + str(self.myId) + "): ERROR " + str(message["code"]) + ": " + message["message"] + ".")
		else:
			printEnd("P(" + str(self.myId) + "): Unknown status '" + message["status"] + "' received form quartermaster")

	def solveClue(self, clue):
		printEnd("P(" + str(self.myId) + "): Solving clue. Currently at stage 1.", "", "")
		clue = self.digInTheSand(clue)
		printEnd("P(" + str(self.myId) + "): Solving clue. Currently at stage 2.", "\r", "")
		clue = self.searchTheRiver(clue)
		printEnd("P(" + str(self.myId) + "): Solving clue. Currently at stage 3.", "\r", "")
		clue = self.crawlIntoTheCave(clue)
		printEnd("P(" + str(self.myId) + "): Solved clue.                               ", "\r", "\n")
		hashedClue = hashlib.md5(clue["data"]).hexdigest()
		# printEnd("HERE IS THE HASH: " + hashedClue)
		clue["data"] = hashedClue
		return clue

	def digInTheSand(self, clue):
		for x in xrange(0,100):
			clue = self.useShovel(clue)
		
		for x in xrange(0,200):	
			clue = self.useBucket(clue)

		for x in xrange(0,100):
			clue = self.useShovel(clue)

		return clue

	def searchTheRiver(self, clue):
		for x in xrange(0,200):	
			clue = self.useBucket(clue)

		return clue

	def crawlIntoTheCave(self, clue):
		for x in xrange(0,200):	
			clue = self.useRope(clue)

		for x in xrange(0,100):
			clue = self.useTorch(clue)

		return clue

	def useShovel(self, clue):
		clue["data"] = ''.join(sorted(clue["data"]))

		if clue["data"][0].isdigit():
			clue["data"] += "0A2B3C"

		clue["data"] = clue["data"][1:]

		return clue

	def useBucket(self, clue):
		newClue = ""

		for c in clue["data"]:
			if c.isdigit():
				c = int(c)

				if c > 5:
					c = c - 2
				else:
					c = c * 2

				c = str(c)

			newClue += c

		clue["data"] = newClue
		return clue

	def useRope(self, clue):
		newClue = ""

		for c in clue["data"]:
			if c.isdigit():
				c = int(c)

				if c % 3 == 0:
					c = "5"
				elif c % 3 == 1:
					c = "A"
				elif c % 3 == 2:
					c = "B"
			elif c.isalpha(): #TODO: can be optimized to just an else
				c = int(c, 16) - 10 # TODO: Check this, i think it is a mistake in the pdf

				if c % 5 == 0:
					c = "C"
				elif c % 1 == 0:
					c = "1"
				elif c % 2 == 0:
					c = "2"
				else:
					c = str(c)

			newClue += c

		clue["data"] = newClue
		return clue

	def useTorch(self, clue):
		newClue = ""
		sum = 0

		for c in clue["data"]:
			if c.isdigit():
				sum += int(c)

		if sum < 100:
			sum = sum * sum

		sum = str(sum)

		if len(sum) < 10:
			sum = "F9E8D7" + sum[1:]
		else:
			sum = sum[6:] + "A1B2C3"

		clue["data"] = sum
		return clue


p = Pirate()

done = False

while not done:
	message = {
		"pirateId": p.myId,
		"status": "idle",
		"request": "clue"
	}
	p.tellQuarterMaster(json.dumps(message))
	message = p.listen()

	while message == {}:
		message = p.listen()

	if message["status"] == "success" and message["command"] == "shutdown":
		done = True

	p.analyseMessage(message)
	done = True


#!/usr/bin/python

import os
import sys
import time
import json
import socket
import threading
import clientsocket
import multiprocessing # for getting number of cores
from time import gmtime, strftime
from datetime import datetime

class QuarterMaster:
	pirates = []
	clues = []
	clientsockets = []
	currentClueId = 0
	solvedClues = []
	mapIndex = 1
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	stop = False
	missedClues = []
	pirateIds = []

	def printEnd(self, text, start="", end="\n"):
		currTime = strftime("%Y-%m-%d %H:%M:%S.", gmtime()) + str(datetime.now().microsecond)
		sys.stdout.write(start+ "(" + currTime + ") QM: " + text + end)
		sys.stdout.flush()

	def __init__(self):
		self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		i = 1

		while i < len(sys.argv):
			if sys.argv[i] == "--first" or sys.argv[i] == "-f":
				self.printEnd("Quarter Master created!")
				self.printEnd("Waking Rummy...", "", "")
				self.tellRummy("-wake")
				self.printEnd("Rummy is awake.     ", "\r")
				self.printEnd("Rummy is preparing...", "", "")
				self.tellRummy("-prepare")
				self.printEnd("Rummy is prepared.       ", "\r")
				self.getPirates()
				self.shipout()
				self.getClues()
			elif sys.argv[i] == "--clues":
				i = i + 1
				cluesFile = open(sys.argv[i])
				self.clues = json.loads(cluesFile.read())
				cluesFile.close()
			elif sys.argv[i] == "--solved-clues":
				i = i + 1
				cluesFile = open(sys.argv[i])
				self.solvedClues = json.loads(cluesFile.read())
				cluesFile.close()
			# elif sys.argv[i] == "--nextClueId" or sys.argv[i] == "-i":
			# 	i = i + 1
			# 	self.currentClueId = sys.argv[i]
			else:
				self.printEnd("Argument " + str(i) + "(" + sys.argv[i] + ") is unknown.")

			i = i + 1

		connected = False
		while not connected:
			try:
				self.serversocket.bind(("localhost", 40000))
				self.serversocket.listen(5)
				connected = True
				self.printEnd("Online.")
			except:
				pass

		clientsocket.ClientSocket.qmLock = threading.RLock()
		clientsocket.ClientSocket.qm = self

	def getPirates(self):
		self.printEnd("Getting pirates...", "", "")
		pirateData = json.loads(self.tellRummy("-add 10"))
		self.pirateIds = pirateData["data"]
		self.printEnd("Got 10 pirates.            ", "\r")


	def listenForConnections(self):
		numPirates = len(self.clientsockets)

		while not self.stop:
			self.printEnd("Waiting for pirate.")
			(cs, address) = self.serversocket.accept()
			with clientsocket.ClientSocket.qmLock:
				ct = clientsocket.ClientSocket(cs)
				self.printEnd("Pirate connected at ", "\r", "")
				print(address)
				ct.send("yourid:" + str(numPirates))

				for x in xrange(0,len(self.clientsockets)):
					self.clientsockets[x].send("newpirate:{\"id\":" + str(numPirates) + ",\"address\":{\"host\":\"" + address[0] + "\",\"port\":\"" + str(address[1]) + "\" } }")
					ct.send("newpirate:{\"id\":" + str(self.clientsockets[x].pirateId) + ",\"address\":{\"host\":\"" + self.clientsockets[x].address[0] + "\",\"port\":\"" + str(self.clientsockets[x].address[1]) + "\" } }")

				self.clientsockets.append(ct)
				ct.pirateId = numPirates
				ct.send("clues:" + json.dumps(self.clues));
				ct.send("solved-clues:" + json.dumps(self.solvedClues));
				ct.send("syncdone");
				ct.start()
				ct.address = address
				numPirates += 1

	def broadcastToPirates(self, message, exceptId = -1):
		with clientsocket.ClientSocket.qmLock:
			for x in xrange(0,len(self.clientsockets)):
				if x != exceptId:
					try:
						self.clientsockets[x].send(message)
					except:
						self.printEnd("Pirate " + str(self.clientsockets[x].pirateId) + " threw exception when broadcasting.")

	def shipout(self):
		self.printEnd("Shipping out...", "", "")
		self.tellRummy("-shipout")
		self.printEnd("Shipped out.       ", "\r")

	def getClues(self):
		self.printEnd("Getting clues...", "", "")
		clueData = json.loads(self.tellRummy("-clues"))
		self.addClues(clueData["data"])
		self.printEnd("Got " + str(len(self.clues)) + " clues.         ", "\r")

	def addClues(self, clueList):
		clueData = clueList
		self.clues = []
		self.currentClueId = 0

		for x in xrange(0,len(clueData)):
			pirateId = clueData[x]["id"]
			oldLength = len(self.clues)
			self.clues.extend(clueData[x]["data"])

			for y in xrange(oldLength,len(self.clues)):
				self.clues[y]["pirateId"] = pirateId

	def tellRummy(self, message):
		returnMsg = os.popen("./rummy.pyc " + message).read()
		return returnMsg

	def reworkSolvedClues(self):
		tmpClues = {}

		for x in xrange(0,len(self.pirateIds)):
			tmpClues[self.pirateIds[x]] = {"data":[], "id":self.pirateIds[x]}

		for x in xrange(0,len(self.solvedClues)):
			tmpClues[self.solvedClues[x]["id"]]["data"].append(self.solvedClues[x]["data"])

		self.solvedClues = []

		for x in xrange(0,len(self.pirateIds)):
			self.solvedClues.append(tmpClues[self.pirateIds[x]])

	def finish(self):
		for x in xrange(0,len(self.clientsockets)):
			self.clientsockets[x].stop = True

		self.stop = True

print("Let's find that treasure!\n")
qm = QuarterMaster()
qm.listenForConnections()

try:
	while not qm.stop:
		time.sleep(10)
except:
	for x in xrange(0, len(qm.clientsockets)):
		qm.clientsockets[x].stop = True
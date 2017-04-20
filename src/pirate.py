#!/usr/bin/python

import os
import time
import sys
import json
import socket
import threading
from time import gmtime, strftime
from datetime import datetime
import hashlib

class Pirate:
	myId = None
	socket = None
	pirates = []
	solvedClues = []
	clues = []

	def printEnd(self, text, start="", end="\n"):
		currTime = strftime("%Y-%m-%d %H:%M:%S.", gmtime()) + str(datetime.now().microsecond)
		sys.stdout.write(start+ "(" + currTime + ") P(" + str(self.myId) + "): " + text + end)
		sys.stdout.flush()

	def __init__(self):
		qmIP =  "localhost"
		qmPort = 40000
		i = 1

		while i < len(sys.argv):
			if sys.argv[i] == "--host" or sys.argv[i] == "-h":
				i = i + 1
				qmIP = sys.argv[i]
			elif sys.argv[i] == "--port" or sys.argv[i] == "-p":
				i = i + 1
				qmPort = sys.argv[i]
			elif sys.argv[i] == "--spawnqm" or sys.argv[i] == "-s":
				os.system("./quartermaster.py --first &")
			else:
				self.printEnd("P: Argument " + str(i) + "(" + sys.argv[i] + ") is unknown.")

			i = i + 1

		self.reconnect(qmIP, qmPort, 5)


	def reconnect(self, host = None, port = None, delay = 35):
		if host == None:
			wait = True
			minId = self.myId
			index = -1

			for x in xrange(0,len(self.pirates)):
				self.printEnd("PIRATE: " + json.dumps(self.pirates))
				if self.pirates[x]["id"] < minId:
					minId = self.pirates[x]["id"]
					index = x

			if index == -1:
				cluesFile = open("all.clue", "w")
				cluesFile.write(json.dumps(self.clues))
				cluesFile.close()
				cluesFile = open("solved.clue", "w")
				cluesFile.write(json.dumps(self.solvedClues))
				cluesFile.close()
				self.printEnd("Spawning new quartermaster.")

				os.system("./quartermaster.py --clues all.clue --solved-clues solved.clue > qm.log&")
				host = "localhost"
			else:
				host = self.pirates[index]["address"]["host"]
			
			port = 40000
		else:
			pass

		self.printEnd("Quarter master should be located at " + host + ":" + str(port))

		connected = False

		while not connected:
			try:
				self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				self.socket.connect((host, port))
				self.socket = self.socket.makefile("w")
				connected = True
				self.printEnd("Online                   ", "\r", "\n")
			except:
				for x in xrange(0, delay):
					self.printEnd("Attempting to reconnect in " + str(delay - x) + " seconds.          ", "\r", "")
					time.sleep(1)

	def tellQuarterMaster(self, message):
		totalsent = 0
		sent = self.socket.send(str(len(message)) + "\n")
		while totalsent < len(message):
			sent = self.socket.send(message[totalsent:])
			if sent == 0:
				raise RuntimeError("socket connection broken")
			totalsent = totalsent + sent

	def listen(self):
		chunks = []
		bytes_recd = 0
		msgLength = 0
		strLength = ""
		stop = False

		while not stop:
			charRead = ''.join(self.socket.recv(1))
			if charRead == "\n":
				stop = True
			else:
				strLength += charRead

		msgLength = int(strLength)

		while bytes_recd < msgLength:
			chunk = self.socket.recv(min(msgLength - bytes_recd, 2048))
			if chunk == '':
				raise RuntimeError("socket connection broken")

			chunks.append(chunk)
			bytes_recd = bytes_recd + len(chunk)

		return ''.join(chunks)

	def analyseMessage(self, message):
		try:
			command = message[:message.index(':')]
			message = message[message.index(':') + 1:]
		except: # Exception as e
			command = message
			message = ""

		if command == "yourid":
			self.myId = message
		elif command == "newpirate":
			self.pirates.append(json.loads(message))
		elif command == "remove-pirate":
			message = int(message)

			for x in xrange(0,len(self.pirates)):
				if message == self.pirates[x]["id"]:
					self.pirates.remove(x)
					break
		elif command == "clues":
			self.clues = json.loads(message)
		elif command == "solved-clue":
			self.solvedClues.append(json.loads(message))
		elif command == "solved-clues":
			self.solvedClues = json.loads(message)
		elif command == "clear-clues":
			self.solvedClues = []
		elif command == "solve-clue":
			solvedClue = self.solveClue(self.clues[int(message)])
			self.tellQuarterMaster("validate-clue:" + json.dumps(solvedClue))
			self.solvedClues.append(solvedClue)
		else:
			raise ValueError("Invalid command: " + command)

	def solveClue(self, clue):
		clue = self.digInTheSand(clue)
		clue = self.searchTheRiver(clue)
		clue = self.crawlIntoTheCave(clue)
		hashedClue = hashlib.md5(clue["data"]).hexdigest()
		clue["data"] = hashedClue.upper()
		return {
			"id": clue["pirateId"],
			"data": {
				"id": clue["id"],
				"key": clue["data"]
			}
		}

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
		else:
			clue["data"] += "1B2C3D"


		clue["data"] = clue["data"][1:].upper()

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
			else:
				ctmp = int(c, 16) - 10

				if ctmp % 5 == 0:
					c = "C"
				elif ctmp % 5 == 1:
					c = "1"
				elif ctmp % 5 == 2:
					c = "2"

			newClue += c

		clue["data"] = newClue.upper()
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

		clue["data"] = sum.upper()
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

		clue["data"] = newClue.upper()
		return clue


p = Pirate()
done = False

while not done:
	try:
		message = p.listen()

		while message != "syncdone":
			p.analyseMessage(message)
			message = p.listen()

		p.printEnd("Synced all data from quarter master.")

		message = "request-clue"
		p.tellQuarterMaster(message)

		while not done:
			message = p.listen()

			if message == "stop":
				done = True
				p.printEnd("Shutting down.                               ", "\r", "\n")
			else:
				p.analyseMessage(message)
	finally:
		p.socket.close()

		if not done:
			print("")
			p.reconnect()
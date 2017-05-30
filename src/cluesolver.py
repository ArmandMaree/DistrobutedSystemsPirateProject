#!/usr/bin/python

from datetime import datetime
import hashlib
import json
from ast import literal_eval
import os
import socket
import sys
import threading # used for potential scalability, not really used
import time
from time import gmtime, strftime

class ClueSolver(threading.Thread):

	def printEnd(self, text, start="", end="\n"):
		currTime = strftime("%Y-%m-%d %H:%M:%S.", gmtime()) + str(datetime.now().microsecond)
		sys.stdout.write(start+ "(" + currTime + ") CS(" + str(self.myId) + "): " + text + end)
		sys.stdout.flush()

	def __init__(self):
		super(ClueSolver, self).__init__()
		self.myId = None
		self.host =  "localhost"
		self.port = 40000
		self.mysocket = None
		self.pirates = []
		self.solvedClues = []
		self.clues = []
		self.stop = False
		i = 1

		# os.system("rm ./data/crew/*.dat")

		while i < len(sys.argv):
			if sys.argv[i] == "--host" or sys.argv[i] == "-h":
				i = i + 1
				self.host = sys.argv[i]
			elif sys.argv[i] == "--port" or sys.argv[i] == "-p":
				i = i + 1
				self.port = sys.argv[i]
			elif sys.argv[i] == "--spawnqm" or sys.argv[i] == "-s":
				os.system("python quartermaster.py --first &")
			else:
				self.printEnd("P: Argument " + str(i - 1) + "(" + sys.argv[i] + ") is unknown.")

			i = i + 1

		while True: # simulated do while
			if self.connectToQuarterMaster():
				self.run()

			if self.stop:
				break
			else:
				self.findNewHost()

	def run(self):
		while not self.stop:
			try:
				message = self.receiveMessage()

				if message == "stop":
					self.sendMessage("stop-ack")
					self.stop = True
				else:
					response = self.analyseMessage(message)

					if response != None:
						self.sendMessage(response)
			except socket.error:
				self.printEnd("Socket error occurred!")
				# self.stop = True
				self.closeSocket()
				return
			except Exception as e:
				self.printEnd("Error occurred: " + str(e))
				raise #debug
			else:
				pass
			finally:
				pass

######################################################################################
#				CLUE OPERTIONS
######################################################################################
	def solveClue(self, pirateIndex, clueIndex):
		clue = self.clues[pirateIndex]["data"][clueIndex]["data"]
		clue = self.digInTheSand(clue)
		clue = self.searchTheRiver(clue)
		clue = self.crawlIntoTheCave(clue)
		clue = hashlib.md5(clue).hexdigest().upper()

		return {
			"id": self.clues[pirateIndex]["id"],
			"data": [{
				"id": self.clues[pirateIndex]["data"][clueIndex]["id"],
				"key": clue
			}]
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
		clue= ''.join(sorted(clue))

		if clue[0].isdigit():
			clue += "0A2B3C"
		else:
			clue += "1B2C3D"


		clue = clue[1:].upper()

		return clue

	def useRope(self, clue):
		newClue = ""

		for c in clue:
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

		clue = newClue.upper()
		return clue

	def useTorch(self, clue):
		newClue = ""
		sum = 0

		for c in clue:
			if c.isdigit():
				sum += int(c)

		if sum < 100:
			sum = sum * sum

		sum = str(sum)

		if len(sum) < 10:
			sum = "F9E8D7" + sum[1:]
		else:
			sum = sum[6:] + "A1B2C3"

		clue = sum.upper()
		return clue

	def useBucket(self, clue):
		newClue = ""

		for c in clue:
			if c.isdigit():
				c = int(c)

				if c > 5:
					c = c - 2
				else:
					c = c * 2

				c = str(c)

			newClue += c

		clue = newClue.upper()
		return clue

######################################################################################
#				SOCKET OPERTIONS
######################################################################################
	def connectToQuarterMaster(self, retryDelay = 5):
		connected = False
		counter = 0

		while not connected and counter < 20:
			try:
				self.mysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.mysocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				self.mysocket.connect((self.host, self.port))
				self.host = self.mysocket.getsockname()[0]
				connected = True
				self.printEnd("Online                   ", "\r", "\n")
			except socket.error:
				counter += 1

				for x in xrange(0, retryDelay):
					# self.printEnd("Attempting to reconnect in " + str(retryDelay - x) + " seconds.          ", "\r", "")
					time.sleep(1)
			except:
				raise

		return connected

	def findNewHost(self):
		hostSolverId = self.myId

		for i in self.pirates:
			if i["id"] < hostSolverId:
				hostSolverId = i["id"]

		self.printEnd("Pirate " + str(hostSolverId) + " will spawn a new Quartermaster.")

		if hostSolverId == self.myId:
			file = open("./all.clues", "w")
			file.write(json.dumps(self.clues))
			file.close()
			file = open("./solved.clues", "w")
			file.write(json.dumps(self.solvedClues))
			file.close()
			time.sleep(1)
			os.system("./quartermaster.py --host " + self.myAddress[0] + " --clues all.clues --solved-clues solved.clues > qm.log &")
			self.host = self.myAddress[0]
		else:
			for i in self.pirates:
				if i["id"] == hostSolverId:
					self.host = i["address"]["host"]
					self.pirates.remove(i)

		self.printEnd("New host located at: " + self.host + ":" + str(self.port))
		# time.sleep(5)

	def closeSocket(self):
		try:
			# self.printEnd("Sent disconnect.")
			self.sendMessage("stop")
			self.mysocket.settimeout(5)

			while self.receiveMessage() != "stop-ack":
				pass

			self.printEnd("Client halted.")
		except socket.error:
			# self.printEnd("Socket error occurred while initiating shutdown!")
			pass
		except Exception as e:
			self.printEnd("Error occurred while initiating shutdown!")
			raise
		else:
			self.printEnd("Shutdown!")
		finally:
			try:
				self.mysocket.close()
			except Exception as e:
				self.printEnd("Error occurred while closing socket!")

			# self.stop = True

######################################################################################
#				MESSAGE OPERTIONS
######################################################################################
	def analyseMessage(self, message):
		try:
			command = message[:message.index(':')]
			message = message[message.index(':') + 1:]
		except:
			command = message
			message = ""

		if command == "your-id":
			self.myId = int(message)
			self.pirates = []
		elif command == "your-address":
			self.myAddress = literal_eval(message)
		elif command == "new-pirate":
			self.pirates.append(json.loads(message))
			self.printEnd("ADDED PIRATE: " + message)
		elif command == "remove-pirate":
			message = int(message)

			for x in xrange(0,len(self.pirates)):
				if message == self.pirates[x]["id"]:
					self.pirates.pop(x)
					self.printEnd("REMOVED PIRATE: " + str(message))
					break
		elif command == "clues":
			self.clues = json.loads(message)
			self.solvedClues = []
		elif command == "solved-clue":
			message = json.loads(message)
			found = False

			for i in self.solvedClues:
				if i["id"] == message["id"]:
					i["data"].extend(message["data"])
					found = True
					break

			if not found:
				self.solvedClues.append(message)
		elif command == "solved-clues":
			self.solvedClues = json.loads(message)
		elif command == "solve-clue":
			message = json.loads(message)
			pirateIndex = int(message["pirateIndex"])
			clueIndex = int(message["clueIndex"])
			solvedClue = self.solveClue(pirateIndex, clueIndex)
			return "validate-clue:" + json.dumps(solvedClue)
		elif command == "pass":
			return "request-clue"
		elif command == "wait":
			return "wait"
		elif command == "pirate-file":
			pirateFile = open("./data/crew/pirates.dat", "w")
			pirateFile.write(message)
			pirateFile.close()
			pass
		elif command == "ship-file":
			shipFile = open("./data/crew/ship.dat", "w")
			shipFile.write(message)
			shipFile.close()
		else:
			raise ValueError("Unknown command: " + command)

		return None

	def sendMessage(self, message):
		totalsent = 0
		message = str(len(message)) + "#" + message

		while totalsent < len(message):
			sent = self.mysocket.send(message[totalsent:])

			if sent == 0:
				raise socket.error

			totalsent = totalsent + sent

	def receiveMessage(self):
		chunks = []
		bytes_recd = 0
		msgLength = 0
		strLength = ""
		stop = False

		while not stop:
			charRead = ''.join(self.mysocket.recv(1))

			if charRead == "":
				raise socket.error
			elif charRead == "#":
				stop = True
			else:
				strLength += charRead

		msgLength = int(strLength)

		while bytes_recd < msgLength:
			chunk = self.mysocket.recv(min(msgLength - bytes_recd, 4096))

			if chunk == '':
				raise socket.error

			chunks.append(chunk)
			bytes_recd = bytes_recd + len(chunk)

		return ''.join(chunks)

######################################################################################
#				RUN OPERTIONS
######################################################################################
cs = ClueSolver()
cs.printEnd("Done.")
import threading
import socket
import time
import sys
import os
from time import gmtime, strftime
from datetime import datetime
import json

class ClientSocket ( threading.Thread ):
	stop = False
	pirateId = None
	currentClueId = None
	sendLock = threading.RLock()

	def printEnd(self, text, start="", end="\n"):
		currTime = strftime("%Y-%m-%d %H:%M:%S.", gmtime()) + str(datetime.now().microsecond)
		sys.stdout.write(start+ "(" + currTime + ") CS(" + str(self.pirateId) + "): " + text + end)
		sys.stdout.flush()

	def __init__(self, socket):
		threading.Thread.__init__(self)
		self.socket = socket

	def send(self, message):
		with self.sendLock:
			totalsent = 0
			sent = self.socket.send(str(len(message)) + "\n")
			while totalsent < len(message):
				sent = self.socket.send(message[totalsent:])
				if sent == 0:
					raise RuntimeError("socket connection broken")
				totalsent = totalsent + sent

	def receive(self):
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

	def run(self):
		stopFromClient = False
		try:
			self.printEnd("Started")
			
			while not self.stop:
				message = self.receive()
				try:
					command = message[:message.index(':')]
					message = message[message.index(':') + 1:]
				except: # Exception as e
					command = message
					message = ""
				
				if command == "request-clue":
					returnMsg = self.getClue()

					if not self.stop:
						message = "solve-clue:" + json.dumps(returnMsg)
				elif command == "validate-clue":
					self.validateClue(message)

					if not self.stop:
						returnMsg = self.getClue()

					if not self.stop:
						message = "solve-clue:" + json.dumps(returnMsg)
				elif command == "stop":
					self.stop = True
					stopFromClient = True
				elif command == "clues":
					ClientSocket.qm.clues = json.loads(message)
				else:
					raise ValueError("Invalid command: " + command)

				if not self.stop:
					self.send(message)

			self.printEnd("Shutting down.")
		finally:
			try:
				self.send("stop")
			except:
				pass

			self.socket.close()

			with ClientSocket.qmLock:
				for x in xrange(0,len(ClientSocket.qm.clientsockets)):
					if ClientSocket.qm.clientsockets[x].pirateId == self.pirateId:
						ClientSocket.qm.clientsockets.pop(x)
						self.printEnd("Removed myself from CS list.")
						break

			ClientSocket.qm.missedClues.append(self.currentClueId)
			ClientSocket.qm.broadcastToPirates("remove-pirate:" + str(self.pirateId))

	def getClue(self):
		clue = None

		if self.currentClueId != None:
			self.printEnd("Using old id")
			clue = self.currentClueId

		while clue == None and not self.stop:
			with ClientSocket.qmLock:
				if not self.stop:
					clueNum = ClientSocket.qm.currentClueId
					ClientSocket.qm.currentClueId = ClientSocket.qm.currentClueId + 1

					if clueNum < len(ClientSocket.qm.clues):
						clue = clueNum

			if clue == None and not self.stop:
				time.sleep(1)

		if not self.stop:
			self.printEnd("Clue #" + str(clue), "\r", "")
		else:
			self.printEnd("Requested to stop!")

		self.currentClueId = clue
			
		return clue

	def validateClue(self, message):
		with ClientSocket.qmLock:
			if not self.stop:
				ClientSocket.qm.broadcastToPirates("solved-clue:" + message, self.pirateId)
				ClientSocket.qm.solvedClues.append(json.loads(message))
				self.currentClueId = None

				if len(ClientSocket.qm.missedClues) > 0:
					self.currentClueId = ClientSocket.qm.missedClues.pop()
					self.printEnd("Picking up missed clue ID: " + str(self.currentClueId))

				if len(ClientSocket.qm.solvedClues) == len(ClientSocket.qm.clues):
					self.printEnd("Validating " + str(len(ClientSocket.qm.solvedClues)) + " clues", "\r", "\n")
					ClientSocket.qm.reworkSolvedClues()
					returnMsg = "{\"returnMsg\":" + ClientSocket.qm.tellRummy("-verify '" + json.dumps(ClientSocket.qm.solvedClues) + "'") + "}"
					returnMsg = json.loads(returnMsg)

					if returnMsg["returnMsg"]["status"] == "success":
						if "finished" in returnMsg["returnMsg"]:
							ClientSocket.qm.finish()
							self.printEnd("Solved all clues.", "\r", "\n")
						else:
							ClientSocket.qm.getClues()
							ClientSocket.qm.broadcastToPirates("clear-clues")
							ClientSocket.qm.broadcastToPirates("clues:" + json.dumps(ClientSocket.qm.clues))
							self.printEnd("All clues solved. Retrieved " + str(len(ClientSocket.qm.clues)) + " new clues.")
					else:
						ClientSocket.qm.addClues(returnMsg["returnMsg"]["data"])
						ClientSocket.qm.broadcastToPirates("clear-clues")
						ClientSocket.qm.broadcastToPirates("clues:" + json.dumps(ClientSocket.qm.clues))
						self.printEnd(str(len(ClientSocket.qm.clues)) + " clues were wrong.")

					ClientSocket.qm.solvedClues = []
					# sys.exit()
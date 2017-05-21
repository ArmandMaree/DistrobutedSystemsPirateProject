from datetime import datetime
import json
import socket
import sys
import threading
from time import gmtime, strftime

class ClientThread(threading.Thread):
	qm = None
	server = None

	def printEnd(self, text, start="", end="\n"):
		currTime = strftime("%Y-%m-%d %H:%M:%S.", gmtime()) + str(datetime.now().microsecond)
		sys.stdout.write(start+ "(" + currTime + ") CT(" + str(self.id) + "): " + text + end)
		sys.stdout.flush()

	def __init__(self, qm, server, mysocket, address):
		super(ClientThread, self).__init__()
		self.qm = qm
		self.server = server
		self.mysocket = mysocket
		self.address = address
		self.mysocket.settimeout(10)
		self.id = None
		self.stop = False
		self.stopped = False
		self.pendingMessages = []
		self.pendingMessagesLock = threading.RLock()

	def run(self):
		clue = None
		self.crashed = False
		clientShutdown = False

		while not self.stop:
			self.crashed = False
			try:
				message = self.receiveMessage()

				try:
					command = message[:message.index(':')]
					message = message[message.index(':') + 1:]
				except:
					command = message
					message = None

				if command == "request-clue":
					clue = self.qm.getNextClueId()

					if clue == None: # all clues for current map have been solved
						message = "wait" #force client to wait for command
					else:
						message = "solve-clue:{\"pirateIndex\":" + str(clue[0]) + ",\"clueIndex\":" + str(clue[1]) + "}"
				elif command == "validate-clue":
					clue = None
					if self.qm.addSolvedClue(json.loads(message)):
						message = None
						self.closeSocket() # will occur in next line
						self.server.shutdown()
						self.qm.shutdown()
					else:
						message = "pass" #force client to request a new clue
				elif command == "wait":
					clue = self.qm.getMissingClue()

					if clue == None: # all clues for current map have been solved
						message = "wait" #force client to wait for command
					else:
						message = "solve-clue:{\"pirateIndex\":" + str(clue[0]) + ",\"clueIndex\":" + str(clue[1]) + "}"
				elif command == "stop":
					message = "stop-ack"
					self.stop = True
					clientShutdown = True
				else:
					raise ValueError("Unknown command: " + command)

				if message != None:
					self.addPendingMessage(message)
					self.flushPendingMessages()
			except socket.timeout:
				self.printEnd("Read timeout!")
			except socket.error:
				self.printEnd("Socket error occurred!                         ", "\r", "\n")
				self.stop = True
				self.crashed = True
			except Exception as e:
				self.printEnd("Error occurred: " + str(e))
				self.stop = True #debug
				self.crashed = True
				raise #debug
			finally:
				if self.crashed and clue != None:
					self.qm.missedClueIds.append(clue)

		if not clientShutdown:
			self.closeSocket()

		self.stopped = True
		self.printEnd("Done.")

######################################################################################
#				SOCKET OPERTIONS
######################################################################################
	def closeSocket(self):
		try:
			# self.printEnd("Sent disconnect.")
			self.sendMessage("stop")

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

			self.stop = True
			self.server.removeClientThreadsFromList((self.id, self, self.address))

######################################################################################
#				MESSAGE OPERTIONS
######################################################################################

	def addPendingMessage(self, message):
		with self.pendingMessagesLock:
			self.pendingMessages.append(message)

	def flushPendingMessages(self):
		with self.pendingMessagesLock:
			while len(self.pendingMessages) > 0:
				message = self.pendingMessages.pop(0)
				self.sendMessage(message)

			# self.pendingMessages = []

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
import clientthread
from datetime import datetime
import json
import socket
import sys
import threading
from time import gmtime, strftime

class Server ( threading.Thread ):
	def printEnd(self, text, start="", end="\n"):
		currTime = strftime("%Y-%m-%d %H:%M:%S.", gmtime()) + str(datetime.now().microsecond)
		sys.stdout.write(start+ "(" + currTime + ") CommServer: " + text + end)
		sys.stdout.flush()

	def __init__(self, qm, host, port):
		super(Server, self).__init__()
		self.stop = False
		self.nextClientThreadId = 0
		self.qm = qm
		self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.serversocket.bind((host, port))
		self.serversocket.listen(5)
		self.clientThreads = []
		self.clientThreadsLock = threading.RLock()
		self.printEnd("Created.")

	def run(self, timeout = 5):
		self.serversocket.settimeout(timeout)
		self.printEnd("Waiting for clue solver.")
		
		while not self.stop:
			try:
				(clientsocket, address) = self.serversocket.accept()
			except socket.timeout:
				pass
			except KeyboardInterrupt:
				self.printEnd("Caught CTRL-C. Shutting down.")
				self.qm.shutdown()
				self.shutdown()
			except Exception as e:
				raise
			else:
				self.addClientThreadToList(clientsocket, address)
				if not self.stop:
					self.printEnd("Waiting for clue solver.")

		self.printEnd("Done.")

	def shutdown(self):
		self.stop = True
		
		with self.clientThreadsLock:
			for i in self.clientThreads:
				i[1].stop = True

		while len(self.clientThreads) > 0:
			pass

######################################################################################
#				CLIENT SOCKET OPERTIONS
######################################################################################
	def addClientThreadToList(self, clientsocket, address):
		with self.clientThreadsLock:
			clientThread = clientthread.ClientThread(self.qm, self, clientsocket, address)
			try: # to sync data with client
				clientThread.addPendingMessage("your-id:" + str(self.nextClientThreadId))
				clientThread.addPendingMessage("your-address:" + str(address))
				clientThread.addPendingMessage("clues:" + json.dumps(self.qm.clues))
				clientThread.addPendingMessage("solved-clues:" + json.dumps(self.qm.solvedClues))

				for i in self.clientThreads:
					clientThread.addPendingMessage("new-pirate:{\"id\":" + str(i[0]) + ",\"address\":{\"host\":\"" + i[2][0] + "\",\"port\":\"" + str(i[2][1]) + "\" } }")

				clientThread.addPendingMessage("pirate-file:" + self.getFileContent("./data/crew/pirates.dat"))
				clientThread.addPendingMessage("ship-file:" + self.getFileContent("./data/crew/ship.dat"))
				clientThread.addPendingMessage("pass")
				clientThread.flushPendingMessages()
				clientThread.id = self.nextClientThreadId
			except Exception as e:
				self.printEnd("New ClientSocket threw exception " + str(e) + " when syncing.")
				clientThread.stop = True
				raise # debug
			else: # if all data could be synced, then add to list
				message = "new-pirate:{\"id\":" + str(self.nextClientThreadId) + ",\"address\":{\"host\":\"" + address[0] + "\",\"port\":\"" + str(address[1]) + "\" } }"
				self.broadcastToClientSockets(message)
				self.clientThreads.append((self.nextClientThreadId, clientThread, address))
				self.nextClientThreadId += 1
				self.printEnd("New ClientSocket added at " + address[0] + ":" + str(address[1]) + ".", "\r")
				clientThread.start()

	def removeClientThreadsFromList(self, clientthread):
		with self.clientThreadsLock:
			clientthread[1].stop = True
			self.clientThreads = [i for i in self.clientThreads if i[0] != clientthread[0]]
			message = "remove-pirate:" + str(clientthread[0])
			self.broadcastToClientSockets(message)

######################################################################################
#				FILE OPERTIONS
######################################################################################
	def getFileContent(self, filename):
		with open(filename, "r") as myfile:
			return myfile.read()

######################################################################################
#				MESSAGE OPERTIONS
######################################################################################
	def broadcastToClientSockets(self, message):
		with self.clientThreadsLock:
			for i in self.clientThreads:
				try:
					i[1].addPendingMessage(message)
				except Exception as e:
					self.printEnd("ClientSocket #" + str(i[0]) + " at " + i[2][0] + ":" + str(i[2][1]) + " threw exception {" + str(e) + "} when broadcasting.")
					self.removeClientThreadsFromList(i)
		
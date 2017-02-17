import os
import time

class Pirate:
	"""docstring for Pirate"""
	numPirates = 0
	myId = 0

	def __init__(self):
		print("Pirate created!")
		myId = Pirate
		Pirate.numPirates = Pirate.numPirates + 1

	def tellQuarterMaster(self, message):
		sentmessage = False
		filename = "quartermaster.chat"
		filenameLock = filename + ".lock"

		if not os.path.exists(filenameLock):
			qmchat = open(filename, "w+")
			qmchat.close()

		while not sentmessage:
			try:
				os.rename(filename, filenameLock)
				qmchat = open(filenameLock, "a+")
				qmchat.write(message)
			except OSError as e:
				print("P(" + str(myId) + ": " + filename + " is locked.")
				time.sleep(1)
			finally:
				qmchat.close()
				os.rename(filenameLock, filename)
				sentmessage = True

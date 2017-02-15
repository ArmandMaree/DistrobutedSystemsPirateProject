import os
import time

class Pirate(object):
	"""docstring for Pirate"""
	numPirates = 0
	myId = 0
	quartermaster = None

	def __init__(self, quartermaster = None):
		print("Pirate created!")
		myId = Pirate
		self.quartermaster = quartermaster

	def tellQuarterMaster(self, message):
		readmessage = False
		filename = "./quartermaster.chat"
		filenameLock = filename + ".lock"

		while not readmessage:
			try:
				os.rename(filename, filenameLock)
				rummychat = open("rummy.chat.lock", "a+")
				rummychat.write(message)
			except OSError as e:
				print("QM: rummy.chat is locked.")
				time.sleep(1)
			finally:
				rummychat.close()
				os.rename(filenameLock, filename)
				readmessage = True

	def tellPirate(self, pirateId, message):
		readmessage = False
		filename = "./pirate" + pirateId + ".chat"
		filenameLock = filename + ".lock"

		while not readmessage:
			try:
				os.rename(filename, filenameLock)
				rummychat = open(filenameLock, "a+")
				rummychat.write(message)
			except OSError as e:
				print("QM: Pirate " + pirateId + " is locked.")
				time.sleep(1)
			finally:
				rummychat.close()
				os.rename(filenameLock, filename)
				readmessage = True

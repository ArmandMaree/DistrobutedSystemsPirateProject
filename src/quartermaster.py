import os
import time

from pirate import Pirate

class QuarterMaster(Pirate):
	"""docstring for QuarterMaster"""

	def __init__(self):
		super(QuarterMaster, self).__init__()
		print("Quarter Master created!")

	def tellRummy(self, message):
		readmessage = False
		filename = "./rummy.chat"
		filenameLock = filename + ".lock"

		while not readmessage:
			try:
				os.rename(filename, filenameLock)
				rummychat = open("rummy.chat.lock", "a+")
				rummychat.write("Q" + message)
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

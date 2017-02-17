#!/usr/bin/python
import os
import time
import json

from pirate import Pirate

class QuarterMaster:
	"""docstring for QuarterMaster"""

	def __init__(self):
		print("Quarter Master created!")
		self.tellRummy("-wake")

	def tellPirate(self, pirateId, message):
		sentmessage = False
		filename = "pirate_" + str(pirateId) + ".chat"
		filenameLock = filename + ".lock"

		if not os.path.exists(filenameLock):
			piratechat = open(filename, "w+")
			piratechat.close()

		while not sentmessage:
			try:
				os.rename(filename, filenameLock)
				piratechat = open(filenameLock, "a+")
				piratechat.write(message)
			except OSError as e:
				print("QM: '" + filename + "' is locked.")
			finally:
				piratechat.close()
				os.rename(filenameLock, filename)
				sentmessage = True
				print("QM: Message sent to pirate " + str(pirateId) + ": " + message)

	def tellRummy(self, message):
		rummyResponse = json.loads(os.popen("./rummy.pyc " + message).read())
		print "Rummy (" + rummyResponse["status"] + "): ", rummyResponse["message"]
		return json.dumps(rummyResponse)

print("Let's find that treasure!\n")
qm = QuarterMaster()
qm.tellPirate(1, "hello")
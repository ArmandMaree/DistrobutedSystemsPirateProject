#!/usr/bin/python

import os
import time
import sys

class Pirate:
	myId = 0

	def __init__(self):
		i = 1
		while i < len(sys.argv):
			if sys.argv[i] == "--id":
				i = i + 1
				myId = sys.argv[i]
			else:
				print("Argument " + str(i) + "(" + sys.argv[i] + ") is unknown.")

			i = i + 1

		print("Pirate " + str(myId) + " created!")

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

p = Pirate()

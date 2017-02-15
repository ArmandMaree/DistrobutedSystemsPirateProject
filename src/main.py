#!/usr/bin/python

import os
import time
import inspect
import sys

import quartermaster

print("Let's find that treasure!\n")

filename = "rummy.chat"
filenameLock = filename + ".lock"
rummychat = open(filename, "w+")
rummychat.close()

qm = quartermaster.QuarterMaster()
qm.tellRummy("./rummy.pyc -wake")
readmessage = False
stop = False

while not stop:
	while not readmessage:
		try:
			os.rename(filename, filenameLock)
			rummychat = open("rummy.chat.lock", "a+")
			quartermasterCommand = rummychat.read()
			print("READ: " + quartermasterCommand)
			readmessage = True

			if not quartermasterCommand.startswith("M"):
				rummychat.close()
				os.remove(filenameLock)
				rummychat = open(filenameLock, "w+")
				rummyResponse = os.popen(quartermasterCommand[1:]).read()
				print "rummy output:", rummyResponse
				rummychat.write("M" + rummyResponse)

		except OSError as e:
			print("M: rummy.chat is locked.")
			time.sleep(1)
		finally:
			rummychat.close()
			os.rename(filenameLock, filename)
			stop = True



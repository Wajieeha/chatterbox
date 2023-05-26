import os
import aiml
import os
import pyaiml21
from autocorrect import spell
from glob import glob
from pyaiml21 import Kernel
k = aiml.Kernel()
Bot = Kernel()
for name in glob("profiles.aiml"):
    Bot.learn_aiml(name)
while True:
    userIn = input("User > ")
    response = Bot.respond(userIn, 'User1')
    print('<Bot>', response)
    print()
    if response.lower() == 'bye see you again':
        break


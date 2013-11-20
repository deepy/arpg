from arpg.newrpg import RPGBotFactory
from twisted.internet import reactor
import ConfigParser
import sys

def main():
    Config = ConfigParser.ConfigParser()
    if len(sys.argv) == 2:
        Config.read(sys.argv[1])
    else:
        Config.read("config.ini")
    f = RPGBotFactory(Config.get("irc", "server"))
    #f2 = RPGBotFactory("Coldfront", "RPG","#rpg")
    reactor.connectTCP(f.server, 6667, f)
    #reactor.connectTCP("irc.coldfront.net", 6667, f2)
    reactor.run()

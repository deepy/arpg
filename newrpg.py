#!/usr/pkg/bin/python

# twisted imports
from twisted.words import service
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, defer

# system imports
import random, time, sys, sqlite3
from time import time, localtime, strftime #43200 = 12h

# database imports
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker


# useless stuff
#import twitter
import ConfigParser

# start doing session.close()

# templates
from jinja2 import Environment, FileSystemLoader

#Configurations
Config = ConfigParser.ConfigParser()
Config.read("config.ini")

# loading the mobile template
env = Environment(loader=FileSystemLoader(Config.get("web", "templatedirectory")))
template = env.get_template('mobile.tpl')
template_output = Config.get("web", "outputdirectory")

#sqlalchy start
db = create_engine(Config.get("db", "string"), echo=False)
Session = sessionmaker(bind=db,expire_on_commit=False)
Base = declarative_base(bind=db)


#sqlalchy end

# //sqlalchy notes
#  mytest = User("test", 1, 1, 1, 1, 1, 1, 1, 1, 1, 10, "1,2", 2, "ArloriaNET")
#  session.add(mytest)
#  session = Session()
#  mytest2 = session.query(User).filter_by(name='test').first()
#  session.commit() to save


# sqlalchy ORM start
class User(Base):
    __tablename__ = 'users'


    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(40), nullable=False)
    level = Column(Integer, nullable=False)
    clown_level = Column(Integer, nullable=False)
    cls = Column(Integer, nullable=False)
    charisma = Column(Integer, nullable=False)
    area = Column(Integer, nullable=False)
    exp = Column(Integer, nullable=False)
    gold = Column(Integer, nullable=False)
    weapon = Column( Integer, nullable=False)
    armor = Column(Integer, nullable=False)
    clchange = Column(Integer, nullable=False)
    classes = Column(String(80), nullable=False)
    faction = Column(Integer, nullable=False)
    age = Column(Integer, nullable=False)
    abtime = Column(Integer, nullable=False)
    helditem = Column(Integer, nullable=False)
    school = Column(Integer, nullable=False)
    network = Column(String(40), nullable=False)

    def __init__(self, name, level, clown_level, cls, charisma, area, exp, gold, weapon, armor, clchange, classes, faction, age, abtime, helditem, school, network):
        self.name = name
        self.level = level
        self.clown_level = clown_level
        self.cls = cls
        self.charisma = charisma
        self.area = area
        self.exp = exp
        self.gold = gold
        self.weapon = weapon
        self.armor = armor
        self.clchange = clchange
        self.classes = classes
        self.faction = faction
        self.age = age
        self.abtime = abtime
        self.helditem = helditem
        self.school = school
        self.network = network

    def __repr__(self):
        return "<User('%s: %s (%s)')>" % (self.name, self.level, self.network)

Base.metadata.create_all(db) #Uncomment this on the first run.
# sqlalchy ORM end

class RPGBot(irc.IRCClient):  
    nickname = "RPG"
    versionName = "RPGBot"
    versionNum = "(Guildbars)"
    fingerReply = "RPGBot (rpg@armchairs.be) - http://x13.se/~deepy/arpg/readme.txt"
    boot = int(time())

    def init(self):
        """ Two times Two is cantaloupe. """
        self.nickname = self.factory.nickname
        self.users = {}
        self.school = {}
        self.factions = {}
        self.feats = {}
        self.crusaders = []
        self.arbiters = []
        
        self.nextfight = 0
        
        self.msg_channel = 1
        self.msg_user = 1
        
        self.weapons = ["club","magic staff","Scroll of Protection","Wall Street Journal",
                        "+8 Divine Sword of Basketweaving","cursed urn","dumpster truck","wooden plank",
                        "Missed Appointment","HTML Validator"]
        self.actions = ["beat down","mutilated","demolished","lightly injured","barely scratched","violated"]
        
        # abuse!
        #self.twat = twitter.Api(username='activerpg', password='meowkitt')
        
        self.feats[2] = ("castlepermit","backstagecastle","minortax") #Noble
        self.feats[3] = ("minortax","lawenforce","warrior") #Citywatch
        self.feats[4] = ("hugetax","rogue") #Merchant
        self.feats[5] = ("magic") #Mage
        self.feats[6] = ("randomrob","rogue") #Waif
        self.feats[7] = ("counterspell","hex") #Shaman
        self.feats[10] = ("nodrown","freeboat","rogue") #Sailor
        self.feats[11] = ("herbalism") #Herbalist, tax reduc for apotekare
        self.feats[12] = ("rogue") #Bard
        self.feats[14] = ("freefarsight","magic") #Farseer
        self.feats[15] = ("randomrob","rogue") #Thief
        self.feats[20] = ("freetele","freefarsight","magic","castlepermit") #Scribe
        
        self.factions[10] = ("buffalop") #Udderlorn (Buffaloops)
        self.factions[15] = ("lizkoot") #V'Gaes (Liz'Koots)

    def cron(self):
        print self.nextfight
        if self.nextfight <= int(time()):
            self.rpg_randomfight()
            self.nextfight = int(time()+14400)

    def pump(self):
        self.cron() #TODO: weakrefs.

    def connectionMade(self):
        self.init()
        self.nickname = self.factory.nickname
        irc.IRCClient.connectionMade(self)
        sys.stdout.write("[connected]\n")

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.msg("NickServ", "identify %s" % Config.get("nickserv", "password"))
        self.mode(self.nickname, True, "R")
        self.join(self.factory.channel)
        self.join("arpg")
        self.join("#crusaders,#arbiters")

    def irc_RPL_WHOISCHANNELS(self, prefix, params):
        nick = params[1]
        channels = params[2].split(None)
        #print channels


    def irc_307(self, prefix, params):
        if params[2] == 'is a registered nick':
            self.rpg_login(params[1])
        else:
            pass

    def irc_RPL_WHOREPLY(self, prefix, params):
        #print "WHO: %s (%s)" % (params, self.factory.network)
        if "r" in params[6]:
            self.rpg_login(params[5])
        #else:
        #    print "WHO: %s" % params

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        # Check to see if they're sending me a private message
        if channel.lower() == self.nickname.lower():
            try:
                if self.users[user]:
                    msg = msg.strip()
                    command, sep, rest = msg.partition(' ')
                    func = getattr(self, 'command_' + command, None)
                    if func is None:
                        self.command(user, msg, 1)
                    else:
                        d = defer.maybeDeferred(func, user, rest) #FIX
                    #d.addErrback(self._show_error)
            except KeyError:
                command, sep, rest = msg.partition(' ')
                print command
                func = getattr(self, 'command_' + command, None)
                if func is None:
                    self.command(user, msg, 0)
                else:
                    d = defer.maybeDeferred(func, user, rest) #FIX
                    #d.addErrback(self._show_error)
        elif channel.lower() == self.factory.channel.lower():
            try:
                if user in self.users:
                    session = Session()
                    gainedexp = int((len(set(msg.lower()))+5) * self.users[user].charisma / 5)
                    self.rpg_awardexp(user, gainedexp)
                    if random.randint(0,35) == 18:
                        if self.users[user].charisma+1 >= 20:
                            self.users[user].clown_level += 1
                            self.users[user].charisma = 6
                            print "%s gained a clown level!" % user
                            self.notify("%s gained a class level!" % str(user))
                        else:
                            self.users[user].charisma += 1
                            print "%s gained a charisma!" % user
                            self.notify("%s gained a charisma!" % str(user))
                    self.pump()
                    session.add(self.users[user])
                    session.commit()
                    session.close()
                    print "<%s> %s (%s)" % (user, msg, gainedexp)
            except (ValueError, KeyError):
                session.close()
                pass #DEBUG ATTEMPT
        return

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        self.rpg_logout(prefix.split('!')[0])

    def irc_JOIN(self, prefix, params):
        #self.whois(prefix.split('!')[0])
        #pass
        if params[0].lower() == self.factory.channel.lower():
            self.sendLine("WHO %s" % self.factory.channel)
        elif params[0].lower() == "#crusaders".lower():
            try:
                if self.users[prefix.split('!')[0]]:
                    if prefix.split('!')[0] in self.crusaders:
                        pass
                    else:
                        self.kick("#arbiters", prefix.split('!')[0], "Not one of the Arbiters!")
            except KeyError:
                if prefix.split('!')[0] != "RPG":
                    self.kick("#crusaders", prefix.split('!')[0], "Not one of the Crusader!")
        elif params[0].lower() == "#arbiters".lower():
            try:
                if self.users[prefix.split('!')[0]]:
                    if prefix.split('!')[0] in self.arbiters:
                        pass
                    else:
                        self.kick("#arbiters", prefix.split('!')[0], "Not one of the Arbiters!")
            except KeyError:
                if prefix.split('!')[0] != "RPG":
                    self.kick("#arbiters", prefix.split('!')[0], "Not one of the Arbiters!")

    def irc_PART(self, prefix, params):
        if params[0].lower() == self.factory.channel:
            self.rpg_logout(prefix.split('!')[0])

    def irc_QUIT(self, prefix, params):
        self.rpg_logout(prefix.split('!')[0])

    def irc_WHOISCHANNELS(self, prefix, params):
        """Called when the WHOIS results are returned?"""
        pass

    def userKicked(self, kickee, channel, kicker, message):
        if channel == self.factory.channel:
            self.rpg_logout(kickee)

    def rpg_randomfight(self):
        if len(self.users) > 1:
            self.rpg_fight(random.sample(self.users.items(), 2))

    def rpg_fight(self, user):
        session = Session()
        #self.fightbuf = session.query(User).filter_by(name=user, network=self.factory.network).first()
        if random.randint(0,1) == 1:
            self.notify("%s %s %s with a %s." % ( str(user[0][0]), random.choice(self.actions), str(user[1][0]), random.choice(self.weapons) ))
        session.commit()
        session.close()

    def rpg_logout(self, user):
        try:
            del self.users[user]
        except (ValueError, KeyError):
            pass
        try:
            self.crusaders.remove(user)
        except ValueError:
            pass
        try:
            self.arbiters.remove(user)
        except ValueError:
            pass        
        #self.users_html() TEMP OFF

    def rpg_login(self, user):
        try:
            if self.users[user]:
                pass
        except KeyError:
            session = Session()
            self.resultsbuf = session.query(User).filter_by(name=user, network=self.factory.network).first()
            if not (self.resultsbuf):
                pass
            else:
                self.users[user] = self.resultsbuf
                self.users_html()
                if self.resultsbuf.faction == 1:
                    self.crusaders.append(user)
                elif self.resultsbuf.faction == 2:
                    self.arbiters.append(user)
                if self.resultsbuf.school != 0:
                    self.school[user] = int(self.resultsbuf.school)
                print self.resultsbuf.level, self.rpg_checkclass(self.resultsbuf.cls), self.resultsbuf.name
                self.notify2( "%s the level %s %s logged in." % (str(self.resultsbuf.name), str(self.resultsbuf.level), str(self.rpg_checkclass(self.resultsbuf.cls))) )
            session.close()

    def rpg_checkclass(self, pclass):
        """ Returns name of classnumber. """
        if pclass == 0:
            pass
        elif pclass == 1:
            return "Peasant" #Normal tax, 25%
        elif pclass == 2:
            return "Noble"
        elif pclass == 3:
            return "Citywatch" #Warrior, small discount on tax (20% tax)
        elif pclass == 4:
            return "Merchant" #Huge tax discount (10% tax)
        elif pclass == 5:
            return "Mage" #Magics
        elif pclass == 6:
            return "Waif" #random chance to rob people
        elif pclass == 7:
            return "Shaman" #Magics
        elif pclass == 10:
            return "Sailor" #Swore enough, drowned enough
        elif pclass == 11:
            return "Herbalist" #Herbalism, healer
        elif pclass == 12:
            return "Bard"
        elif pclass == 13:
            return "Tailor"
        elif pclass == 14:
            return "Farseer"
        elif pclass == 15:
            return "Thief" #random chance to rob people
        elif pclass == 20:
            return "Scribe" #Developer

    def rpg_classname(self, pclass):
        """ Returns classnumber of name. """
        if pclass == 0:
            pass
        elif pclass == "Peasant":
            return 1
        elif pclass == "Noble":
            return 2 
        elif pclass == "Citywatch":
            return 3
        elif pclass == "Merchant":
            return 4
        elif pclass == "Mage":
            return 5
        elif pclass == "Waif":
            return 6
        elif pclass == "Shaman":
            return 7
        elif pclass == "Sailor":
            return 10
        elif pclass == "Herbalist":
            return 11
        elif pclass == "Bard":
            return 12
        elif pclass == "Tailor":
            return 13
        elif pclass == "Farseer":
            return 14
        elif pclass == "Thief":
            return 15
        elif pclass == "Scribe":
            return 20

    def rpg_checkfeats(self, pclass):
        if int(pclass) in self.feats:
            return self.feats[pclass]
        else:
            return "none"

    def rpg_getlegitclass(self, user, type):
        legitclasses = [int(legclass) for legclass in self.users[user].classes.split(',')]
        legitclbuff = ""
        if type == 1:
            return legitclasses
        if type == 2:
            for legitclass in legitclasses:
                legitclbuff += self.rpg_checkclass(int(legitclass)) + " "
            return legitclbuff

    def rpg_awardexp(self, user, exp):
        """ Awards user experience. """
        session = Session()
        self.users[user].exp += exp
        if self.rpg_checklevel(self.users[user].level, exp+self.users[user].exp) == 1:
            self.users[user].level += 1
            print "%s is now level: %s" % (user, self.users[user].level)
            if self.msg_user == 1:
                self.notice(user, "Congratulations! You gained level %s" % self.users[user].level)
            self.notify("%s gained level %s!" % (str(user), str(self.users[user].level)))
            self.users_html()
        session.merge(self.users[user])
        session.commit()
        session.close()

    def rpg_changeclass(self, user, nclass):
        """ Attempts to change user's class. """
        session = Session()
        try:
            if self.users[user]:
                if self.users[user].clown_level > self.users[user].clchange:
                    if nclass in self.rpg_getlegitclass(user, 1):
                        self.users[user].cls = nclass
                        self.msg(user, "Congratulations, you are now a %s." % self.rpg_checkclass(nclass))
                        self.notify("%s is now a %s." % (str(user), str(self.rpg_checkclass(nclass))) )
                        session.merge(self.users[user])
                        session.commit()
                        session.close()
                        self.users_html()
                    else:
                        self.msg(user, "You can't change into that class.")
                        session.close()
                else:
                    session.close()
                    self.msg(user, "You're not allowed to change class at the moment.")
        except KeyError:
            session.close()
            #pass #DEBUG ATTEMPT

    def notify(self, message):
        """ One up the twatter. """
        if self.msg_channel == 1:
            self.msg("#arpg", message)
        #print self.twat.PostUpdate(message).text

    def notify2(self, message):
        """ Twitter free notification. """
        if self.msg_channel == 1:
            self.msg("#arpg", message)

    def rpg_changeschool(self, user, message):
        """ Change Guild. """
        if user in self.users:
            if message == "Mages":
                choice = 1
            elif message == "Warriors":
                choice = 2
            elif message == "Thieves":
                choice = 3
            else:
                return "Invalid choice."
            if choice:
                self.school[user] = choice
                session = Session()
                session.add(self.users[user])
                session.commit()
                session.close()
                return "Updated Guild choice."

    def rpg_checklevel(self, level, exp):
        """ Harcoded level tables. """
        if level == 1 and exp >= 100:
            return 1
        elif level == 2 and exp >= 200:
            return 1
        elif level == 3 and exp >= 400:
            return 1
        elif level == 4 and exp >= 800:
            return 1
        elif level == 5 and exp >= 1500:
            return 1
        elif level == 6 and exp >= 2600:
            return 1
        elif level == 7 and exp >= 4200:
            return 1
        elif level == 8 and exp >= 6400:
            return 1
        elif level == 9 and exp >= 9300:
            return 1
        elif level == 10 and exp >= 13000:
            return 1
        elif level == 11 and exp >= 17600:
            return 1
        elif level == 12 and exp >= 23200:
            return 1
        elif level == 13 and exp >= 29900:
            return 1
        elif level == 14 and exp >= 37800:
            return 1
        elif level == 15 and exp >= 47000:
            return 1
        elif level == 16 and exp >= 57600:
            return 1
        elif level == 17 and exp >= 69700:
            return 1
        elif level == 18 and exp >= 83400:
            return 1
        elif level == 19 and exp >= 98800:
            return 1
        elif level == 20 and exp >= 116000:
            return 1
        elif level == 21 and exp >= 135100:
            return 1
        elif level == 22 and exp >= 156200:
            return 1
        elif level == 23 and exp >= 179400:
            return 1
        elif level == 24 and exp >= 204800:
            return 1
        elif level == 25 and exp >= 232500:
            return 1
        elif level == 26 and exp >= 262600:
            return 1
        elif level == 27 and exp >= 295200:
            return 1
        elif level == 28 and exp >= 330400:
            return 1
        elif level == 29 and exp >= 368300:
            return 1
        elif level == 30 and exp >= 409000:
            return 1
        elif level == 31 and exp >= 452600:
            return 1
        elif level == 32 and exp >= 499200:
            return 1
        elif level == 33 and exp >= 548900:
            return 1
        elif level == 34 and exp >= 601800:
            return 1
        elif level == 35 and exp >= 658000:
            return 1
        elif level == 36 and exp >= 717600:
            return 1
        elif level == 37 and exp >= 780700:
            return 1
        elif level == 38 and exp >= 847400:
            return 1
        elif level == 39 and exp >= 917800:
            return 1
        elif level == 40 and exp >= 992000:
            return 1
        elif level == 41 and exp >= 1070100:
            return 1
        elif level == 42 and exp >= 1152200:
            return 1
        elif level == 43 and exp >= 1238400:
            return 1
        elif level == 44 and exp >= 1328800:
            return 1
        elif level == 45 and exp >= 1423500:
            return 1
        elif level == 46 and exp >= 1522600:
            return 1
        elif level == 47 and exp >= 1626200:
            return 1
        elif level == 48 and exp >= 1734400:
            return 1
        elif level == 49 and exp >= 1847300:
            return 1
        else:
            return 0


    def users_html(self):
        self.f = open("%s/%s/online.txt" % (template_output, self.factory.network), "w")
        self.buffer = "Users online:\n"
        for user in self.users:
            self.buffer += "%s(%s) " % (user, self.users[user].level)
        self.failbuffer = self.buffer
        self.buffer += "\nLast updated: %s" % (strftime("%a, %d %b %Y %H:%M:%S", localtime()))
        self.f.write(self.buffer)
        self.f.close()
        self.html_fulldump() #T!EMP OFF
        #self.factions_html() TEMP OFF
        #self.html_m_online(self.failbuffer.split(" ")) TEMP OFF

    def html_mobile(self):
        pass

    def html_m_online(self, listauser):
        self.f = open("%s/m/%s/online.html" % (template_output, self.factory.network), "w")
        self.buflist = []
        #for item in self.factions:
        #    self.buflist.append(listitem("#", item))
        self.f.write(template.render(title="Online users", navigation= [listitem("index.html", "Home")], pretext=listauser ))
        self.f.close()

    def html_m_user(self, userlist):
        self.f = open("%s/m/%s/users.html" % (template_output, self.factory.network), "w")
        self.f.write(template.render(title="Online users", navigation= [listitem("index.html", "Home")], pretext=userlist ))
        self.f.close()

    def html_fulldump(self):
        session = Session()
        self.f = open("%s/%s/users.txt" % (template_output, self.factory.network), "w")
        self.buffer = "IRCRPG players:\n"
        self.classbuff = ""
        for row in session.query(User).filter_by(network=self.factory.network).order_by(User.level.desc()).all():
            if row.cls != 0:
                self.classbuff = self.rpg_checkclass(row.cls)+" "
            #Gold formula: int(round(n, 1 - int(math.log10(n))))
            self.buffer += "%s%s, level: %s.%s (%s)\n" % (self.classbuff, row.name, row.level, row.clown_level, int(float("%.1e" % row.gold)))
        self.f.write(self.buffer)
        self.f.close()
        self.html_m_user(self.buffer)
        session.close()

    def whois(self, nickname, server=None):
        if server is None:
            self.sendLine('WHOIS ' + nickname)
        else:
            self.sendLine('WHOIS %s %s' % (server, nickname))

    def kick(self, channel, user, reason=None):
        if channel[0] not in '&#!+': channel = '#' + channel
        if reason:
            self.sendLine("KICK %s %s :%s" % (channel, user, reason))
        else:
            self.sendLine("KICK %s %s" % (channel, user))

    def command(self, user, msg, status):
        session = Session()
        self.messbuf = msg.split(" ", 1)
        if (self.messbuf[0] == "die"):
            if user == "Cat":
                reactor.stop()
        elif (self.messbuf[0] == "fight"):
            if user == "Cat":
                self.rpg_randomfight()
        elif (self.messbuf[0] == "pump"):
            if user == "Cat":
                self.pump()
        elif (self.messbuf[0] == "online"):
            self.msg(user, str(self.users))
        elif (self.messbuf[0] == "sonline"):
            self.msg(user, str(self.school))
        elif (self.messbuf[0] == "login"):
            self.whois(user)
        elif (self.messbuf[0] == "classes"):
            try:
                if self.users[user]:
                    self.msg(user, self.rpg_getlegitclass(user, 2))
            except KeyError:
                session.close()
        elif (self.messbuf[0] == "class"):
            try:
                self.rpg_changeclass(user, self.rpg_classname(self.messbuf[1]))
            except ValueError:
                session.close()
                self.msg(user, "You are allowed to change class once per every cl.")
        elif (self.messbuf[0] == "guild"):
            try:
                self.msg(user, self.rpg_changeschool(user, self.messbuf[1]))
            except IndexError:
                self.msg(user, "Error, valid choices are: mages, warriors, thieves.")
        elif (self.messbuf[0] == "alogout"):
            if user == "Cat":
                self.rpg_logout(self.messbuf[1])
        elif (self.messbuf[0] == "achschool"):
            if user == "Cat":
                self.rpg_changeschool(user, self.messbuf[1])
        elif (self.messbuf[0] == "aglc"):
            self.msg(user, self.rpg_getlegitclass(self.messbuf[1], 1))
        elif (self.messbuf[0] == "aglcl"):
            self.msg(user, self.rpg_getlegitclass(self.messbuf[1], 2))
        elif (self.messbuf[0] == "online"):
            self.msg(user, int(time()) - self.boot)
        else:
            if user.find("Serv") == -1:
                self.msg(user, "Commands are: register, classes, guild, class")
        session.close() #DEBUG ATTEMPT

    def command_test(self, user, rest):
        print "yes"
        print rest
        print user

    def command_html(self, user, rest):
        if user == "Cat":
            command = rest.partition(' ')
            if command == "users":
                self.users_html()
            elif command == "full":
                self.html_fulldump()

    def command_register(self, user, rest):
        session = Session()
        if not (session.query(User).filter_by(name=user, network=self.factory.network).first()):
            self.msg(user, "Registering you.")
            session.add(User(user, 1, 0, 1, 6, 1, 0, 0, 1, 1, 0,'1,3,5,6',0,int(time()),int(time()), 0, 0, self.factory.network))
            session.commit()
            self.sendLine("WHO %s" % self.factory.channel)
        else:
            self.msg(user, "Already registered.")
        session.close()

class listitem:
    href = "#"
    caption = "link"

    def __init__(self, href, caption):
        self.href = href
        self.caption = caption


class RPGBotFactory(protocol.ClientFactory):

    # I like having a comment here
    protocol = RPGBot

    def __init__(self, network, nickname, channel):
        self.network = network
        self.channel = channel
        self.nickname = nickname
    
    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


if __name__ == '__main__':
    f = RPGBotFactory("ArloriaNET", Config.get("irc", "nickname"), Config.get("irc", "channel"))
    #f2 = RPGBotFactory("Coldfront", "RPG","#rpg")
    
    # connect factory to this host and port
    reactor.connectTCP(Config.get("irc", "server"), 6667, f)
    #reactor.connectTCP("irc.coldfront.net", 6667, f2)
    # run bot
    reactor.run()

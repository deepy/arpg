#!/usr/bin/env python

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

# game imports
import arpg.events as events
import arpg.modules.notify as notify

import ConfigParser
import os

# templates
from jinja2 import Environment, FileSystemLoader

#Configurations
Config = ConfigParser.ConfigParser()
if len(sys.argv) == 2:
    Config.read(sys.argv[1])
else:
    Config.read("config.ini")

# loading the mobile template
env = Environment(loader=FileSystemLoader(Config.get("web", "templatedirectory")))
template = env.get_template('mobile.tpl')
template_output = Config.get("web", "outputdirectory")

# SQLAlchemy
db = create_engine(Config.get("db", "string"), echo=False)
Session = sessionmaker(bind=db,expire_on_commit=False)
Base = declarative_base(bind=db)

class Quest:
    def __init_(self, type, winners=False):
        self.finished = []
        self.progress = {}

    def progress(self, user, progress):
        pass

    def _finish(self):
        pass

class Guild(Base):
    __tablename__ = 'guilds'

    id = Column(Integer, Sequence('guild_id_seq'), primary_key=True)
    name = Column(String(40), nullable=False)
    shortname = Column(String(10), nullable=False)
    owner = Column(Integer, nullable=False)
    network = Column(String(40), nullable=False)

    def __init__(self, owner):
        self.owner = owner

    def __repr__(self):
        return "<Guild('%s <%s> (%s))')>" % (self.name, self.shortname, self.network)

class GuildInvite(Base):
    __tablename__ = 'guildinvites'

    id = Column(Integer, Sequence('guild_id_seq'), primary_key=True)
    guild = Column(String(40), nullable=False)
    target = Column(String(40), nullable=False)
    inviter = Column(String(40), nullable=False)
    network = Column(String(40), nullable=False)

    def __init__(self, guild, target, inviter, network):
        self.guild = guild
        self.target = target
        self.inviter = inviter
        self.network = network

    def __repr__(self):
        return "<GuildInvite('%s: %s (%s))')>" % (self.guild, self.target, self.network)

class Names(Base):
    __tablename__ = 'names'

    id = Column(Integer, Sequence('name_id_seq'), primary_key=True)
    parent = Column(String(40), nullable=False)
    name = Column(String(40), nullable=False)
    network = Column(String(40), nullable=False)

    def __init__(self, parent, name, network):
        self.parent = parent
        self.name = name
        self.network = network

    def __repr__(self):
        return "<Name('%s: %s (%s)')>" % (self.parent, self.name, self.network)

class User(Base):
    __tablename__ = 'users'


    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(40), nullable=False)
    level = Column(Integer, nullable=False)
    clown_level = Column(Integer, nullable=False)
    cls = Column(Integer, nullable=False)
    charisma = Column(Integer, nullable=False)
    exp = Column(Integer, nullable=False)
    gold = Column(Integer, nullable=False)
    clchange = Column(Integer, nullable=False)
    classes = Column(String(80), nullable=False)
    faction = Column(Integer, nullable=False)
    age = Column(Integer, nullable=False)
    network = Column(String(40), nullable=False)
    guild = Column(String(40), nullable=True, default=None)
    quests_completed = Column(Integer, nullable=False, default=0)

    def __init__(self, name, network):
        self.name = name
        self.level = 1
        self.clown_level = 0
        self.cls = 1
        self.charisma = 6
        self.exp = 0
        self.gold = 0
        self.clchange = 0
        self.classes = '1,3,5,6'
        self.faction = 0
        self.age = int(time())
        self.network = network

    def __repr__(self):
        return "<User('%s: %s (%s)')>" % (self.name, self.level, self.network)

Base.metadata.create_all(db)
from functools import wraps

# decorators

def adminOnly(f):
    def check(*args, **kwargs):
        if args[1] == Config.get(args[0].factory.server, "admin"):
            return f(*args, **kwargs)
        return
    return check

class RPGBot(irc.IRCClient):  
    nickname = "RPG"
    versionName = "RPGBot"
    versionNum = "(Guildbars)"
    fingerReply = "RPGBot (rpg@armchairs.be) - http://x13.se/~deepy/arpg/readme.txt"
    boot = int(time())

    def p_decorate(func):
        def func_wrapper(*args, **kwargs):
            print "<p>{0}</p>".format(func(*args, **kwargs))
        return func_wrapper


    def init(self):
        """ Two times Two is cantaloupe. """
        self.nickname = self.factory.nickname
        self.output_channel = Config.get(self.factory.server, "output")
        self.users = {}
        self.commonusers = []
        self.factions = {}
        self.feats = {}
        self.crusaders = []
        self.arbiters = []
        
        self.events = events.Manager()
        self.events.RegisterListener(self)
        self.notifications = notify.Handler(self.events)

        self.nextfight = 0
        
        self.msg_channel = 1
        self.msg_user = 1
        
        self.leveltable = {
            1: 100,
            2: 200,
            3: 400,
            4: 800,
            5: 1500,
            6: 2600,
            7: 4200,
            8: 6400,
            9: 9300,
            10: 13000,
            11: 17600,
            12: 23200,
            13: 29900,
            14: 37800,
            15: 47000,
            16: 57600,
            17: 69700,
            18: 83400,
            19: 98800,
            20: 116000,
            21: 135100,
            22: 156200,
            23: 179400,
            24: 204800,
            25: 232500,
            26: 262600,
            27: 295200,
            28: 330400,
            29: 368300,
            30: 409000,
            31: 452600,
            32: 499200,
            33: 548900,
            34: 601800,
            35: 658000,
            36: 717600,
            37: 780700,
            38: 847400,
            39: 917800,
            40: 992000,
            41: 1070100,
            42: 1152200,
            43: 1238400,
            44: 1328800,
            45: 1423500,
            46: 1522600,
            47: 1626200,
            48: 1734400,
            49: 1847300,
        }

        self.classlist = {
            "Peasant": 1,
            "Noble": 2,
            "Citywatch": 3,
            "Merchant": 4,
            "Mage": 5,
            "Waif": 6,
            "Shaman": 7,
            "Sailor": 10,
            "Herbalist": 11,
            "Bard": 12,
            "Tailor": 13,
            "Farseer": 14,
            "Thief": 15,
            "Scribe": 20
        }

        self.inverseclass = {v: k for k, v in self.classlist.items()}

        self.weapons = ["club","magic staff","Scroll of Protection","Wall Street Journal",
                        "+8 Divine Sword of Basketweaving","cursed urn","dumpster truck","wooden plank",
                        "Missed Appointment","HTML Validator"]
        self.actions = ["beat down","mutilated","demolished","lightly injured","barely scratched","violated","laminated"]
        
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
        self.guilds = {}

        session = Session()

        for guild in session.query(Guild).filter_by(network=self.factory.network).all():
            self.guilds[guild.shortname] = guild

        session.close()

    def cron(self):
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
        if Config.get(self.factory.server, "service") == "nickserv":
            self.msg("NickServ", "identify %s" % Config.get(self.factory.server, "nickpass"))
            self.mode(self.nickname, True, "R")
        for channel in self.factory.channels:
            self.join(channel)
            self.sendLine("WHO %s %%a" % channel)
        self.join(Config.get(self.factory.server, "output"))
        self.join(Config.get(self.factory.server, "crusaders"))
        self.join(Config.get(self.factory.server, "arbiters"))

    def irc_307(self, prefix, params):
        # Rizon's equivalent of 330.
        # irc_330(prefix, params)
        if params[2] == 'is a registered nick':
            self.rpg_login(params[1], params[1])
        else:
            pass

    def irc_354(self, prefix, params):
        # FreeNode, WHO #channel %na
        if self.factory.type == "ircd-seven":
            try:
                if params[2] != "0":
                    self.rpg_login(params[1], params[2])
            except IndexError:
                pass

    def irc_RPL_WHOISCHANNELS(self, prefix, params):
        if self.factory.type in ["ircd-seven", "rizon"]:
            for channel in self.factory.channels:
                if channel+" " in params[2]:
                    self.commonusers.append(params[1])
                    return True

    def irc_330(self, prefix, params):
        # irc_RPL_WHOISACCOUNT. ircu, used at FreeNode.
        if self.factory.type == "ircd-seven":
            if params[1] in self.commonusers:
                self.rpg_register(params[2], None)
                try:
                    self.commonusers.remove(params[1])
                except ValueError:
                    pass
        if self.factory.type == "rizon":
            print params

    def irc_RPL_WHOREPLY(self, prefix, params):
        #print "WHO: %s (%s)" % (params, self.factory.network)
        if self.factory.type in ["unreal","rizon"]:
            if "r" in params[6]:
                self.rpg_login(params[5], params[5])

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        # Check to see if they're sending me a private message
        if channel.lower() == self.nickname.lower():
            if user.find("Serv") == -1:
                try:
                    if self.users[user]:
                        isAuthenticated = True
                except KeyError:
                    isAuthenticated = False

                msg = msg.strip()
                command, sep, rest = msg.partition(' ')
                function = getattr(self, 'command_' + command, None)
                if function is None:
                    self.events.Post(events.Command(user=user, command=command, parameters=rest, authenticated=isAuthenticated))
                else:
                    d = defer.maybeDeferred(function, user, rest, isAuthenticated)
                    #d.addErrback(self._show_error)
        elif channel.lower() in self.factory.channels:
            try:
                if user in self.users:
                    session = Session()
                    gainedexp = int((len(set(msg.lower()))+5) / 4)
                    self.rpg_awardexp(user, gainedexp)
                    #self.pump()
                    session.add(self.users[user])
                    session.commit()
                    session.close()
                    print "%s <%s> %s (%s)" % (channel.lower(), user, msg, gainedexp)
            except (ValueError, KeyError):
                session.close()
        return

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        self.rpg_logout(prefix.split('!')[0])

    def irc_JOIN(self, prefix, params):
        if params[0].lower() in self.factory.channels:
            self.sendLine("WHO %s %%na" % params[0])
        elif params[0].lower() == Config.get(self.factory.server, "crusaders").lower():
            try:
                if self.users[prefix.split('!')[0]]:
                    if prefix.split('!')[0] not in self.crusaders:
                        self.kick(Config.get(self.factory.server, "crusaders"), prefix.split('!')[0], "Not one of the Crusaders!")
            except KeyError:
                if prefix.split('!')[0] != self.nickname:
                    self.kick(Config.get(self.factory.server, "crusaders"), prefix.split('!')[0], "Not one of the Crusaders!")
        elif params[0].lower() == Config.get(self.factory.server, "arbiters").lower():
            try:
                if self.users[prefix.split('!')[0]]:
                    if prefix.split('!')[0] not in self.arbiters:
                        self.kick(Config.get(self.factory.server, "arbiters"), prefix.split('!')[0], "Not one of the Arbiters!")
            except KeyError:
                if prefix.split('!')[0] != self.nickname:
                    self.kick(Config.get(self.factory.server, "arbiters"), prefix.split('!')[0], "Not one of the Arbiters!")

    def irc_PART(self, prefix, params):
        if params[0].lower() in self.factory.channels:
            self.rpg_logout(prefix.split('!')[0])

    def irc_QUIT(self, prefix, params):
        self.rpg_logout(prefix.split('!')[0])

    def userKicked(self, kickee, channel, kicker, message):
        if channel in self.factory.channels:
            self.rpg_logout(kickee)

    def rpg_randomfight(self):
        if len(self.users) > 1:
            self.rpg_fight(random.sample(self.users.items(), 2))

    def rpg_fight(self, user):
        session = Session()
        #self.fightbuf = session.query(User).filter_by(name=user, network=self.factory.network).first()
        if random.randint(0,1) == 1:
            self.events.Post(events.Message("%s %s %s with a %s." % ( str(user[0][0]), random.choice(self.actions), str(user[1][0]), random.choice(self.weapons) ), "output"))
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

    def rpg_login(self, nickname, user):
        if nickname not in self.users:
            session = Session()
            resultsbuf = session.query(Names).filter(func.lower(Names.name) == func.lower(user), func.lower(Names.network) == func.lower(self.factory.network)).first()
            if not (resultsbuf):
                resultsbuf = session.query(User).filter(func.lower(User.name) == func.lower(user), func.lower(User.network) == func.lower(self.factory.network)).first()
            else:
                resultsbuf = session.query(User).filter_by(name=resultsbuf.parent, network=self.factory.network).first()
            if (resultsbuf):
                self.users[nickname] = resultsbuf
                self.users_html()
                if resultsbuf.faction == 1:
                    self.crusaders.append(nickname)
                elif resultsbuf.faction == 2:
                    self.arbiters.append(nickname)
                print resultsbuf.level, self.rpg_checkclass(resultsbuf.cls), resultsbuf.name
                self.events.Post(events.Login(str(resultsbuf.name), str(resultsbuf.level), str(self.rpg_checkclass(resultsbuf.cls)), resultsbuf.guild))
            session.close()

    def rpg_checkclass(self, pclass):
        """ Returns name of classnumber. """
        return self.inverseclass.get(pclass, "Serf")

    def rpg_classname(self, pclass):
        """ Returns classnumber of name. """
        return self.classlist.get(pclass, 0)

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
        self.events.Post(events.ExpGained(name=user, amount=exp))
        if self.rpg_checklevel(self.users[user].level, exp+self.users[user].exp) == 1:
            self.users[user].level += 1
            print "%s is now level: %s" % (user, self.users[user].level)
            if self.msg_user == 1:
                self.notice(user, "Congratulations! You gained level %s" % self.users[user].level)
            self.events.Post(events.Levelup(str(user), str(self.users[user].level)))
            self.users_html()
        session.merge(self.users[user])
        session.commit()
        session.close()

    def rpg_changeclass(self, user, nclass):
        """ Attempts to change user's class. """
        session = Session()
        try:
            if self.users[user]:
                if nclass in self.rpg_getlegitclass(user, 1):
                    self.users[user].cls = nclass
                    self.msg(user, "Congratulations, you are now a %s." % self.rpg_checkclass(nclass))
                    self.events.Post(events.Message("%s is now a %s." % (str(user), str(self.rpg_checkclass(nclass))), "output" ))
                    session.merge(self.users[user])
                    session.commit()
                    session.close()
                    self.users_html()
                else:
                    self.msg(user, "You can't change into that class.")
                    session.close()
        except KeyError:
            session.close()

    def rpg_checklevel(self, level, exp):
        """ Harcoded level tables. """
        try:
            if exp >= self.leveltable[level]:
                return 1
            else:
                return 0
        except KeyError:
            return 0

    def users_html(self):
        f = open(os.path.join(template_output, self.factory.network, "online.txt"), "w")
        ubuffer = "Users online:\n"
        for user in self.users:
            ubuffer += "%s(%s) " % (user, self.users[user].level)
        failbuffer = ubuffer
        ubuffer += "\nLast updated: %s" % (strftime("%a, %d %b %Y %H:%M:%S", localtime()))
        f.write(ubuffer)
        f.close()
        self.html_fulldump()

    def html_fulldump(self):
        session = Session()
        f = open(os.path.join(template_output, self.factory.network, "users.txt"), "w")
        ubuffer = "IRCRPG players:\n"
        classbuff = ""
        for row in session.query(User).filter_by(network=self.factory.network).order_by(User.level.desc()).all():
            if row.cls != 0:
                classbuff = self.rpg_checkclass(row.cls)+" "
            #Gold formula: int(round(n, 1 - int(math.log10(n))))
            ubuffer += "%s%s, level: %s.%s (%s)\n" % (classbuff, row.name, row.level, row.clown_level, int(float("%.1e" % row.gold)))
        f.write(ubuffer)
        f.close()
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

    @adminOnly
    def command_die(self, user, rest, isAuthenticated):
        reactor.stop()

    def command_guild(self, user, rest, isAuthenticated):
        if isAuthenticated:
            if not self.users[user].guild:
                session = Session()
                command, sep, rest = rest.partition(' ')
                if command == "create":
                    self.events.Post(events.Message(target=user, message="Not yet implemented."))
                elif command == "invite":
                    self.events.Post(events.Message(target=user, message="Not yet implemented."))
                elif command == "join":
                    command, sep, rest = rest.partition(' ')
                    if command == '':
                        result = "Invited to join: "
                        for guild in session.query(GuildInvite).filter(func.lower(GuildInvite.target) == func.lower(user), func.lower(GuildInvite.network) == func.lower(self.factory.network)).all():
                            result += "%s (%s) by %s, " % (self.guilds[guild.guild].name, self.guilds[guild.guild].shortname, guild.inviter)
                        if len(result) > 17 :
                            self.events.Post(events.Message(target=user, message=str(result)))
                    else:
                        if not self.users[user].guild:
                            result = session.query(GuildInvite).filter(func.lower(GuildInvite.target) == func.lower(user), func.lower(GuildInvite.guild) == func.lower(command), func.lower(GuildInvite.network) == func.lower(self.factory.network)).first()
                            if result:
                                self.users[user].guild = result.guild
                                session.merge(self.users[user])
                                session.delete(result)
                                session.commit()
                                self.events.Post(events.Message(target=user, message="Joined {0}.".format(self.guilds[result.guild].name) ))
                                self.events.Post(events.Message(target="output", message="{0} has joined {1}.".format(user, self.guilds[result.guild].name)))
                            else:
                                self.events.Post(events.Message(target=user, message="Couldn't find that invite."))
                        else:
                            self.events.Post(events.Message(target=user, message="You must leave you current guild before you can join another."))
                session.close()

    def command_class(self, user, rest, isAuthenticated):
        if isAuthenticated:
            try:
                self.rpg_changeclass(user,self.classlist[rest.capitalize()])
            except KeyError:
                self.events.Post(events.Message(target=user, message=self.rpg_getlegitclass(user, 2)))

    def command_classes(self, user, rest, isAuthenticated):
        if isAuthenticated:
            self.events.Post(events.Message(target=user, message=self.rpg_getlegitclass(user, 2)))

    def command_help(self, user, rest, isAuthenticated):
        if isAuthenticated:
            self.events.Post(events.Message(target=user, message="Commands are: register, classes, guild, class"))
        else:
            self.events.Post(events.Message(target=user, message="Commands are: register"))

    def command_online(self, user, rest, isAuthenticated):
        self.events.Post(events.Message(target=user, message=str(self.users)))

    @adminOnly
    def command_insert(self, user, rest, isAuthenticated):
        session = Session()
        names = rest.split(' ')
        session.add(Names(names[0], names[1], self.factory.network))
        session.commit()
        session.close()

    @adminOnly
    def command_html(self, user, rest, isAuthenticated):
        command = rest.partition(' ')
        if command[0] == "users":
            self.users_html()
        elif command[0] == "full":
            self.html_fulldump()

    def command_register(self, user, rest, isAuthenticated):
        if self.factory.type == "ircd-seven":
            self.whois(user)
        else:
            self.rpg_register(user, rest)

    def rpg_register(self, user, rest):
        session = Session()
        if not (session.query(User).filter_by(name=user, network=self.factory.network).first()):
            self.msg(user, "Registering you.")
            session.add(User(user, self.factory.network))
            session.commit()
            for channel in self.factory.channels:
                self.sendLine("WHO %s %%na" % channel)
        else:
            self.msg(user, "Already registered.")
        session.close()

    def _logout(self, user):
        pass

    def _login(self, user):
        pass

    def Notify(self, event):
        if isinstance(event, events.Message):
            if event.target == "output":
                if self.msg_channel == 1:
                    self.msg(self.output_channel, event.message)
            else:
                self.msg(event.target, event.message)

class listitem:
    href = "#"
    caption = "link"

    def __init__(self, href, caption):
        self.href = href
        self.caption = caption


class RPGBotFactory(protocol.ReconnectingClientFactory):

    # Configuration files.
    Config = ConfigParser.ConfigParser()
    Config.read("config.ini")

    # I like having a comment here
    protocol = RPGBot

    def __init__(self, server):
        self.server = server
        self.network = Config.get(self.server, "network")
        self.type = Config.get(self.server, "type")
        self.channels = Config.get(self.server, "channels").lower().replace(' ','').split(',')
        self.nickname = Config.get(self.server, "nickname")
    
    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.callLater(30, connector.connect)


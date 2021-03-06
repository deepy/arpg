class Event:
    def __init__(self):
        self.name = "Irrelevant Event"

class Collision(Event):
    def __init__(self, collider, targets):
        self.name = "Collision Event"
        self.collider = collider
        self.targets = targets

class Login(Event):
    def __init__(self, name, level, cls, guild=None):
        self.name = name
        self.level = level
        self.cls = cls
        self.guild = guild

class Logout(Event):
    def __init__(self, name, level, cls):
        self.name = name
        self.level = level
        self.cls = cls

class Levelup(Event):
    def __init__(self, name, level):
        self.name = name
        self.level = level

class ExpGained(Event):
    def __init__(self, name, amount):
        self.name = name
        self.amount = amount

class Message(Event):
    def __init__(self, message, target):
        self.message = message
        self.target = target

class Command(Event):
    def __init__(self, user, command, parameters=None, authenticated=False):
        self.user = user
        self.command = command
        self.parameters = parameters
        self.authenticated = authenticated

class Manager:
    def __init__(self ):
        from weakref import WeakKeyDictionary
        self.listeners = WeakKeyDictionary()

    def RegisterListener( self, listener ):
        self.listeners[ listener ] = 1

    def UnregisterListener( self, listener ):
        if listener in self.listeners.keys():
            del self.listeners[ listener ]
        
    def Post( self, event ):
        for listener in self.listeners.keys():
            listener.Notify( event )

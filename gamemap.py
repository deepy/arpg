from events import *

class BE:
    def __init__(self, size):
        from weakref import WeakKeyDictionary
        self.listeners = WeakKeyDictionary()
        self.field = [ [ [] for col in range(size) ] for row in range(size) ]
        
    def display(self):
        for i in self.field:
            for j in i:
                print j,
            print ""

    def add(self, item, cord):
        if len(self.field[ cord[ 0 ] ] [ cord [ 1 ] ]) >= 1:
            self.broadcast(CollisionEvent(item,self.field[ cord[ 0 ] ] [ cord [ 1 ] ]))
        else:
            pass
        self.field[ cord[ 0 ] ][ cord[ 1 ] ].append(item)
    
    def register(self, listener):
        self.listeners [ listener ] = 1

    def unregister(self, listener):
        if listener in self.listeners.keys():
            del self.listeners[ listener ]
    
    def broadcast(self, event):
        for listener in self.listeners.keys():
            listener.Notify(event)
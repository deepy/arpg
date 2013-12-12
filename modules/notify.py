import arpg.events as events

class Handler:
    def __init__(self, manager):
        self.manager = manager
        self.manager.RegisterListener(self)

    def Notify(self, event):
        if isinstance(event, events.Login):
            self.manager.Post(events.Message("%s the level %s %s logged in." % (event.name, event.level, event.cls), "output"))
        if isinstance(event, events.Levelup):
            self.manager.Post(events.Message("%s gained level %s!" % (event.name, event.level), "output"))

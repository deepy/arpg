import arpg.events as events

class Handler:
    def __init__(self, manager):
        self.manager = manager
        self.manager.RegisterListener(self)

    def Notify(self, event):
        if isinstance(event, events.Login):
            if event.guild:
                self.manager.Post(events.Message("{0} <{1}> the level {2} {3} logged in.".format(event.name, event.guild, event.level, event.cls), "output"))
            else:
                self.manager.Post(events.Message("{0} the level {1} {2} logged in.".format(event.name, event.level, event.cls), "output"))
        if isinstance(event, events.Levelup):
            self.manager.Post(events.Message("{0} gained level {1}!".format(event.name, event.level), "output"))

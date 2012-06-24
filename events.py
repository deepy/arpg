class Event:
    def __init__(self):
        self.name = "Irrelevant Event"

class CollisionEvent(Event):
    def __init__(self, collider, targets):
        self.name = "Collision Event"
        self.collider = collider
        self.targets = targets
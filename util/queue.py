from collections import deque
from errors import errors

class MemeQueue:
    """
    Handles memes to be played next.
    """

    def __init__(self, guild_id):
        self.deck = deque([])
        self.guild_id = ""


    def addToQueue(self, fileName):
        self.deck.append(fileName)


    def currentInQueue(self):
        currentElement = self.deck[0]
        return currentElement
    
    def removeCurrent(self):
        removedElement = self.deck.popleft()
        return removedElement



queues = {}

def add_element(guild_id, fileName):
    queue = queues.get(guild_id)

    if queue:
        queues[guild_id].addToQueue(fileName)
    else:
        queue = MemeQueue(guild_id)
        queue.addToQueue(fileName)
        queues[guild_id] = queue


def get_current(guild_id):
    queue = getQueue(guild_id)
    if queue:
        return queue.currentInQueue()


def remove_current(guild_id):
    queue = getQueue(guild_id)
    if queue:
        return queue.removeCurrent()


def getQueue(guild_id):
    queue = queues.get(guild_id)
    
    if not queue:
        print("No queue for this guild")
        return

    deck = queue.deck

    if not deck:
        del queues[guild_id]
        print("Queue is empty")
        return

    return queue
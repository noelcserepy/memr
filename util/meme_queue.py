from collections import deque
from errors.errors import QueueError, EmptyError

class MemeQueue:
    """Queue for housing Meme objects to be played next."""

    def __init__(self, meme):
        self.deck = deque([])


    def addToQueue(self, meme):
        self.deck.append(meme)


    def currentInQueue(self):
        currentElement = self.deck[0]
        return currentElement
    

    def next(self):
        removedElement = self.deck.popleft()
        return removedElement



queues = {}

def add_element(meme):
    try:
        queue = queues.get(meme.guild_id)

        if queue:
            queues[meme.guild_id].addToQueue(meme)
        else:
            queue = MemeQueue(meme)
            queue.addToQueue(meme)
            queues[meme.guild_id] = queue
    except:
        raise QueueError("Failed to add element to queue.")

def get_current(meme):
    try:
        queue = getQueue(meme.guild_id)
        if queue:
            if queue.deck:
                return queue.currentInQueue()
            del queues[meme.guild_id]
            return
    except Exception as e:
        raise QueueError("Failed to get current element from queue.", e)


def next(meme):
    try:
        queue = getQueue(meme.guild_id)
        if queue:
            if queue.deck:
                return queue.next()
            del queues[meme.guild_id]
            return
    except:
        raise QueueError("Failed to remove element from queue.")


def getQueue(guild_id):
    try:
        queue = queues.get(guild_id)
        if not queue:
            raise QueueError("No queue for this guild")

        return queue
    except QueueError as e:
        raise e
    except:
        raise QueueError("Failed to get queue.")

def cleanup(meme):
    """ Removes leftover queues and queue elements if errors occur. """
    pass
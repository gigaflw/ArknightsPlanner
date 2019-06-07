import os

ROOT = os.path.dirname(os.path.realpath(__file__))

def LeaderBoard(capacity: int = 3):
    import heapq
    class _lb(list): pass
    leaderboard = _lb()

    def add(self, item):
        heapq.heappush(self, item)

        if len(self) > self.capacity > 0:
            heapq.heappop(self)

    def top(self, n = 1):
        return max(self)

    leaderboard.capacity = capacity
    leaderboard.add = add.__get__(leaderboard)
    leaderboard.top = top.__get__(leaderboard)

    return leaderboard

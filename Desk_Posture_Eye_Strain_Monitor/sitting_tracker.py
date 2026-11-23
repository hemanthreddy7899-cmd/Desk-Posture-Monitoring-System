
import time

class SittingTracker:

    def __init__(self):
        self.start_time = time.time()
        self.total_paused = 0
        self.pause_start = None

    def pause(self):
        if self.pause_start is None:
            self.pause_start = time.time()

    def resume(self):
        if self.pause_start is not None:
            self.total_paused += time.time() - self.pause_start
            self.pause_start = None

    def get_sitting_time(self):
        current_time = self.pause_start or time.time()

        elapsed = current_time - self.start_time - self.total_paused

        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

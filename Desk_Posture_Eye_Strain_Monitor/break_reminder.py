
import time

class BreakReminder:

    def __init__(self):
        self.start_time = time.time()
        self.break_interval = 20 * 60
        self.break_duration = 20
        self.break_start = None

    def get_status(self):
        current_time = time.time()

        if self.break_start is not None:
            elapsed_break = current_time - self.break_start

            if elapsed_break < self.break_duration:
                remaining = int(self.break_duration - elapsed_break)
                return f"Break time! Look away: {remaining}s"

            self.break_start = None
            self.start_time = current_time

        elapsed = current_time - self.start_time
        remaining = int(self.break_interval - elapsed)

        if remaining <= 0:
            self.break_start = current_time
            return "Break time! Look away for 20 seconds"

        minutes = remaining // 60
        seconds = remaining % 60

        return f"Next break in: {minutes:02d}:{seconds:02d}"

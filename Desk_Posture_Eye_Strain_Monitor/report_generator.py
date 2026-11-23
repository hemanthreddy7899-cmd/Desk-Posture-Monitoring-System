
import csv
import os
from datetime import datetime


def save_report(sitting_time, blink_count, breaks_completed):

    filename = "monitoring_report.csv"

    file_exists = os.path.isfile(filename)

    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M:%S")

    with open(filename, "a", newline="") as file:

        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "Date",
                "Time",
                "Sitting Time",
                "Blink Count",
                "Breaks Completed"
            ])

        writer.writerow([
            current_date,
            current_time,
            sitting_time,
            blink_count,
            breaks_completed
        ])

    return filename

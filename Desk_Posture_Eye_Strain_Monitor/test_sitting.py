
import cv2
from sitting_tracker import SittingTracker

camera = cv2.VideoCapture(0)
tracker = SittingTracker()

if not camera.isOpened():
    print("Cannot open webcam")
    raise SystemExit

while True:
    success, frame = camera.read()

    if not success:
        break

    sitting_time = tracker.get_sitting_time()

    cv2.putText(
        frame,
        "Sitting Time: " + sitting_time,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 255),
        2
    )

    cv2.imshow("Sitting Time Tracker", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()


import cv2
from break_reminder import BreakReminder

camera = cv2.VideoCapture(0)
reminder = BreakReminder()

if not camera.isOpened():
    print("Cannot open webcam")
    raise SystemExit

while True:
    success, frame = camera.read()

    if not success:
        break

    status = reminder.get_status()

    cv2.putText(
        frame,
        status,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2
    )

    cv2.imshow("Eye Break Reminder", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()

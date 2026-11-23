
import cv2
from eye_detection import detect_eye_status

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Cannot open webcam")
    raise SystemExit

while True:
    success, frame = camera.read()

    if not success:
        break

    frame, status = detect_eye_status(frame)

    cv2.imshow("Eye Detection Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()

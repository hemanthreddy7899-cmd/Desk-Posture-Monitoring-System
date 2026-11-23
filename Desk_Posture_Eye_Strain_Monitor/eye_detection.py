
import cv2
import mediapipe as mp
import math

mp_face_mesh = mp.solutions.face_mesh

LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

BLINK_THRESHOLD = 0.20

blink_count = 0
eyes_closed = False


def distance(p1, p2):
    return math.dist(p1, p2)


def eye_ratio(landmarks, eye_points, width, height):
    points = []

    for index in eye_points:
        landmark = landmarks[index]
        points.append((
            int(landmark.x * width),
            int(landmark.y * height)
        ))

    vertical1 = distance(points[1], points[5])
    vertical2 = distance(points[2], points[4])
    horizontal = distance(points[0], points[3])

    if horizontal == 0:
        return 0

    return (vertical1 + vertical2) / (2 * horizontal)


def detect_eye_status(frame):
    global blink_count, eyes_closed

    height, width = frame.shape[:2]

    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as face_mesh:

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        status = "Face not detected"

        if results.multi_face_landmarks:
            face = results.multi_face_landmarks[0]

            left = eye_ratio(face.landmark, LEFT_EYE, width, height)
            right = eye_ratio(face.landmark, RIGHT_EYE, width, height)

            average = (left + right) / 2

            if average < BLINK_THRESHOLD:
                status = "Eyes Closed"

                if not eyes_closed:
                    eyes_closed = True

            else:
                status = "Eyes Open"

                if eyes_closed:
                    blink_count += 1
                    eyes_closed = False

        cv2.putText(
            frame,
            status,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Blink Count: {blink_count}",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 0),
            2
        )

    return frame, status

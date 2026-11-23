import tkinter as tk
from tkinter import messagebox, ttk
import cv2
import mediapipe as mp
import math
import time
import csv
import os
from datetime import datetime
from PIL import Image, ImageTk
import sqlite3
import hashlib
import secrets

try:
    import winsound  # Built into Windows; used for posture warning beeps.
except ImportError:
    winsound = None

import tkinter as tk
from tkinter import messagebox, ttk
import cv2
import mediapipe as mp
import math
import time
import csv
import os
from datetime import datetime
from PIL import Image, ImageTk


# =========================================================
# APPLICATION SETTINGS
# =========================================================

root = tk.Tk()
root.withdraw()  # Show the dashboard only after successful login.
root.title("Desk Posture and Eye Strain Monitoring System")
root.geometry("1280x920")
root.minsize(1100, 820)
root.configure(bg="#0b1220")

# Consistent dark styling for native tables and scrollable controls.
style = ttk.Style(root)
try:
    style.theme_use("clam")
except tk.TclError:
    pass
style.configure("Treeview", background="#151f2e", foreground="#e5edf8",
                fieldbackground="#151f2e", rowheight=34, borderwidth=0,
                font=("Segoe UI", 10))
style.configure("Treeview.Heading", background="#26364d", foreground="#f1f5f9",
                font=("Segoe UI", 10, "bold"), relief="flat")
style.map("Treeview", background=[("selected", "#155e75")],
          foreground=[("selected", "#ffffff")])


camera = None
running = False

# Fast posture warning: repeat the alert frequently while poor posture continues.
last_posture_alert_time = 0.0
posture_alert_cooldown = 0.45

# Eye blink tracking
blink_count = 0
eyes_closed = False

# Sitting and monitoring time
sitting_start = None
total_sitting = 0.0

session_start = None
total_monitoring = 0.0

# Break reminder
break_interval = 20 * 60       # 20 minutes
break_duration = 20            # 20 seconds
break_cycle_start = None
break_start = None
breaks_completed = 0


# =========================================================
# FACE DETECTION
# =========================================================

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)

if face_cascade.empty():
    messagebox.showerror(
        "Face Detection Error",
        "OpenCV could not load the face detection file."
    )


# =========================================================
# MEDIAPIPE POSTURE DETECTION
# =========================================================

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


# =========================================================
# MEDIAPIPE EYE DETECTION
# =========================================================

mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
BLINK_THRESHOLD = 0.20


def calculate_distance(point1, point2):
    return math.dist(point1, point2)


def calculate_eye_ratio(landmarks, eye_points, width, height):
    points = []

    for index in eye_points:
        landmark = landmarks[index]
        points.append((
            int(landmark.x * width),
            int(landmark.y * height)
        ))

    vertical1 = calculate_distance(points[1], points[5])
    vertical2 = calculate_distance(points[2], points[4])
    horizontal = calculate_distance(points[0], points[3])

    if horizontal == 0:
        return 0

    return (vertical1 + vertical2) / (2.0 * horizontal)


def format_time(seconds):
    seconds = max(0, int(seconds))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# =========================================================
# DASHBOARD HEADING
# =========================================================

tk.Label(
    root,
    text="DESK POSTURE AND EYE STRAIN MONITORING SYSTEM",
    font=("Segoe UI", 22, "bold"),
    bg="#0b1220",
    fg="#e5edf8"
).pack(pady=14)

tk.Label(
    root,
    text="LIVE HEALTH MONITORING DASHBOARD",
    font=("Segoe UI", 11, "bold"),
    bg="#0b1220",
    fg="#91a4bd"
).pack(pady=(0, 8))


# =========================================================
# MAIN PANEL AND CAMERA DISPLAY
# =========================================================

panel = tk.Frame(root, bg="#151f2e", padx=20, pady=16, highlightthickness=1, highlightbackground="#26364d")
panel.pack(fill="both", expand=True, padx=22, pady=8)

camera_frame = tk.Frame(
    panel,
    width=760,
    height=430,
    bg="#05080e"
)
camera_frame.pack(pady=8)
camera_frame.pack_propagate(False)

video_label = tk.Label(
    camera_frame,
    text="CAMERA NOT STARTED",
    font=("Segoe UI", 18, "bold"),
    bg="#05080e",
    fg="#e5edf8"
)
video_label.pack(fill="both", expand=True)


# =========================================================
# STATUS CARDS
# =========================================================

status_frame = tk.Frame(panel, bg="#151f2e")
status_frame.pack(pady=8)


def create_status(parent, title, color):
    card = tk.Frame(
        parent,
        bg="#202d40",
        width=300,
        height=66,
        padx=10,
        pady=8,
        highlightthickness=1, highlightbackground="#34445b"
    )
    card.pack_propagate(False)
    card.pack(side="left", padx=5)

    label = tk.Label(
        card,
        text=title,
        font=("Segoe UI", 10, "bold"),
        bg="#202d40",
        fg=color,
        wraplength=280
    )
    label.pack(expand=True)

    return label


face_label = create_status(status_frame, "Face: Not Started", "red")
posture_label = create_status(status_frame, "Posture: Not Started", "#e5edf8")
eye_label = create_status(status_frame, "Eye Status: Not Started", "#e5edf8")


# =========================================================
# STATISTICS CARDS
# =========================================================

stats_frame = tk.Frame(panel, bg="#151f2e")
stats_frame.pack(pady=8)


def create_stat(parent, title):
    card = tk.Frame(
        parent,
        bg="#202d40",
        width=215,
        height=82,
        padx=10,
        pady=8,
        highlightthickness=1, highlightbackground="#34445b"
    )
    card.pack_propagate(False)
    card.pack(side="left", padx=5)

    tk.Label(
        card,
        text=title,
        font=("Segoe UI", 9, "bold"),
        bg="#202d40",
        fg="#e5edf8"
    ).pack()

    value = tk.Label(
        card,
        text="00:00:00" if "TIME" in title else "0",
        font=("Segoe UI", 14, "bold"),
        bg="#202d40",
        fg="#198754"
    )
    value.pack()

    return value


blink_value = create_stat(stats_frame, "BLINK COUNT")
sitting_value = create_stat(stats_frame, "SITTING TIME")
monitoring_value = create_stat(stats_frame, "MONITORING TIME")
break_value = create_stat(stats_frame, "BREAK STATUS")


break_label = tk.Label(
    panel,
    text="Break Status: Waiting for monitoring",
    font=("Segoe UI", 11, "bold"),
    bg="#151f2e",
    fg="#e5edf8"
)
break_label.pack(pady=7)


# =========================================================
# CAMERA UPDATE
# =========================================================

def update_camera():
    global camera, running
    global blink_count, eyes_closed
    global break_start, break_cycle_start, breaks_completed
    global last_posture_alert_time

    posture_warning = False

    if not running or camera is None:
        return

    success, frame = camera.read()

    if not success:
        root.after(30, update_camera)
        return

    frame = cv2.flip(frame, 1)
    height, width = frame.shape[:2]

    # ---------------- FACE DETECTION ----------------

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(40, 40)
    )

    for (x, y, w, h) in faces:
        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )
        cv2.putText(
            frame,
            "Face",
            (x, max(20, y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

    if len(faces) > 0:
        face_label.config(
            text=f"Face: Detected ({len(faces)})",
            fg="green"
        )
    else:
        face_label.config(text="Face: Not Detected", fg="red")

    # ---------------- POSTURE DETECTION ----------------

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pose_results = pose.process(rgb_frame)

    if pose_results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame,
            pose_results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )

        landmarks = pose_results.pose_landmarks.landmark

        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
        left_ear = landmarks[mp_pose.PoseLandmark.LEFT_EAR.value]
        right_ear = landmarks[mp_pose.PoseLandmark.RIGHT_EAR.value]

        shoulders_visible = (
            left_shoulder.visibility > 0.55 and
            right_shoulder.visibility > 0.55
        )
        hips_visible = (
            left_hip.visibility > 0.55 and
            right_hip.visibility > 0.55
        )

        if not shoulders_visible:
            posture_label.config(
                text="Posture: Face camera and show both shoulders",
                fg="orange"
            )
            cv2.putText(
                frame, "SHOW BOTH SHOULDERS",
                (15, 35), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (0, 165, 255), 2
            )
        else:
            shoulder_width = abs(right_shoulder.x - left_shoulder.x)

            # A narrow shoulder width often indicates a side-on camera view.
            # This is an estimate; camera angle and body shape affect it.
            if shoulder_width < 0.18:
                side_candidates = [
                    (left_ear, left_shoulder, left_hip),
                    (right_ear, right_shoulder, right_hip)
                ]
                visible_side = max(
                    side_candidates,
                    key=lambda points: min(
                        points[0].visibility,
                        points[1].visibility,
                        points[2].visibility
                    )
                )
                ear, shoulder, hip = visible_side

                if min(
                    ear.visibility,
                    shoulder.visibility,
                    hip.visibility
                ) < 0.50:
                    posture_label.config(
                        text="Posture: Side view - show ear, shoulder and hip",
                        fg="orange"
                    )
                    cv2.putText(
                        frame, "SIDE VIEW: SHOW EAR, SHOULDER AND HIP",
                        (15, 35), cv2.FONT_HERSHEY_SIMPLEX,
                        0.48, (0, 165, 255), 2
                    )
                else:
                    torso_height = abs(hip.y - shoulder.y)

                    if torso_height < 0.08:
                        posture_label.config(
                            text="Posture: Move back so upper body is visible",
                            fg="orange"
                        )
                    else:
                        # Approximate side-view indicators, normalized by
                        # torso height to reduce sensitivity to camera distance.
                        forward_head_ratio = (
                            abs(ear.x - shoulder.x) / torso_height
                        )
                        torso_lean_ratio = (
                            abs(shoulder.x - hip.x) / torso_height
                        )

                        if (forward_head_ratio > 0.38 or
                                torso_lean_ratio > 0.22):
                            posture_warning = True
                            posture_label.config(
                                text="Posture: Possible Forward Slouch - Sit Upright",
                                fg="red"
                            )
                            cv2.putText(
                                frame, "POSSIBLE FORWARD SLOUCH - SIT UPRIGHT",
                                (15, 35), cv2.FONT_HERSHEY_SIMPLEX,
                                0.48, (0, 0, 255), 2
                            )
                        else:
                            posture_label.config(
                                text="Posture: Side View Alignment Looks Good",
                                fg="green"
                            )
                            cv2.putText(
                                frame, "SIDE VIEW ALIGNMENT OK",
                                (15, 35), cv2.FONT_HERSHEY_SIMPLEX,
                                0.6, (0, 255, 0), 2
                            )
            else:
                # Front-view check: shoulder tilt and shoulder/hip centre shift.
                if shoulder_width < 0.04:
                    posture_label.config(
                        text="Posture: Move a little farther from camera",
                        fg="orange"
                    )
                else:
                    shoulder_tilt = abs(
                        right_shoulder.y - left_shoulder.y
                    ) / shoulder_width

                    torso_shift = None
                    if hips_visible:
                        shoulder_center_x = (
                            left_shoulder.x + right_shoulder.x
                        ) / 2
                        hip_center_x = (
                            left_hip.x + right_hip.x
                        ) / 2
                        torso_shift = abs(
                            shoulder_center_x - hip_center_x
                        )

                    # Front-view forward-lean detection using MediaPipe's
                    # relative depth (z) landmarks. When the upper body moves
                    # toward the camera, the shoulders become closer than the
                    # hips, so shoulder_z - hip_z becomes more negative.
                    forward_lean = False
                    if hips_visible:
                        shoulder_z = (
                            left_shoulder.z + right_shoulder.z
                        ) / 2.0
                        hip_z = (left_hip.z + right_hip.z) / 2.0

                        torso_height_px = abs(
                            ((left_hip.y + right_hip.y) / 2.0 -
                             (left_shoulder.y + right_shoulder.y) / 2.0)
                            * height
                        )

                        if torso_height_px > 1:
                            forward_depth_ratio = (
                                (shoulder_z - hip_z) * width
                            ) / torso_height_px

                            # Negative values indicate the shoulders are
                            # closer to the camera than the hips.
                            forward_lean = forward_depth_ratio < -0.18

                    bad_posture = (
                        shoulder_tilt > 0.20 or
                        (torso_shift is not None and torso_shift > 0.18)
                    )

                    if forward_lean:
                        posture_warning = True
                        posture_label.config(
                            text="Posture: FORWARD LEAN DETECTED - SIT UPRIGHT",
                            fg="red"
                        )
                        cv2.putText(
                            frame, "FORWARD LEAN DETECTED - SIT UPRIGHT!",
                            (15, 35), cv2.FONT_HERSHEY_SIMPLEX,
                            0.58, (0, 0, 255), 2
                        )
                    elif bad_posture:
                        posture_warning = True
                        posture_label.config(
                            text="Posture: Possible Side Lean - Sit Straight",
                            fg="red"
                        )
                        cv2.putText(
                            frame, "POSSIBLE SIDE LEAN - SIT STRAIGHT",
                            (15, 35), cv2.FONT_HERSHEY_SIMPLEX,
                            0.55, (0, 0, 255), 2
                        )
                    elif hips_visible:
                        posture_label.config(
                            text="Posture: Front Alignment Looks Good",
                            fg="green"
                        )
                        cv2.putText(
                            frame, "FRONT ALIGNMENT OK",
                            (15, 35), cv2.FONT_HERSHEY_SIMPLEX,
                            0.65, (0, 255, 0), 2
                        )
                    else:
                        posture_label.config(
                            text="Posture: Shoulders Aligned - Show Waist for Full Check",
                            fg="green"
                        )
                        cv2.putText(
                            frame, "SHOULDERS ALIGNED - SHOW WAIST FOR FULL CHECK",
                            (15, 35), cv2.FONT_HERSHEY_SIMPLEX,
                            0.48, (0, 255, 0), 2
                        )
    else:
        posture_label.config(
            text="Posture: Body Not Detected - Adjust Camera",
            fg="red"
        )

    # ---------------- POSTURE SOUND ALERT ----------------

    current_time = time.time()
    if posture_warning and (
        current_time - last_posture_alert_time >= posture_alert_cooldown
    ):
        try:
            if winsound is not None:
                winsound.Beep(1500, 120)  # Higher-pitched, short, fast warning beep
            else:
                root.bell()
        except Exception:
            # Sound is an optional alert; monitoring should continue if audio fails.
            pass

        last_posture_alert_time = current_time

    # ---------------- EYE DETECTION ----------------

    eye_results = face_mesh.process(rgb_frame)

    if eye_results.multi_face_landmarks:
        face = eye_results.multi_face_landmarks[0]

        left_ratio = calculate_eye_ratio(
            face.landmark, LEFT_EYE, width, height
        )
        right_ratio = calculate_eye_ratio(
            face.landmark, RIGHT_EYE, width, height
        )

        average_ratio = (left_ratio + right_ratio) / 2

        if average_ratio < BLINK_THRESHOLD:
            eye_status = "Eyes Closed"

            if not eyes_closed:
                eyes_closed = True
        else:
            eye_status = "Eyes Open"

            if eyes_closed:
                blink_count += 1
                eyes_closed = False

        eye_label.config(
            text=f"Eye Status: {eye_status}",
            fg="green" if eye_status == "Eyes Open" else "red"
        )
    else:
        eye_label.config(
            text="Eye Status: Face Not Detected",
            fg="orange"
        )
        eyes_closed = False

    # ---------------- TIME STATISTICS ----------------

    now = time.time()

    current_sitting = total_sitting
    if sitting_start is not None:
        current_sitting += now - sitting_start

    current_monitoring = total_monitoring
    if session_start is not None:
        current_monitoring += now - session_start

    sitting_value.config(text=format_time(current_sitting))
    monitoring_value.config(text=format_time(current_monitoring))
    blink_value.config(text=str(blink_count))

    # ---------------- BREAK REMINDER ----------------

    if break_start is not None:
        break_remaining = int(
            break_duration - (now - break_start)
        )

        if break_remaining > 0:
            break_status = f"Look Away: {break_remaining}s"
            break_label.config(
                text="Break Reminder: Look away from the screen",
                fg="orange"
            )
        else:
            # Count this completed break only once.
            breaks_completed += 1
            break_start = None
            break_cycle_start = now
            break_status = "Completed"
            break_label.config(
                text="Break completed. Monitoring resumed.",
                fg="green"
            )

    else:
        elapsed_since_break = now - break_cycle_start
        remaining = int(break_interval - elapsed_since_break)

        if remaining <= 0:
            break_start = now
            break_status = "Take Break"
            break_label.config(
                text="Time for a 20-second eye break!",
                fg="red"
            )
        else:
            minutes = remaining // 60
            seconds = remaining % 60
            break_status = f"{minutes:02d}:{seconds:02d}"
            break_label.config(
                text=f"Next eye break in: {minutes:02d}:{seconds:02d}",
                fg="#e5edf8"
            )

    break_value.config(text=break_status)

    # ---------------- DISPLAY CAMERA ----------------

    display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(display_frame)
    image = image.resize((640, 360))

    photo = ImageTk.PhotoImage(image)
    video_label.config(image=photo, text="")
    video_label.image = photo

    root.after(30, update_camera)


# =========================================================
# START MONITORING
# =========================================================

def start_monitoring():
    global camera, running
    global sitting_start, session_start
    global break_cycle_start, break_start, eyes_closed

    if running:
        return

    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not camera.isOpened():
        camera.release()
        camera = None
        messagebox.showerror(
            "Camera Error",
            "Unable to access webcam. Close other camera applications and try again."
        )
        return

    running = True
    now = time.time()

    sitting_start = now
    session_start = now
    break_cycle_start = now
    break_start = None
    eyes_closed = False

    face_label.config(text="Face: Searching...", fg="blue")
    posture_label.config(text="Posture: Checking...", fg="blue")
    eye_label.config(text="Eye Status: Checking...", fg="blue")

    update_camera()


# =========================================================
# STOP MONITORING
# =========================================================

def stop_monitoring():
    global camera, running
    global sitting_start, total_sitting
    global session_start, total_monitoring
    global break_start, break_cycle_start

    now = time.time()

    if sitting_start is not None:
        total_sitting += now - sitting_start
        sitting_start = None

    if session_start is not None:
        total_monitoring += now - session_start
        session_start = None

    running = False
    break_start = None
    break_cycle_start = None

    if camera is not None:
        camera.release()
        camera = None

    video_label.config(image="", text="CAMERA STOPPED")
    video_label.image = None

    face_label.config(text="Face: Stopped", fg="red")
    posture_label.config(text="Posture: Stopped", fg="red")
    eye_label.config(text="Eye Status: Stopped", fg="red")
    break_label.config(text="Break Status: Monitoring Stopped", fg="red")

    sitting_value.config(text=format_time(total_sitting))
    monitoring_value.config(text=format_time(total_monitoring))


# =========================================================
# GENERATE AND SAVE CSV REPORT
# =========================================================

def generate_report():
    now = time.time()

    current_sitting = total_sitting
    if sitting_start is not None:
        current_sitting += now - sitting_start

    current_monitoring = total_monitoring
    if session_start is not None:
        current_monitoring += now - session_start

    report_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "monitoring_report.csv"
    )

    file_exists = os.path.isfile(report_file)

    try:
        with open(report_file, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            if not file_exists or os.path.getsize(report_file) == 0:
                writer.writerow([
                    "Date",
                    "Time",
                    "Total Monitoring Time",
                    "Total Sitting Time",
                    "Blink Count",
                    "Breaks Completed"
                ])

            writer.writerow([
                datetime.now().strftime("%Y-%m-%d"),
                datetime.now().strftime("%H:%M:%S"),
                format_time(current_monitoring),
                format_time(current_sitting),
                blink_count,
                breaks_completed
            ])

        messagebox.showinfo(
            "Report Saved",
            "Monitoring report saved successfully!\n\n"
            f"File: {report_file}"
        )

    except OSError as error:
        messagebox.showerror(
            "Report Error",
            f"Could not save the report:\n{error}"
        )




# =========================================================
# MONITORING HISTORY AND GRAPHICAL DASHBOARD
# =========================================================

def seconds_from_time(value):
    """Convert HH:MM:SS text from the CSV into seconds."""
    try:
        hours, minutes, seconds = value.strip().split(":")
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    except (ValueError, AttributeError):
        return 0


def draw_history_chart(canvas, title, dates, values, value_label):
    """Draw a simple bar chart using Tkinter Canvas (no extra package needed)."""
    canvas.delete("all")
    canvas.update_idletasks()

    width = max(canvas.winfo_width(), 420)
    height = max(canvas.winfo_height(), 250)

    left, right, top, bottom = 48, width - 18, 48, height - 42
    chart_width = right - left
    chart_height = bottom - top

    canvas.create_text(
        width / 2, 20, text=title,
        font=("Segoe UI", 12, "bold"), fill="#e5edf8"
    )

    if not values or max(values) <= 0:
        canvas.create_text(
            width / 2, height / 2,
            text="No report data yet",
            font=("Segoe UI", 11), fill="#64748b"
        )
        return

    maximum = max(values)
    scale_max = maximum * 1.2
    canvas.create_line(left, top, left, bottom, fill="#94a3b8")
    canvas.create_line(left, bottom, right, bottom, fill="#94a3b8")

    for step in range(5):
        value = scale_max * step / 4
        y = bottom - (value / scale_max) * chart_height
        canvas.create_line(left, y, right, y, fill="#e2e8f0")
        canvas.create_text(
            left - 8, y, text=f"{value:.0f}",
            anchor="e", font=("Segoe UI", 8), fill="#64748b"
        )

    slot = chart_width / max(len(values), 1)
    bar_width = min(42, slot * 0.62)

    for index, value in enumerate(values):
        x_center = left + slot * (index + 0.5)
        bar_height = (value / scale_max) * chart_height
        x1 = x_center - bar_width / 2
        x2 = x_center + bar_width / 2
        y1 = bottom - bar_height

        canvas.create_rectangle(
            x1, y1, x2, bottom,
            fill="#3b82f6", outline=""
        )
        canvas.create_text(
            x_center, y1 - 10,
            text=f"{value:.1f}" if value < 10 else f"{value:.0f}",
            font=("Segoe UI", 8, "bold"), fill="#334155"
        )
        date_text = dates[index]
        if len(date_text) > 5:
            date_text = date_text[5:]
        canvas.create_text(
            x_center, bottom + 16,
            text=date_text, font=("Segoe UI", 8), fill="#475569"
        )

    canvas.create_text(
        right, height - 8, text=value_label,
        anchor="e", font=("Segoe UI", 8), fill="#64748b"
    )


def open_history_dashboard():
    report_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "monitoring_report.csv"
    )

    if not os.path.isfile(report_file):
        messagebox.showinfo(
            "No History Found",
            "No monitoring report has been created yet.\n"
            "Run monitoring and click GENERATE REPORT first."
        )
        return

    daily = {}

    try:
        with open(report_file, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            required = {
                "Date", "Total Monitoring Time", "Total Sitting Time",
                "Blink Count", "Breaks Completed"
            }

            if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
                messagebox.showerror(
                    "Report Format Error",
                    "The CSV report does not contain the expected columns."
                )
                return

            for row in reader:
                date_text = row.get("Date", "").strip()
                if not date_text:
                    continue

                if date_text not in daily:
                    daily[date_text] = {
                        "monitoring": 0,
                        "sitting": 0,
                        "blinks": 0,
                        "breaks": 0,
                        "sessions": 0
                    }

                item = daily[date_text]
                item["monitoring"] += seconds_from_time(
                    row.get("Total Monitoring Time", "00:00:00")
                )
                item["sitting"] += seconds_from_time(
                    row.get("Total Sitting Time", "00:00:00")
                )

                try:
                    item["blinks"] += int(row.get("Blink Count", 0))
                    item["breaks"] += int(row.get("Breaks Completed", 0))
                except (ValueError, TypeError):
                    pass

                item["sessions"] += 1

    except (OSError, csv.Error) as error:
        messagebox.showerror(
            "History Error", f"Could not read the report:\n{error}"
        )
        return

    if not daily:
        messagebox.showinfo("No History Found", "The CSV report is empty.")
        return

    sorted_dates = sorted(daily.keys())[-7:]

    history_window = tk.Toplevel(root)
    history_window.title("Monitoring History and Graphical Dashboard")
    history_window.geometry("1050x720")
    history_window.configure(bg="#0b1220")

    tk.Label(
        history_window,
        text="MONITORING HISTORY",
        font=("Segoe UI", 18, "bold"),
        bg="#0b1220", fg="#e5edf8"
    ).pack(pady=(14, 4))

    tk.Label(
        history_window,
        text="Daily totals from the saved CSV reports (latest 7 dates)",
        font=("Segoe UI", 10),
        bg="#0b1220", fg="#91a4bd"
    ).pack(pady=(0, 10))

    table_frame = tk.Frame(history_window, bg="#151f2e", padx=10, pady=10)
    table_frame.pack(fill="x", padx=18, pady=6)

    columns = (
        "date", "monitoring", "sitting",
        "blinks", "breaks", "reports"
    )
    table = ttk.Treeview(
        table_frame, columns=columns, show="headings", height=7
    )

    headings = {
        "date": "Date",
        "monitoring": "Monitoring Time",
        "sitting": "Sitting Time",
        "blinks": "Blink Count",
        "breaks": "Breaks Completed",
        "reports": "Reports Saved"
    }

    widths = {
        "date": 130, "monitoring": 150, "sitting": 150,
        "blinks": 120, "breaks": 140, "reports": 120
    }

    for column in columns:
        table.heading(column, text=headings[column])
        table.column(column, width=widths[column], anchor="center")

    for date_text in reversed(sorted_dates):
        item = daily[date_text]
        table.insert(
            "",
            "end",
            values=(
                date_text,
                format_time(item["monitoring"]),
                format_time(item["sitting"]),
                item["blinks"],
                item["breaks"],
                item["sessions"]
            )
        )

    table.pack(fill="x")

    charts_frame = tk.Frame(history_window, bg="#0b1220")
    charts_frame.pack(fill="both", expand=True, padx=18, pady=10)

    chart_left = tk.Canvas(
        charts_frame, bg="#151f2e", height=280,
        highlightthickness=1, highlightbackground="#34445b"
    )
    chart_left.pack(side="left", fill="both", expand=True, padx=(0, 6))

    chart_right = tk.Canvas(
        charts_frame, bg="#151f2e", height=280,
        highlightthickness=1, highlightbackground="#34445b"
    )
    chart_right.pack(side="left", fill="both", expand=True, padx=(6, 0))

    date_labels = sorted_dates
    monitoring_hours = [
        daily[day]["monitoring"] / 3600 for day in date_labels
    ]
    sitting_hours = [
        daily[day]["sitting"] / 3600 for day in date_labels
    ]

    draw_history_chart(
        chart_left, "Daily Monitoring Time (hours)",
        date_labels, monitoring_hours, "Hours"
    )
    draw_history_chart(
        chart_right, "Daily Sitting Time (hours)",
        date_labels, sitting_hours, "Hours"
    )

    tk.Label(
        history_window,
        text="Blink counts and completed breaks are shown in the table above.",
        font=("Segoe UI", 9),
        bg="#0b1220", fg="#91a4bd"
    ).pack(pady=(0, 12))



# =========================================================
# RESET STATISTICS
# =========================================================

def reset_statistics():
    global blink_count, eyes_closed
    global total_sitting, sitting_start
    global total_monitoring, session_start
    global break_cycle_start, break_start, breaks_completed

    if running:
        messagebox.showinfo(
            "Reset Statistics",
            "Please stop monitoring before resetting statistics."
        )
        return

    blink_count = 0
    eyes_closed = False
    total_sitting = 0.0
    sitting_start = None
    total_monitoring = 0.0
    session_start = None
    break_cycle_start = None
    break_start = None
    breaks_completed = 0

    blink_value.config(text="0")
    sitting_value.config(text="00:00:00")
    monitoring_value.config(text="00:00:00")
    break_value.config(text="0")

    break_label.config(
        text="Break Status: Ready",
        fg="#e5edf8"
    )


# =========================================================
# BUTTONS
# =========================================================

button_frame = tk.Frame(panel, bg="#151f2e")
button_frame.pack(pady=(10, 14), before=camera_frame)

tk.Button(
    button_frame,
    text="START MONITORING",
    command=start_monitoring,
    bg="#198754",
    fg="white",
    font=("Segoe UI", 10, "bold"),
    width=16,
    height=2,
    relief="flat", activeforeground="white", cursor="hand2", bd=0
).pack(side="left", padx=5)

tk.Button(
    button_frame,
    text="STOP MONITORING",
    command=stop_monitoring,
    bg="#dc3545",
    fg="white",
    font=("Segoe UI", 10, "bold"),
    width=16,
    height=2,
    relief="flat", activeforeground="white", cursor="hand2", bd=0
).pack(side="left", padx=5)

tk.Button(
    button_frame,
    text="GENERATE REPORT",
    command=generate_report,
    bg="#6f42c1",
    fg="white",
    font=("Segoe UI", 10, "bold"),
    width=16,
    height=2,
    relief="flat", activeforeground="white", cursor="hand2", bd=0
).pack(side="left", padx=5)

tk.Button(
    button_frame,
    text="VIEW HISTORY",
    command=open_history_dashboard,
    bg="#0f766e",
    fg="white",
    font=("Segoe UI", 10, "bold"),
    width=16,
    height=2,
    relief="flat", activeforeground="white", cursor="hand2", bd=0
).pack(side="left", padx=5)

tk.Button(
    button_frame,
    text="RESET STATISTICS",
    command=reset_statistics,
    bg="#0d6efd",
    fg="white",
    font=("Segoe UI", 10, "bold"),
    width=16,
    height=2,
    relief="flat", activeforeground="white", cursor="hand2", bd=0
).pack(side="left", padx=5)


tk.Label(
    panel,
    text=(
        "Keep your face and upper body visible to the webcam. "
        "The posture and eye indicators are approximate."
    ),
    font=("Segoe UI", 9),
    bg="#151f2e",
    fg="#91a4bd",
    wraplength=900
).pack(pady=5)


# =========================================================
# CLOSE APPLICATION
# =========================================================

def close_application():
    stop_monitoring()
    pose.close()
    face_mesh.close()
    root.destroy()


# =========================================================
# LOGIN AND REGISTRATION (SQLite)
# =========================================================

AUTH_DB = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "users.db"
)


def initialize_auth_database():
    """Create the user table if it does not already exist."""
    with sqlite3.connect(AUTH_DB) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def hash_password(password, salt):
    """Hash a password using PBKDF2-HMAC-SHA256."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        200000
    ).hex()


def open_registration_window(login_window, username_entry_login, password_entry_login):
    register_window = tk.Toplevel(login_window)
    register_window.title("Create Account")
    register_window.geometry("420x390")
    register_window.resizable(False, False)
    register_window.configure(bg="#0b1220")
    register_window.transient(login_window)
    register_window.grab_set()

    tk.Label(
        register_window,
        text="CREATE ACCOUNT",
        font=("Segoe UI", 18, "bold"),
        bg="#0b1220",
        fg="#e5edf8"
    ).pack(pady=(25, 18))

    form = tk.Frame(register_window, bg="#151f2e", padx=28, pady=26, highlightthickness=1, highlightbackground="#34445b")
    form.pack(fill="both", expand=True, padx=25, pady=(0, 25))

    tk.Label(form, text="Username", bg="#151f2e", fg="#cbd5e1",
             font=("Segoe UI", 10, "bold")).pack(anchor="w")
    username_entry = tk.Entry(form, font=("Segoe UI", 12), width=30, bg="#0d1726", fg="#e5edf8", insertbackground="#e5edf8", relief="flat", highlightthickness=1, highlightbackground="#34445b", highlightcolor="#38bdf8")
    username_entry.pack(fill="x", pady=(5, 14))

    tk.Label(form, text="Password", bg="#151f2e", fg="#cbd5e1",
             font=("Segoe UI", 10, "bold")).pack(anchor="w")
    password_entry = tk.Entry(form, font=("Segoe UI", 12),
                              show="*", width=30, bg="#0d1726", fg="#e5edf8", insertbackground="#e5edf8", relief="flat", highlightthickness=1, highlightbackground="#34445b", highlightcolor="#38bdf8")
    password_entry.pack(fill="x", pady=(5, 14))

    tk.Label(form, text="Confirm Password", bg="#151f2e", fg="#cbd5e1",
             font=("Segoe UI", 10, "bold")).pack(anchor="w")
    confirm_entry = tk.Entry(form, font=("Segoe UI", 12),
                             show="*", width=30, bg="#0d1726", fg="#e5edf8", insertbackground="#e5edf8", relief="flat", highlightthickness=1, highlightbackground="#34445b", highlightcolor="#38bdf8")
    confirm_entry.pack(fill="x", pady=(5, 18))

    def register_user():
        username = username_entry.get().strip()
        password = password_entry.get()
        confirm = confirm_entry.get()

        if not username or not password or not confirm:
            messagebox.showwarning(
                "Missing Details", "Please fill in all fields.",
                parent=register_window
            )
            return

        if len(username) < 3:
            messagebox.showwarning(
                "Invalid Username",
                "Username must contain at least 3 characters.",
                parent=register_window
            )
            return

        if len(password) < 6:
            messagebox.showwarning(
                "Weak Password",
                "Password must contain at least 6 characters.",
                parent=register_window
            )
            return

        if password != confirm:
            messagebox.showerror(
                "Password Mismatch",
                "The passwords do not match.",
                parent=register_window
            )
            return

        salt = secrets.token_hex(16)
        password_hash = hash_password(password, salt)

        try:
            with sqlite3.connect(AUTH_DB) as connection:
                connection.execute(
                    """INSERT INTO users
                       (username, password_hash, salt, created_at)
                       VALUES (?, ?, ?, ?)""",
                    (
                        username,
                        password_hash,
                        salt,
                        datetime.now().isoformat(timespec="seconds")
                    )
                )
            messagebox.showinfo(
                "Registration Successful",
                "Your account has been created. You can now log in.",
                parent=register_window
            )
            register_window.destroy()
            username_entry_login.delete(0, tk.END)
            username_entry_login.insert(0, username)
            password_entry_login.focus_set()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Username Exists",
                "That username is already registered. Choose another.",
                parent=register_window
            )
        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error", str(error), parent=register_window
            )

    tk.Button(
        form,
        text="REGISTER",
        command=register_user,
        bg="#198754",
        fg="white",
        activebackground="#146c43",
        font=("Segoe UI", 11, "bold"),
        relief="flat",
        cursor="hand2",
        pady=9
    ).pack(fill="x")


def show_login_window():
    initialize_auth_database()

    login_window = tk.Toplevel(root)
    login_window.title("Login - Posture and Eye Strain Monitoring")
    login_window.geometry("480x510")
    login_window.resizable(False, False)
    login_window.configure(bg="#0b1220")
    login_window.protocol(
        "WM_DELETE_WINDOW",
        lambda: (login_window.destroy(), root.destroy())
    )

    tk.Label(
        login_window,
        text="DESK POSTURE & EYE STRAIN",
        font=("Segoe UI", 17, "bold"),
        bg="#0b1220",
        fg="#e5edf8"
    ).pack(pady=(30, 5))

    tk.Label(
        login_window,
        text="MONITORING SYSTEM",
        font=("Segoe UI", 12, "bold"),
        bg="#0b1220",
        fg="#91a4bd"
    ).pack(pady=(0, 18))

    form = tk.Frame(login_window, bg="#151f2e", padx=34, pady=30, highlightthickness=1, highlightbackground="#34445b")
    form.pack(fill="both", expand=True, padx=35, pady=(0, 30))

    tk.Label(
        form, text="Welcome Back",
        font=("Segoe UI", 16, "bold"),
        bg="#151f2e", fg="#e5edf8"
    ).pack(pady=(0, 20))

    tk.Label(
        form, text="Username", font=("Segoe UI", 10, "bold"),
        bg="#151f2e", fg="#cbd5e1"
    ).pack(anchor="w")
    username_entry_login = tk.Entry(
        form, font=("Segoe UI", 12), relief="flat", bd=0, bg="#0d1726", fg="#e5edf8", insertbackground="#e5edf8", highlightthickness=1, highlightbackground="#34445b", highlightcolor="#38bdf8"
    )
    username_entry_login.pack(fill="x", ipady=7, pady=(5, 14))

    tk.Label(
        form, text="Password", font=("Segoe UI", 10, "bold"),
        bg="#151f2e", fg="#cbd5e1"
    ).pack(anchor="w")
    password_entry_login = tk.Entry(
        form, font=("Segoe UI", 12), show="*", relief="flat", bd=0, bg="#0d1726", fg="#e5edf8", insertbackground="#e5edf8", highlightthickness=1, highlightbackground="#34445b", highlightcolor="#38bdf8"
    )
    password_entry_login.pack(fill="x", ipady=7, pady=(5, 18))

    def login_user():
        username = username_entry_login.get().strip()
        password = password_entry_login.get()

        if not username or not password:
            messagebox.showwarning(
                "Missing Details",
                "Enter both username and password.",
                parent=login_window
            )
            return

        try:
            with sqlite3.connect(AUTH_DB) as connection:
                record = connection.execute(
                    """SELECT password_hash, salt
                       FROM users WHERE username = ? COLLATE NOCASE""",
                    (username,)
                ).fetchone()

            if record is None:
                messagebox.showerror(
                    "Login Failed",
                    "Username or password is incorrect.",
                    parent=login_window
                )
                return

            stored_hash, salt = record
            entered_hash = hash_password(password, salt)

            if secrets.compare_digest(entered_hash, stored_hash):
                messagebox.showinfo(
                    "Login Successful",
                    f"Welcome, {username}!",
                    parent=login_window
                )
                root.title(
                    f"Desk Posture and Eye Strain Monitoring System - {username}"
                )
                login_window.destroy()
                root.deiconify()
            else:
                messagebox.showerror(
                    "Login Failed",
                    "Username or password is incorrect.",
                    parent=login_window
                )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error", str(error), parent=login_window
            )

    tk.Button(
        form,
        text="LOGIN",
        command=login_user,
        bg="#e5edf8",
        fg="white",
        activebackground="#254b78",
        font=("Segoe UI", 11, "bold"),
        relief="flat",
        cursor="hand2",
        pady=12
    ).pack(fill="x", pady=(0, 12))

    tk.Button(
        form,
        text="CREATE NEW ACCOUNT",
        command=lambda: open_registration_window(
            login_window, username_entry_login, password_entry_login
        ),
        bg="#198754",
        fg="white",
        activebackground="#146c43",
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        cursor="hand2",
        pady=9
    ).pack(fill="x")

    tk.Label(
        form,
        text="New user? Register first, then log in.",
        font=("Segoe UI", 9),
        bg="#151f2e",
        fg="#64748b"
    ).pack(pady=(14, 0))

    username_entry_login.focus_set()


# =========================================================
# START APPLICATION
# =========================================================

root.protocol("WM_DELETE_WINDOW", close_application)
show_login_window()
root.mainloop()
import sqlite3
import hashlib
import secrets
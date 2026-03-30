import cv2
import mediapipe as mp
import time

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

bad_start_time = None
alert = False

while True:
    success, frame = cap.read()
    if not success:
        break
    
    h, w, _ = frame.shape

    # Mirror fix
    frame = cv2.flip(frame, 1)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = pose.process(rgb_frame)

    posture = "DETECTING..."
    color = (200, 200, 200)
    issues = []

    if result.pose_landmarks:
        mp_draw.draw_landmarks(frame, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        landmarks = result.pose_landmarks.landmark

        nose = landmarks[mp_pose.PoseLandmark.NOSE]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]

        h, w, _ = frame.shape

        # Convert to pixel coordinates
        nose_x, nose_y = int(nose.x * w), int(nose.y * h)
        l_sh_x, l_sh_y = int(left_shoulder.x * w), int(left_shoulder.y * h)
        r_sh_x, r_sh_y = int(right_shoulder.x * w), int(right_shoulder.y * h)

        shoulder_center_x = (l_sh_x + r_sh_x) // 2
        shoulder_center_y = (l_sh_y + r_sh_y) // 2

        # 🔥 Thresholds (tunable)
        vertical_threshold = 60
        horizontal_threshold = 50
        shoulder_balance_threshold = 40

        # 🧠 CONDITIONS

        # 1. Head too forward
        if abs(nose_x - shoulder_center_x) > horizontal_threshold:
            issues.append("Head Forward")

        # 2. Head too low
        if (shoulder_center_y - nose_y) < vertical_threshold:
            issues.append("Slouching")

        # 3. Shoulder imbalance
        if abs(l_sh_y - r_sh_y) > shoulder_balance_threshold:
            issues.append("Leaning")

        # Final decision
        if len(issues) == 0:
            posture = "GOOD POSTURE"
            color = (255, 150, 0)  # blue-ish
            bad_start_time = None
            alert = False
        else:
            posture = "BAD POSTURE"
            color = (0, 0, 255)

            if bad_start_time is None:
                bad_start_time = time.time()

            elapsed = time.time() - bad_start_time

            if elapsed > 5:
                alert = True

    # 🎨 UI IMPROVEMENTS

    # Semi-transparent overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 120), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.5, frame, 0.5, 0)

    # Main posture text
    cv2.putText(frame, posture, (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

    # Show issues if any
    for i, issue in enumerate(issues):
        cv2.putText(frame, f"- {issue}", (30, 80 + i * 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # Alert
    if alert:
        cv2.putText(frame, "ALERT: FIX YOUR POSTURE!", (30, h - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

    cv2.imshow("AI Posture Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
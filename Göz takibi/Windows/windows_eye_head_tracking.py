"""
Windows Eye/Head Tracking Mouse Controller
-----------------------------------------
Production-oriented reference implementation that combines:
- MediaPipe Face Mesh landmarks
- Head pose (yaw/pitch) based pointer control
- Exponential smoothing + deadzone
- Blink detection (EAR) for click
- Optional dwell click

Requirements:
    pip install opencv-python mediapipe pyautogui numpy

Run:
    python windows_eye_head_tracking.py
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass

import cv2
import mediapipe as mp
import numpy as np
import pyautogui

# ----------------------------- Constants -----------------------------
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
TARGET_FPS = 30
FRAME_SKIP = 1  # process every frame; set 2 for half compute cost

# Mediapipe configuration
MAX_NUM_FACES = 1
REFINE_LANDMARKS = True
MIN_DETECTION_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.6

# Smoothing / mapping
SMOOTHING_ALPHA = 0.25   # exponential smoothing factor
CENTER_DEADZONE = 0.04   # ignore tiny head movements near center
MOVE_SCALE_X = 2.2
MOVE_SCALE_Y = 2.0
CALIBRATION_SECONDS = 2.0

# Blink (EAR)
EAR_BLINK_THRESHOLD = 0.19
EAR_CONSEC_FRAMES = 2
DOUBLE_BLINK_WINDOW = 0.5
BLINK_COOLDOWN = 0.3

# Dwell click (optional)
ENABLE_DWELL_CLICK = True
DWELL_RADIUS_PX = 40
DWELL_TIME_SEC = 1.1
DWELL_COOLDOWN_SEC = 1.0

# Face mesh indices (MediaPipe)
LEFT_EYE_LMS = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_LMS = [362, 385, 387, 263, 373, 380]

# Head pose anchor points (stable face mesh points)
POSE_LM_IDS = {
    "nose_tip": 1,
    "chin": 152,
    "left_eye_outer": 33,
    "right_eye_outer": 263,
    "mouth_left": 61,
    "mouth_right": 291,
}


@dataclass
class CalibrationState:
    is_calibrated: bool = False
    yaw_center: float = 0.0
    pitch_center: float = 0.0
    start_time: float = 0.0
    yaw_samples: list[float] | None = None
    pitch_samples: list[float] | None = None


class ExpSmoother:
    def __init__(self, alpha: float):
        self.alpha = alpha
        self.initialized = False
        self.x = 0.0
        self.y = 0.0

    def update(self, nx: float, ny: float) -> tuple[float, float]:
        if not self.initialized:
            self.x, self.y = nx, ny
            self.initialized = True
        else:
            self.x = self.alpha * nx + (1.0 - self.alpha) * self.x
            self.y = self.alpha * ny + (1.0 - self.alpha) * self.y
        return self.x, self.y


class DwellClick:
    def __init__(self, radius_px: int, dwell_sec: float, cooldown_sec: float):
        self.radius_px = radius_px
        self.dwell_sec = dwell_sec
        self.cooldown_sec = cooldown_sec
        self.anchor = None
        self.anchor_t = 0.0
        self.last_click_t = 0.0

    def update(self, point: tuple[int, int], now: float) -> bool:
        if now - self.last_click_t < self.cooldown_sec:
            return False

        if self.anchor is None:
            self.anchor = point
            self.anchor_t = now
            return False

        dist = np.hypot(point[0] - self.anchor[0], point[1] - self.anchor[1])
        if dist <= self.radius_px:
            if now - self.anchor_t >= self.dwell_sec:
                self.last_click_t = now
                self.anchor = None
                return True
        else:
            self.anchor = point
            self.anchor_t = now
        return False


def landmark_to_xy(landmark, width: int, height: int) -> tuple[int, int]:
    return int(landmark.x * width), int(landmark.y * height)


def eye_aspect_ratio(points: np.ndarray) -> float:
    # points order: p1, p2, p3, p4, p5, p6
    p1, p2, p3, p4, p5, p6 = points
    vertical_1 = np.linalg.norm(p2 - p6)
    vertical_2 = np.linalg.norm(p3 - p5)
    horizontal = np.linalg.norm(p1 - p4)
    if horizontal < 1e-6:
        return 0.0
    return (vertical_1 + vertical_2) / (2.0 * horizontal)


def solve_head_pose(landmarks, frame_w: int, frame_h: int) -> tuple[float, float]:
    image_points = np.array(
        [
            landmark_to_xy(landmarks[POSE_LM_IDS["nose_tip"]], frame_w, frame_h),
            landmark_to_xy(landmarks[POSE_LM_IDS["chin"]], frame_w, frame_h),
            landmark_to_xy(landmarks[POSE_LM_IDS["left_eye_outer"]], frame_w, frame_h),
            landmark_to_xy(landmarks[POSE_LM_IDS["right_eye_outer"]], frame_w, frame_h),
            landmark_to_xy(landmarks[POSE_LM_IDS["mouth_left"]], frame_w, frame_h),
            landmark_to_xy(landmarks[POSE_LM_IDS["mouth_right"]], frame_w, frame_h),
        ],
        dtype=np.float64,
    )

    model_points = np.array(
        [
            (0.0, 0.0, 0.0),
            (0.0, -63.6, -12.5),
            (-43.3, 32.7, -26.0),
            (43.3, 32.7, -26.0),
            (-28.9, -28.9, -24.1),
            (28.9, -28.9, -24.1),
        ],
        dtype=np.float64,
    )

    focal_length = frame_w
    center = (frame_w / 2, frame_h / 2)
    camera_matrix = np.array(
        [[focal_length, 0, center[0]], [0, focal_length, center[1]], [0, 0, 1]],
        dtype=np.float64,
    )
    dist_coeffs = np.zeros((4, 1), dtype=np.float64)

    success, rvec, _ = cv2.solvePnP(
        model_points,
        image_points,
        camera_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE,
    )
    if not success:
        return 0.0, 0.0

    rotation_matrix, _ = cv2.Rodrigues(rvec)
    proj_matrix = np.hstack((rotation_matrix, np.zeros((3, 1), dtype=np.float64)))
    _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(proj_matrix)

    pitch = float(euler_angles[0]) / 45.0
    yaw = float(euler_angles[1]) / 45.0
    return yaw, pitch


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def normalized_to_screen(nx: float, ny: float, screen_w: int, screen_h: int) -> tuple[int, int]:
    sx = int(clamp01(nx) * (screen_w - 1))
    sy = int(clamp01(ny) * (screen_h - 1))
    return sx, sy


def apply_deadzone(value: float, deadzone: float) -> float:
    if abs(value) < deadzone:
        return 0.0
    if value > 0:
        return (value - deadzone) / (1 - deadzone)
    return (value + deadzone) / (1 - deadzone)


def main() -> None:
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.0
    screen_w, screen_h = pyautogui.size()

    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)

    face_mesh = mp.solutions.face_mesh.FaceMesh(
        max_num_faces=MAX_NUM_FACES,
        refine_landmarks=REFINE_LANDMARKS,
        min_detection_confidence=MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
    )

    smoother = ExpSmoother(SMOOTHING_ALPHA)
    dwell = DwellClick(DWELL_RADIUS_PX, DWELL_TIME_SEC, DWELL_COOLDOWN_SEC)

    calibration = CalibrationState(
        is_calibrated=False,
        start_time=time.time(),
        yaw_samples=[],
        pitch_samples=[],
    )

    blink_frames = 0
    blink_times = deque(maxlen=4)
    last_click_t = 0.0
    frame_counter = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame_counter += 1
        if FRAME_SKIP > 1 and frame_counter % FRAME_SKIP != 0:
            continue

        frame = cv2.flip(frame, 1)
        frame_h, frame_w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)

        now = time.time()

        if result.multi_face_landmarks:
            face = result.multi_face_landmarks[0]
            lms = face.landmark

            yaw, pitch = solve_head_pose(lms, frame_w, frame_h)

            if not calibration.is_calibrated:
                calibration.yaw_samples.append(yaw)
                calibration.pitch_samples.append(pitch)
                elapsed = now - calibration.start_time
                cv2.putText(
                    frame,
                    f"Calibrating... keep head centered ({CALIBRATION_SECONDS - elapsed:.1f}s)",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                )
                if elapsed >= CALIBRATION_SECONDS:
                    calibration.yaw_center = float(np.mean(calibration.yaw_samples))
                    calibration.pitch_center = float(np.mean(calibration.pitch_samples))
                    calibration.is_calibrated = True
                cv2.imshow("Eye/Head Mouse", frame)
                if cv2.waitKey(1) & 0xFF == 27:
                    break
                continue

            rel_yaw = (yaw - calibration.yaw_center) * MOVE_SCALE_X
            rel_pitch = (pitch - calibration.pitch_center) * MOVE_SCALE_Y

            rel_yaw = apply_deadzone(rel_yaw, CENTER_DEADZONE)
            rel_pitch = apply_deadzone(rel_pitch, CENTER_DEADZONE)

            nx = 0.5 + rel_yaw * 0.5
            ny = 0.5 + rel_pitch * 0.5

            sx_norm, sy_norm = smoother.update(nx, ny)
            sx, sy = normalized_to_screen(sx_norm, sy_norm, screen_w, screen_h)

            pyautogui.moveTo(sx, sy, _pause=False)

            # Blink detection from EAR
            left_eye = np.array([landmark_to_xy(lms[i], frame_w, frame_h) for i in LEFT_EYE_LMS], dtype=np.float32)
            right_eye = np.array([landmark_to_xy(lms[i], frame_w, frame_h) for i in RIGHT_EYE_LMS], dtype=np.float32)
            ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2.0

            if ear < EAR_BLINK_THRESHOLD:
                blink_frames += 1
            else:
                if blink_frames >= EAR_CONSEC_FRAMES:
                    blink_times.append(now)
                    if now - last_click_t > BLINK_COOLDOWN:
                        pyautogui.click(button="left")
                        last_click_t = now
                blink_frames = 0

            # Optional double blink -> right click
            if len(blink_times) >= 2 and (blink_times[-1] - blink_times[-2]) <= DOUBLE_BLINK_WINDOW:
                if now - last_click_t > BLINK_COOLDOWN:
                    pyautogui.click(button="right")
                    last_click_t = now
                blink_times.clear()

            if ENABLE_DWELL_CLICK and dwell.update((sx, sy), now):
                pyautogui.click(button="left")

            cv2.putText(frame, f"EAR: {ear:.3f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, f"Yaw/Pitch: {yaw:.2f}/{pitch:.2f}", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)
            cv2.circle(frame, (int(sx_norm * frame_w), int(sy_norm * frame_h)), 8, (0, 0, 255), -1)

        cv2.imshow("Eye/Head Mouse", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        if key == ord("c"):
            calibration.is_calibrated = False
            calibration.start_time = time.time()
            calibration.yaw_samples = []
            calibration.pitch_samples = []

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

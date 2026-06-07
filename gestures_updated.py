import cv2
import mediapipe as mp
import numpy as np
import math
import os
import time

# Full path to adb
ADB_PATH = "C:\\Users\Home\OneDrive\Desktop\platform-tools\\adb.exe" 

# Webcam
cap = cv2.VideoCapture(0)

# MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# Gesture cooldown setup
last_action_time = time.time()
cooldown = 1  # in seconds

# ADB command helper
def run_adb(command):
    os.system(f'"{ADB_PATH}" shell {command}')

def adb_volume_control(action):
    if action == "up":
        run_adb("input keyevent 24")
    elif action == "down":
        run_adb("input keyevent 25")

def adb_swipe(direction):
    if direction == "left":
        run_adb("input swipe 800 800 200 800")  # Swipe left
    elif direction == "right":
        run_adb("input swipe 200 800 800 800")  # Swipe right
    elif direction == "scroll":
        run_adb("input swipe 500 800 500 300")  # Scroll up

def adb_open_camera():
    run_adb("am start -a android.media.action.IMAGE_CAPTURE")

while True:
    success, img = cap.read()
    if not success:
        break

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    lm_list = []

    if results.multi_hand_landmarks:
        handLms = results.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

        for id, lm in enumerate(handLms.landmark):
            h, w, c = img.shape
            cx, cy = int(lm.x * w), int(lm.y * h)
            lm_list.append((id, cx, cy))

        if lm_list:
            x1, y1 = lm_list[4][1], lm_list[4][2]   # Thumb tip
            x2, y2 = lm_list[8][1], lm_list[8][2]   # Index tip
            x3, y3 = lm_list[12][1], lm_list[12][2] # Middle tip

            # Draw line
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 0), 3)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            cv2.circle(img, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

            # Calculate thumb-index distance
            length = math.hypot(x2 - x1, y2 - y1)

            current_time = time.time()

            # Volume control
            if current_time - last_action_time > cooldown:
                if length < 30:
                    adb_volume_control("down")
                    last_action_time = current_time
                elif length > 150:
                    adb_volume_control("up")
                    last_action_time = current_time

            # Swipe gesture (based on thumb to middle finger)
            swipe_length = x3 - x1
            if abs(swipe_length) > 100 and (current_time - last_action_time > cooldown):
                if swipe_length > 0:
                    adb_swipe("right")
                else:
                    adb_swipe("left")
                last_action_time = current_time

            # Scroll gesture (hand lifted up)
            if y1 < 200 and (current_time - last_action_time > cooldown):
                adb_swipe("scroll")
                last_action_time = current_time

            # Open camera (hand closed — tip fingers close together)
            fist_close = math.hypot(x2 - x3, y2 - y3)
            if fist_close < 20 and (current_time - last_action_time > cooldown):
                adb_open_camera()
                last_action_time = current_time

    cv2.imshow("Gesture Control", img)
    key = cv2.waitKey(1)
    if key == ord('q') or cv2.getWindowProperty("Gesture Control", cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()
cv2.waitKey(1)

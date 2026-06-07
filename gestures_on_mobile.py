import cv2
import mediapipe as mp
import numpy as np
import math
import os

# Webcam 
cap = cv2.VideoCapture(0)

# MediaPipe setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils

# ADB command
ADB_PATH = "C:\\Users\Home\OneDrive\Desktop\platform-tools\\adb.exe"  # ← adjust this path if needed

def adb_volume_control(action):
    if action == "up":
        os.system(f'"{ADB_PATH}" shell input keyevent 24')
    elif action == "down":
        os.system(f'"{ADB_PATH}" shell input keyevent 25')


while True:
    success, img = cap.read()
    if not success:
        break

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    lm_list = []

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)
            for id, lm in enumerate(handLms.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lm_list.append((id, cx, cy))

        if lm_list:
            x1, y1 = lm_list[4][1], lm_list[4][2]  # Thumb tip
            x2, y2 = lm_list[8][1], lm_list[8][2]  # Index tip
            length = math.hypot(x2 - x1, y2 - y1)

            # Gesture feedback
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 0), 3)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            cv2.circle(img, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

            # ADB volume trigger
            if length < 30:
                adb_volume_control("down")
            elif length > 150:
                adb_volume_control("up")

    cv2.imshow("Mobile Gesture Control", img)

    key = cv2.waitKey(1)
    if key == ord('q') or cv2.getWindowProperty("Mobile Gesture Control", cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()
cv2.waitKey(1)

import cv2
import mediapipe as mp
import numpy as np
import math
import os
import time
import speech_recognition as sr
import threading

# Path to adb.exe
ADB_PATH = "C:\\Users\Home\OneDrive\Desktop\platform-tools\\adb.exe"  # Change if needed

# Webcam
cap = cv2.VideoCapture(0)

# MediaPipe setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# Cooldown to avoid repeating gestures rapidly
last_action_time = time.time()
cooldown = 1  # in seconds

def run_adb(command):
    os.system(f'"{ADB_PATH}" shell {command}')

def adb_volume_control(action):
    if action == "up":
        run_adb("input keyevent 24")
    elif action == "down":
        run_adb("input keyevent 25")

def adb_swipe(direction):
    if direction == "left":
        run_adb("input swipe 800 800 200 800")
    elif direction == "right":
        run_adb("input swipe 200 800 800 800")
    elif direction == "scroll":
        run_adb("input swipe 500 800 500 300")

def adb_open_camera():
    run_adb("am start -a android.media.action.IMAGE_CAPTURE")

#  Voice Command Listener
def listen_to_voice():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)

    print("[Voice Assistant] Ready for commands...")

    while True:
        with mic as source:
            try:
                audio = recognizer.listen(source, timeout=5)
                command = recognizer.recognize_google(audio).lower()
                print(f"[Voice] You said: {command}")

                if "volume up" in command:
                    adb_volume_control("up")
                elif "volume down" in command:
                    adb_volume_control("down")
                elif "swipe left" in command:
                    adb_swipe("left")
                elif "swipe right" in command:
                    adb_swipe("right")
                elif "scroll down" in command:
                    adb_swipe("scroll")
                elif "open camera" in command:
                    adb_open_camera()

            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                print("[Voice] Could not understand.")
            except Exception as e:
                print(f"[Voice] Error: {e}")

#  Run voice listener in a separate thread
voice_thread = threading.Thread(target=listen_to_voice, daemon=True)
voice_thread.start()

#  Gesture detection loop
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
            x1, y1 = lm_list[4][1], lm_list[4][2]   # Thumb
            x2, y2 = lm_list[8][1], lm_list[8][2]   # Index
            x3, y3 = lm_list[12][1], lm_list[12][2] # Middle

            length = math.hypot(x2 - x1, y2 - y1)
            swipe_length = x3 - x1
            fist_close = math.hypot(x2 - x3, y2 - y3)

            current_time = time.time()

            if current_time - last_action_time > cooldown:
                if length < 30:
                    adb_volume_control("down")
                    last_action_time = current_time
                elif length > 150:
                    adb_volume_control("up")
                    last_action_time = current_time
                elif abs(swipe_length) > 100:
                    adb_swipe("right" if swipe_length > 0 else "left")
                    last_action_time = current_time
                elif y1 < 200:
                    adb_swipe("scroll")
                    last_action_time = current_time
                elif fist_close < 20:
                    adb_open_camera()
                    last_action_time = current_time

    cv2.imshow("Voice + Gesture Control", img)
    key = cv2.waitKey(1)
    if key == ord('q') or cv2.getWindowProperty("Voice + Gesture Control", cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()
cv2.waitKey(1)

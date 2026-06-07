import cv2
import mediapipe as mp
import numpy as np
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import math

# Setup camera
cap = cv2.VideoCapture(0)

# MediaPipe hands module
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils

# Audio setup
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

vol_range = volume.GetVolumeRange()
min_vol = vol_range[0]
max_vol = vol_range[1]

while True:
    success, img = cap.read()
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)

    lm_list = []

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            for id, lm in enumerate(handLms.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lm_list.append((id, cx, cy))
            
            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

        # Thumb tip: id 4 | Index finger tip: id 8
        if lm_list:
            x1, y1 = lm_list[4][1], lm_list[4][2]
            x2, y2 = lm_list[8][1], lm_list[8][2]
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            # Draw line and circle
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 0), 3)
            cv2.circle(img, (cx, cy), 10, (255, 0, 255), cv2.FILLED)

            # Calculate distance
            length = math.hypot(x2 - x1, y2 - y1)

            # Convert to volume level
            vol = np.interp(length, [20, 180], [min_vol, max_vol])
            volume.SetMasterVolumeLevel(vol, None)

            # Visual volume bar
            vol_bar = np.interp(length, [20, 180], [400, 150])
            cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 2)
            cv2.rectangle(img, (50, int(vol_bar)), (85, 400), (0, 255, 0), cv2.FILLED)

    cv2.imshow("Volume Control", img)

    # Proper exit: 'q' key OR window close button
    key = cv2.waitKey(1)
    if key == ord('q') or cv2.getWindowProperty("Volume Control", cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()
cv2.waitKey(1)  # Extra wait for proper cleanup


import cv2 
import time
import random
import mediapipe as mp

# -----------------------
# Config
# -----------------------
COUNTDOWN_SEC = 3            # countdown time every match
WIN_SCORE = 2                # 3 matches 2 wins
SHOW_RESULT_SEC = 1.5        # time to show win/lose/draw result
FPS_TEXT_POS = (10, 30)

# -----------------------
# MediaPipe Hands
# -----------------------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# -----------------------
# Tools: classify gesture
# -----------------------
def finger_states(landmarks, handedness_label):
    def is_finger_extended(tip, pip, mcp):
        return (tip.y < pip.y) and (pip.y < mcp.y)

    index  = is_finger_extended(landmarks[8],  landmarks[6],  landmarks[5])
    middle = is_finger_extended(landmarks[12], landmarks[10], landmarks[9])
    ring   = is_finger_extended(landmarks[16], landmarks[14], landmarks[13])
    pinky  = is_finger_extended(landmarks[20], landmarks[18], landmarks[17])

    if handedness_label == 'Right':
        thumb = landmarks[4].x < landmarks[2].x
    else:
        thumb = landmarks[4].x > landmarks[2].x

    return thumb, index, middle, ring, pinky

def classify_gesture(landmarks, handedness_label):
    thumb, idx, mid, ring, pinky = finger_states(landmarks, handedness_label)
    extended = [thumb, idx, mid, ring, pinky]
    count_ext = sum(extended)

    if count_ext >= 4 and idx and mid and ring and pinky:
        return 'paper'
    if idx and mid and (not ring) and (not pinky):
        return 'scissors'
    if count_ext <= 1 and (not idx) and (not mid) and (not ring) and (not pinky):
        return 'rock'
    return 'unknown'

# -----------------------
# Decide the winner
# -----------------------
def judge(player, comp):
    if player == comp:
        return 'draw'
    rules = {'rock': 'scissors', 'scissors': 'paper', 'paper': 'rock'}
    return 'win' if rules.get(player, None) == comp else 'lose'

# -----------------------
#  Screen assist
# -----------------------
def draw_center_text(img, text, color=(255,255,255), scale=2, thickness=3, dy=0):
    h, w = img.shape[:2]
    size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
    x = (w - size[0]) // 2
    y = (h + size[1]) // 2 + dy
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)

def draw_choice_block(img, label, position='left'):
    h, w = img.shape[:2]
    block_w, block_h = 220, 80
    y1 = 30
    x1 = 30 if position == 'left' else w - 30 - block_w
    x2, y2 = x1 + block_w, y1 + block_h
    cv2.rectangle(img, (x1, y1), (x2, y2), (200,200,200), 2)
    cv2.putText(img, label, (x1 + 15, y1 + 55), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,255,0), 3, cv2.LINE_AA)

def draw_choice_block(img, label, position='left'):
    h, w = img.shape[:2]
    block_w, block_h = 220, 80
    y1 = 50
    x1 = 30 if position == 'left' else w - 30 - block_w
    x2, y2 = x1 + block_w, y1 + block_h

    # draw rectangle
    cv2.rectangle(img, (x1, y1), (x2, y2), (200,200,200), 2)

    # auto scale text to fit in the block
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 1.5
    thickness = 3
    max_width = block_w - 20   # leave some margin
    text_size, _ = cv2.getTextSize(label, font, scale, thickness)

    # if the text is too wide, reset scale
    while text_size[0] > max_width and scale > 0.5:
        scale -= 0.1
        text_size, _ = cv2.getTextSize(label, font, scale, thickness)

    # auto center text
    text_w, text_h = text_size
    x_text = x1 + (block_w - text_w) // 2
    y_text = y1 + (block_h + text_h) // 2  # 注意OpenCV的y是基线，所以+text_h/2

    # draw text
    cv2.putText(img, label, (x_text, y_text), font, scale, (0,255,0), thickness, cv2.LINE_AA)

def win_lose_flash(frame, result, t0, duration=SHOW_RESULT_SEC):
    elapsed = time.time() - t0
    phase = int(elapsed * 6) % 2
    if result == 'win':
        color = (0, 255, 0) if phase == 0 else (0, 180, 0)
        draw_center_text(frame, "YOU WIN!", color, 2.0, 4)
    elif result == 'lose':
        color = (0, 0, 255) if phase == 0 else (0, 0, 180)
        draw_center_text(frame, "YOU LOSE!", color, 2.0, 4)
    else:
        draw_center_text(frame, "DRAW", (255,255,0), 2.0, 4)

# -----------------------
# Game State
# -----------------------
player_score = 0
computer_score = 0
state = 'waiting'
count_start = None
reveal_time = None
player_choice = None
computer_choice = None

cap = cv2.VideoCapture(0)
prev = time.time()
fps = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)

        # resize 
        frame = cv2.resize(frame, (960, 720))

        # FPS
        now = time.time()
        fps = 0.9*fps + 0.1*(1.0/(now - prev))
        prev = now

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        # draw hand landmarks
        if results.multi_hand_landmarks:
            for lm in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame, lm, mp_hands.HAND_CONNECTIONS,
                    mp_styles.get_default_hand_landmarks_style(),
                    mp_styles.get_default_hand_connections_style()
                )

        # scores and FPS
        score_text = f"YOU {player_score} : {computer_score} CPU"
        cv2.putText(frame, score_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255,255,255), 3, cv2.LINE_AA)
        cv2.putText(frame, f"FPS: {int(fps)}", FPS_TEXT_POS, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180,180,180), 1)

        # final score
        if player_score == WIN_SCORE or computer_score == WIN_SCORE:
            final = "MATCH WIN!" if player_score > computer_score else "MATCH LOSE!"
            draw_center_text(frame, final, (0,255,0) if player_score>computer_score else (0,0,255), 2.2, 5, dy=-40)
            draw_center_text(frame, "Press R to restart, ESC to quit", (255,255,255), 0.9, 2, dy=40)
            cv2.imshow("RPS", frame)
            key = cv2.waitKey(5) & 0xFF
            if key == 27: break
            if key in (ord('r'), ord('R')):
                player_score = 0
                computer_score = 0
                player_choice = None
                computer_choice = None
                state = 'waiting'
            continue

        # state machine
        if state == 'waiting':
            draw_center_text(frame, "Press SPACE to start", (255,255,255), 1.2, 2)
            cv2.imshow("RPS", frame)
            key = cv2.waitKey(5) & 0xFF
            if key == 27: break
            if key == 32:  # SPACE
                player_choice = None
                computer_choice = None
                count_start = time.time()
                state = 'counting'

        elif state == 'counting':
            remain = COUNTDOWN_SEC - (time.time() - count_start)
            n = max(0, int(remain) + 1)
            draw_center_text(frame, f"{n}", (0,255,255), 3.0, 6)

            if results.multi_hand_landmarks and results.multi_handedness and len(results.multi_handedness) >= 1:
                lm = results.multi_hand_landmarks[0].landmark
                handed = results.multi_handedness[0].classification[0].label
                player_choice = classify_gesture(lm, handed)

            if remain <= 0:
                p = player_choice if player_choice in ('rock','paper','scissors') else 'unknown'
                c = random.choice(['rock','paper','scissors'])
                player_choice, computer_choice = p, c
                reveal_time = time.time()
                state = 'reveal'

            cv2.imshow("RPS", frame)
            if cv2.waitKey(5) & 0xFF == 27: break

        elif state == 'reveal':
            draw_choice_block(frame, f"YOU: {player_choice.upper() if player_choice!='unknown' else '???'}", 'left')
            draw_choice_block(frame, f"CPU: {computer_choice.upper()}", 'right')
            draw_center_text(frame, "SHOOT!", (255,255,255), 1.4, 3, dy=60)

            cv2.imshow("RPS", frame)
            if cv2.waitKey(5) & 0xFF == 27: break

            if time.time() - reveal_time >= 0.8:
                result = 'draw' if player_choice == 'unknown' else judge(player_choice, computer_choice)
                result_time = time.time()
                if result == 'win': player_score += 1
                elif result == 'lose': computer_score += 1
                state = ('result', result, result_time)

        elif isinstance(state, tuple) and state[0] == 'result':
            _, result, t0 = state
            draw_choice_block(frame, f"YOU: {player_choice.upper() if player_choice!='unknown' else '???'}", 'left')
            draw_choice_block(frame, f"CPU: {computer_choice.upper()}", 'right')
            win_lose_flash(frame, result, t0)

            cv2.imshow("RPS", frame)
            key = cv2.waitKey(5) & 0xFF
            if key == 27: break
            if time.time() - t0 > SHOW_RESULT_SEC:
                state = 'waiting'

finally:
    cap.release()
    cv2.destroyAllWindows()
    hands.close()

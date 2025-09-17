# Rock–Paper–Scissors with MediaPipe (Python)

## Introduction

A minimal interactive Rock–Paper–Scissors game using MediaPipe Hands + OpenCV.
Show your hand gesture to the camera; after a countdown, the computer reveals its choice simultaneously.
The app judges the round, keeps score (best-of-3), and shows a simple win/lose animation.

## ✨ Features

- Real-time hand gesture recognition (✊ rock/ ✌️ scissors/ 🖐 paper)

- Synchronized reveal after countdown

- Round result + scoring (BO3)

- Simple win/lose animations

- Minimal dependencies, beginner-friendly

## 📸 Screenshots & Demo

### Screenshot
<img src="assets/screenshot.png" alt="Screenshot" width="400"/>

### Demo GIF
<img src="assets/media.gif" alt="Demo Gameplay" width="400"/>

## 🛠 Setup

Python 3.10/3.11 recommended.

```bash
# Conda
conda create -n mp_env python=3.10 -y
conda activate mp_env
pip install -r requirements.txt

# venv
python -m venv .venv

# Windows:
.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

## ▶️ Run

```bash
python rps_game.py
```

- Space to start a round
- Esc to quit
- First to 2 wins the match

## 🎮 Playing methods and rules

- Countdown: Default 3 seconds
- Synchronous card play: After the countdown is over, the program locks the player's gestures and randomly generates computer gestures.
- Rules for judgment: Stones beat scissors, scissors beat cloth, cloth beat stones; identification failure is recorded as ???, this game will be judged or scored (can be modified in the code)

## 🧩 Gesture Rules (simplified)

- Paper: index/middle/ring/pinky extended
- Scissors: index + middle extended, others folded
- Rock: fingers folded; thumb flexible
- Decisions are made from MediaPipe landmarks (x/y).


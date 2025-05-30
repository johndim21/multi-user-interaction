# Multiuser Real-Time Interaction GUI

This is a real-time multi-user interaction system built with YOLOv11 and Python. It supports:

- Pose-based keypoint streaming (`osc_sender_yolov11`)
- Hand-voting detection (`hand_voting_yolov11`)

## Features

- Select camera source (webcam or RTSP)
- View live video feed with annotations
- OSC message stats panel

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Place `yolo11n-pose.pt` in the `gui_app` directory.

3. Run the GUI:

```bash
python run_app.py
```

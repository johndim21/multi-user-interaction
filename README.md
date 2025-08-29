# Multi-User Interaction Module

This project provides a **real-time multi-user interaction system** that
combines computer vision and Open Sound Control (OSC) messaging. It
enables multiple participants to interact naturally in an installation,
performance, or research setting by detecting body poses and gestures
and transmitting them to other applications (such as
AAASeed) for visualization.

## ✨ Features

-   **Pose detection** using
    [YOLOv11-Pose](https://github.com/ultralytics/ultralytics).
-   **Multi-user support** for detecting and tracking multiple people in
    a camera feed.
-   **Gesture-based interactions** (e.g., hand voting).
-   **OSC communication** for sending keypoints and interaction data to
    other apps.
-   **User-friendly GUI** built with Tkinter to:
    -   Select the camera
    -   Choose between modules (pose sender or hand voting)
    -   View live annotated video
    -   Monitor OSC messages and detection stats

## 📂 Project Structure

    multi-user-interaction-main/
    │── run_app.py              # Main entrypoint for launching the GUI
    │── requirements.txt        # Python dependencies
    │── yolo11n-pose.pt         # YOLOv11-Pose model weights
    │
    └── gui_app/
        ├── multiuser_gui.py        # Tkinter GUI logic
        ├── osc_sender_yolov11.py   # Pose detection + OSC sender
        ├── hand_voting_yolov11.py  # Hand voting interaction module
        └── yolo11n-pose.pt         # Local copy of model weights

## 🛠 Installation

1.  Clone this repository or download the ZIP and extract it:

    ``` bash
    git clone https://github.com/johndim21/multi-user-interaction.git
    cd multi-user-interaction
    ```

2.  Create and activate a virtual environment (recommended):

    ``` bash
    python -m venv venv
    source venv/bin/activate   # On macOS/Linux
    venv\Scripts\activate      # On Windows
    ```

3.  Install dependencies:

    ``` bash
    pip install -r requirements.txt
    ```

4.  Make sure you have a working camera (webcam or IP camera).

## 🚀 Usage

Start the application with:

``` bash
python run_app.py
```

### GUI Options

-   **OSC Sender (Pose Detection):**\
    Detects multiple users' body poses and sends keypoints over OSC.

-   **Hand Voting Module:**\
    Recognizes simple hand gestures for voting/interaction and sends
    results via OSC.

-   **Camera Selection:**\
    Choose the camera source directly from the GUI.

The live video window will show detected users with keypoints and
annotated gestures, while the right panel displays **detection
statistics** and **sent OSC messages**.

## 🔌 OSC Integration

-   The module sends data via the [OSC
    protocol](https://opensoundcontrol.stanford.edu/).\
-   Default OSC settings can be configured in the code
    (`osc_sender_yolov11.py` or `hand_voting_yolov11.py`).\
-   Works seamlessly with AAASeed for real-time
    visualization.

## 📦 Requirements

-   Python 3.9+
-   Webcam or IP camera
-   Dependencies listed in `requirements.txt` (YOLO, OpenCV, Tkinter,
    python-osc, etc.)

## 🎨 Example Use Cases

-   Interactive art installations
-   Multi-user performances
-   Live exhibitions and participatory experiences
-   Research on natural multi-user interactions

## 📖 License

MIT License. See [LICENSE](LICENSE) for details.

------------------------------------------------------------------------

### Acknowledgments

Developed as part of the **Artcast4D Project** (Work Package 2, Task 2.4
"Natural multi-user interaction").\
This project has received funding from the European Union’s Horizon Europe research and innovation programme under grant agreement No 101061163.\
Powered by [Ultralytics
YOLO](https://github.com/ultralytics/ultralytics).

import cv2
import numpy as np
from ultralytics import YOLO
import time
from pythonosc import udp_client
import threading
import queue

model = YOLO('yolo11n-pose.pt')
osc_client = udp_client.SimpleUDPClient(address="127.0.0.1", port=18010)
ch_name = "OSC_hand_voting"
i_frame = 1
n_points = 17

class VideoCapture:
    def __init__(self, source):
        self.cap = cv2.VideoCapture(source)
        self.q = queue.Queue()
        self.running = True
        self.t = threading.Thread(target=self._reader)
        self.t.daemon = True
        self.t.start()

    def _reader(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()
                except queue.Empty:
                    pass
            self.q.put(frame)
            self.state = ret

    def read(self):
        return self.q.get(), self.state

    def stop(self):
        self.running = False
        self.t.join()
        self.cap.release()

def run_osc_sender(camera_source, update_frame, update_stats, running_flag):
    global i_frame
    rtsp_stream = VideoCapture(camera_source)
    fps = 0
    frame_rate = 15

    while rtsp_stream.cap.isOpened() and running_flag():
        frame, success = rtsp_stream.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        start_time = time.time()

        results = model(frame)

        person_count = 0
        for result in results:
            frame = result.plot()
            for person, keypoints in enumerate(result.keypoints.xyn.cpu().numpy()):
                person_count += 1
                data_for_OSC = [ch_name, i_frame, "P", person + 1, 2, n_points]
                for i, keypoint in enumerate(keypoints):
                    data_x, data_y = keypoint
                    data_x = np.float64(data_x * 10)
                    data_y = np.float64(1 - data_y) * 10
                    id = i + 1
                    data_for_OSC += [id, data_x, data_y]
                osc_client.send_message("/AAASeed/ndim/begin", [ch_name, i_frame, 2, n_points])
                osc_client.send_message("/AAASeed/ndim/group_data", data_for_OSC)
                osc_client.send_message("/AAASeed/ndim/end", [ch_name, i_frame])

        loop_time = time.time() - start_time
        if loop_time > 0:
            fps = 0.9 * fps + 0.1 / loop_time

        update_stats({"people": person_count, "fps": fps})
        update_frame(frame)
        # i_frame += 1

    rtsp_stream.stop()
    update_stats({"people": 0, "fps": 0})
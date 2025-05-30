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
n_pairs = 1

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

def run_hand_voting(camera_source, update_frame, update_stats, running_flag):
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

        peopleDetected   = 0
        handsDownCounter = 0
        handsUpCounter   = 0
        rightHandCounter = 0
        leftHandCounter  = 0
        raisedHandsList  = []
        x_coord_for_eye  = 0

        results = model(frame)

        for result in results:
            data_for_OSC = [ch_name, i_frame, "HandsRaised", 1, 3, n_pairs]
            boxes = result.boxes
            keypoints = result.keypoints.xyn.cpu().numpy()
            peopleDetected = len(boxes)

            for b, k in zip(boxes, keypoints):
                leftHandUp = False
                rightHandUp = False
                # Check if left wrist (k[9][1]) is higher than left elbow (k[7][1]) and left elbow (k[7][1]) is higher than left shoulder (k[5][1]) 
                if not k[9][1] == 0  and not k[0][1] == 0:
                    if k[9][1] < k[0][1]:
                        rightHandUp = True
                        raisedHandsList.append(k[0][0])
                # Check if right wrist (k[10][1]) is higher than right elbow (k[8][1]) and right elbow (k[8][1]) is higher than right shoulder (k[6][1]) 
                if not k[10][1] == 0 and not k[0][1] == 0:
                    if k[10][1] < k[0][1]:
                        leftHandUp = True
                        raisedHandsList.append(k[0][0])
                
                if leftHandUp and rightHandUp:
                    text = 'Both hands up'
                    handsUpCounter += 1
                elif leftHandUp and not rightHandUp:
                    text = 'Left hand up'
                    leftHandCounter += 1
                elif not leftHandUp and rightHandUp:
                    text = 'Right hand up'
                    rightHandCounter += 1
                else:
                    text = 'Hands down'
                    handsDownCounter += 1

                x_min, y_min, x_max, y_max = b.xyxy[0].cpu().numpy()
                frame = cv2.rectangle(
                                frame, 
                                (int(x_min), int(y_min)),(int(x_max), int(y_max)), 
                                (0,0,255), 2
                            )
                (w, h), _ = cv2.getTextSize(
                        text.upper(), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
                    )
                frame = cv2.rectangle(
                                frame, 
                                (int(x_min), int(y_min)-20),(int(x_min)+w, int(y_min)), 
                                (0,0,255), -1
                            )
                cv2.putText(frame,
                            f'{text}',
                            (int(x_min), int(y_min)-4),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (255, 255, 255),
                            thickness=2
                        )
        
        raised_hands = rightHandCounter + leftHandCounter
        new_min = -0.07
        new_max = 0.07

        if len(raisedHandsList) == 0:
            x_coord_for_eye = 0
        elif len(raisedHandsList) == 1:
             x_coord_for_eye = raisedHandsList[0]
        else:
            # i = randrange(len(raisedHandsList))
            # x_coord_for_eye = raisedHandsList[i]
            x_coord_for_eye = raisedHandsList[0]
        
        x_norm = x_coord_for_eye * (new_max - new_min) + new_min
        if x_norm == -0.07:
            x_norm = 0

        x_norm = np.float64(x_norm)

        data_for_OSC += [i_frame, peopleDetected, raised_hands, x_norm]
        osc_client.send_message("/AAASeed/ndim/begin", [ch_name, i_frame, 2, n_pairs])
        osc_client.send_message("/AAASeed/ndim/group_data", data_for_OSC)
        osc_client.send_message("/AAASeed/ndim/end", [ch_name, i_frame])

        loop_time = time.time() - start_time
        if loop_time > 0:
            fps = 0.9 * fps + 0.1 / loop_time

        update_stats({"people": peopleDetected, "hands": raised_hands, "fps": fps})
        update_frame(frame)
        # i_frame += 1

    rtsp_stream.stop()
    update_stats({"people": 0, "hands": 0, "fps": 0})
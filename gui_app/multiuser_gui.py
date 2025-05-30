import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import cv2
from PIL import Image, ImageTk
from gui_app.osc_sender_yolov11 import run_osc_sender
from gui_app.hand_voting_yolov11 import run_hand_voting

class MultiUserGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-user Interaction Module")
        self.root.geometry("1000x800")

        self.script_choice = tk.StringVar(value="osc_sender_yolov11")
        self.source_type = tk.StringVar(value="Webcam")
        self.camera_index = tk.IntVar(value=0)
        self.ip_address = tk.StringVar()
        self.port = tk.StringVar(value="554")
        self.username = tk.StringVar()
        self.password = tk.StringVar()

        self.running = False
        self.worker_thread = None
        self.frame_queue = queue.Queue()
        self.stats_queue = queue.Queue()

        self.build_gui()
        self.poll_queues()

    def build_gui(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Select Script:").grid(row=0, column=0, sticky="w")
        ttk.Combobox(frame, textvariable=self.script_choice,
                     values=["osc_sender_yolov11", "hand_voting_yolov11"],
                     state="readonly").grid(row=0, column=1, sticky="w")

        ttk.Label(frame, text="Source Type:").grid(row=1, column=0, sticky="w")
        ttk.Combobox(frame, textvariable=self.source_type,
                     values=["Webcam", "RTSP"], state="readonly", width=10).grid(row=1, column=1, sticky="w")

        self.cam_entry = ttk.Entry(frame, textvariable=self.camera_index, width=5)
        ttk.Label(frame, text="Webcam Index:").grid(row=2, column=0, sticky="w")
        self.cam_entry.grid(row=2, column=1, sticky="w")

        self.rtsp_fields = ttk.Frame(frame)
        ttk.Label(self.rtsp_fields, text="IP Address:").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.rtsp_fields, textvariable=self.ip_address).grid(row=0, column=1)
        ttk.Label(self.rtsp_fields, text="Port:").grid(row=1, column=0, sticky="w")
        ttk.Entry(self.rtsp_fields, textvariable=self.port).grid(row=1, column=1)
        ttk.Label(self.rtsp_fields, text="Username:").grid(row=2, column=0, sticky="w")
        ttk.Entry(self.rtsp_fields, textvariable=self.username).grid(row=2, column=1)
        ttk.Label(self.rtsp_fields, text="Password:").grid(row=3, column=0, sticky="w")
        ttk.Entry(self.rtsp_fields, textvariable=self.password, show="*").grid(row=3, column=1)
        self.rtsp_fields.grid(row=3, column=0, columnspan=2, pady=5)
        self.rtsp_fields.grid_remove()

        self.source_type.trace_add("write", self.toggle_source_fields)
        self.script_choice.trace_add("write", self.toggle_stats_fields)

        ttk.Button(frame, text="Start", command=self.start_script).grid(row=4, column=0, pady=10)
        ttk.Button(frame, text="Stop", command=self.stop_script).grid(row=4, column=1, pady=10)

        self.frame_label = ttk.Label(frame)
        self.frame_label.grid(row=5, column=0, columnspan=2)

        stats_frame = ttk.LabelFrame(frame, text="Live Stats")
        stats_frame.grid(row=6, column=0, columnspan=2, pady=10, sticky="ew")

        self.stats_labels = {
            "people": tk.StringVar(value="0"),
            "hands": tk.StringVar(value="0"),
            "fps": tk.StringVar(value="0.0")
        }

        ttk.Label(stats_frame, text="People detected:").grid(row=0, column=0, sticky="w")
        ttk.Label(stats_frame, textvariable=self.stats_labels["people"]).grid(row=0, column=1, sticky="w")

        self.hands_row_label = ttk.Label(stats_frame, text="Hands raised:")
        self.hands_row_label.grid(row=1, column=0, sticky="w")
        self.hands_row_value = ttk.Label(stats_frame, textvariable=self.stats_labels["hands"])
        self.hands_row_value.grid(row=1, column=1, sticky="w")

        ttk.Label(stats_frame, text="FPS:").grid(row=2, column=0, sticky="w")
        ttk.Label(stats_frame, textvariable=self.stats_labels["fps"]).grid(row=2, column=1, sticky="w")

        self.toggle_stats_fields()

    def toggle_source_fields(self, *args):
        if self.source_type.get() == "Webcam":
            self.cam_entry.grid()
            self.rtsp_fields.grid_remove()
        else:
            self.cam_entry.grid_remove()
            self.rtsp_fields.grid()

    def toggle_stats_fields(self, *args):
        if self.script_choice.get() == "hand_voting_yolov11":
            self.hands_row_label.grid()
            self.hands_row_value.grid()
        else:
            self.hands_row_label.grid_remove()
            self.hands_row_value.grid_remove()

    def get_camera_source(self):
        if self.source_type.get() == "Webcam":
            return self.camera_index.get()
        else:
            ip = self.ip_address.get()
            port = self.port.get()
            user = self.username.get()
            pwd = self.password.get()
            return f"rtsp://{user}:{pwd}@{ip}:{port}/stream2"

    def start_script(self):
        if self.running:
            messagebox.showinfo("Info", "Script is already running.")
            return

        self.running = True
        self.frame_queue.queue.clear()
        self.stats_queue.queue.clear()

        camera_source = self.get_camera_source()
        script = self.script_choice.get()
        runner = run_osc_sender if script == "osc_sender_yolov11" else run_hand_voting

        self.worker_thread = threading.Thread(
            target=runner,
            args=(camera_source, self.frame_queue.put, self.stats_queue.put, lambda: self.running),
            daemon=True
        )
        self.worker_thread.start()

    def stop_script(self):
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
        self.clear_frame()

    def update_frame(self, frame):
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=img)
        self.frame_label.imgtk = imgtk
        self.frame_label.config(image=imgtk)

    def poll_queues(self):
        try:
            while True:
                frame = self.frame_queue.get_nowait()
                self.update_frame(frame)
        except queue.Empty:
            pass

        try:
            while True:
                stats = self.stats_queue.get_nowait()
                if isinstance(stats, dict):
                    if "people" in stats:
                        self.stats_labels["people"].set(str(stats["people"]))
                    if "hands" in stats:
                        self.stats_labels["hands"].set(str(stats["hands"]))
                    if "fps" in stats:
                        self.stats_labels["fps"].set(f"{stats['fps']:.2f}")
        except queue.Empty:
            pass

        self.root.after(30, self.poll_queues)

    def clear_frame(self):
        self.frame_label.config(image="")
        self.frame_label.imgtk = None

    def on_close(self):
        self.stop_script()
        self.root.destroy()


def main():
    root = tk.Tk()
    gui = MultiUserGUI(root)
    root.protocol("WM_DELETE_WINDOW", gui.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
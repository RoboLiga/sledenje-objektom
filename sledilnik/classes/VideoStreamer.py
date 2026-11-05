import threading
import time
import cv2


class VideoStreamer:
    """Fetches video from camera"""

    def __init__(self):
        self.ret = None
        self.frame = None
        self.timestamp = None
        self.video = None
        self.running = False
        self._new_frame = threading.Condition()
        self._frame_id = 0
        self._last_read_id = 0
        return

    def __del__(self):
        if self.video.isOpened():
            self.video.release()
        return

    def start(self, src):
        self.timestamp = time.time()
        # Initialize the video camera stream and read the first frame
        self.video = cv2.VideoCapture(src)
        if not self.video.isOpened():
            # Camera failed
            raise IOError("Couldn't open video file or webcam.")
        self.ret, self.frame = self.video.read()
        if not self.ret:
            self.video.release()
            raise IOError("Couldn't open video frame.")
        self._frame_id = 1
        self.running = True

        # Start the thread to read frames from the video stream
        t = threading.Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        try:
            # Keep looping infinitely until the stream is closed
            while self.running:
                #  Read the next frame from the stream (blocks until the camera delivers)
                ret, frame = self.video.read()
                with self._new_frame:
                    self.ret, self.frame = ret, frame
                    self.timestamp = time.time()
                    self._frame_id += 1
                    self._new_frame.notify_all()
        except:
            import traceback
            traceback.print_exc()
        finally:
            # If the thread indicator variable is set, stop the thread
            self.running = False
            # Wake any waiter so it can exit
            with self._new_frame:
                self._new_frame.notify_all()
            self.video.release()
        return

    def wait_for_frame(self, timeout=None):
        # Block until there is an unread frame. Returns False on timeout or stop
        with self._new_frame:
            self._new_frame.wait_for(
                lambda: self._frame_id != self._last_read_id or not self.running,
                timeout,
            )
            return self._frame_id != self._last_read_id

    def read(self):
        # Return the frame most recently read
        with self._new_frame:
            self._last_read_id = self._frame_id
            return self.frame, self.timestamp

    def stop(self):
        self.running = False
        if self.video.isOpened():
            self.video.release()
        return

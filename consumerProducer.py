#! /usr/bin/python3
import cv2, time
from threading import Thread, Semaphore, Lock


class Queue():
    def __init__(self):
        self.queue = []

        # two semaphores and a mutex to use per each queue
        self.empty = Semaphore(10)
        self.full = Semaphore(0)
        self.mutex = Lock()

    def put(self, frame):
        # acquiere first sempahore which would be realesed by another thread when consuming from the queue
        self.empty.acquire()
        self.mutex.acquire()
        self.queue.append(frame)
        self.mutex.release()
        self.full.release()
        return

    def get(self):
        # acquiere second Semaphore which would be realesed by another thread when producing to the queue
        self.full.acquire()
        self.mutex.acquire()
        frame = self.queue.pop(0)
        self.mutex.release()
        self.empty.release() # realese 1 permit that we use to add a frame to the first queue
        return frame


# create two queues for the frames
frameQueue = Queue()
grayQueue = Queue()


class ExtractFrames(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.videoCapture = cv2.VideoCapture('clip.mp4')
        # get total frames of the video
        self.totalFrames = int(self.videoCapture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.count = 0

    def run(self):
        # gets the first frame and a boolean value if frame extraccion is successful
        success, image = self.videoCapture.read()

        while True:
            # if frame extraccion is successful, and continues to extract the next frame
            if success:
                # get the frame
                frameQueue.put(image)
                # get next frame from file if the extraccion is successful
                success, image = self.videoCapture.read()
                print(f'Reading frame {self.count}')
                self.count = self.count + 1

            # once we reach the total frame count, we add -1 to signal the threads that there are no more frames
            if self.count == self.totalFrames:
                frameQueue.put(-1)
                break

        # signal to notify that thread has finished
        print('Frame extraction complete')
        return

class ConvertToGrayScale(Thread):
        def __init__(self):
            Thread.__init__(self)
            self.count = 0

        def run(self):

            while True:
                # get a frame from the first queue
                frame = frameQueue.get()

                # if we see the signal (-1) that there are no more frames, we exit the loop
                if type(frame) == int and frame == -1:
                    grayQueue.put(-1)
                    break

                # converts normal frame to grayscale and add it to the second queue
                grayscaleFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                grayQueue.put(grayscaleFrame)

                print(f'Converting Frame {self.count}')
                self.count = self.count + 1

            print('Convert to gray scale complete')
            return

class DisplayVideo(Thread):
    def __init__(self):
        Thread.__init__(self)

        self.delay = 42 #delay of 42 ms
        self.count = 0

    def run(self):
        while True:
            # get a grayscale frame
            frame = grayQueue.get()

            # if we see the signal (-1) that there are no more frames, we break the loop
            if type(frame) == int and frame == -1:
                break

            # video player window
            cv2.imshow('Video', frame)

            print(f'Displaying Frame {self.count}')
            self.count = self.count + 1

            # wait 42ms before displaying the next frame
            if cv2.waitKey(self.delay) and 0xFF == ord('q'):
                break

        cv2.destroyAllWindows()

        print('Display frames complete')
        return


extractFrames = ExtractFrames()
extractFrames.start()

convertFrames = ConvertToGrayScale()
convertFrames.start()

displayFrames = DisplayVideo()
displayFrames.start()

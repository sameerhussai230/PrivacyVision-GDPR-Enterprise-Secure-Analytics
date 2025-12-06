import time
import cv2
from kafka import KafkaProducer

# CONFIG
TOPIC_NAME = "cctv_raw_feed"
KAFKA_SERVER = "127.0.0.1:9092"
VIDEO_SOURCE = "test_video.mp4"

def start_camera():
    print(f"--- 🎥 Connecting Camera to {KAFKA_SERVER} ---")
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVER,
            max_request_size=10485760,
            retries=5
        )
    except Exception as e:
        print(f"❌ Kafka Error: {e}")
        return

    cap = cv2.VideoCapture(VIDEO_SOURCE)
    
    while True: # Infinite Loop for Demo
        if not cap.isOpened():
            cap = cv2.VideoCapture(VIDEO_SOURCE)
        
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("🔄 Replaying Video...")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            if ret:
                producer.send(TOPIC_NAME, buffer.tobytes())
                time.sleep(0.03) # ~30 FPS

if __name__ == "__main__":
    start_camera()
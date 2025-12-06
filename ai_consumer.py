import cv2
import numpy as np
import time
from kafka import KafkaConsumer
from ultralytics import YOLO
from db_manager import DatabaseHandler

# CONFIGURATION
TOPIC_NAME = "cctv_raw_feed"
KAFKA_SERVER = "127.0.0.1:9092"

# --- GATE COORDINATES ---
LINE_START_REL = (0.72, 1.0) 
LINE_END_REL   = (0.98, 0.55)

# --- ACCURACY SETTINGS ---
# The "Buffer Zone": You must pass the line by this many pixels to count.
# Increase this if people "hover" near the gate.
CROSSING_BUFFER = 30  

STATE_SWITCH_COOLDOWN = 3.0
HEAD_RATIO = 0.20
FACE_CONF = 0.15
BLUR_PADDING = 25

# DATA STORAGE
person_state = {}       
last_switch_time = {}   

# COUNTERS
total_entries = 0
total_exits = 0

def get_distance_from_line(px, py, line_start, line_end):
    """
    Calculates horizontal distance from the line at height py.
    Negative = Inside (Left), Positive = Outside (Right)
    """
    x1, y1 = line_start
    x2, y2 = line_end
    
    # Avoid division by zero
    if y2 - y1 == 0: return px - x1
    
    # Calculate where the line is (X) at this specific Y height
    line_x_at_py = x1 + (py - y1) * ((x2 - x1) / (y2 - y1))
    
    # Return difference (Distance in pixels)
    return px - line_x_at_py

def apply_heavy_blur(img, x1, y1, x2, y2):
    h, w = img.shape[:2]
    x1, y1 = max(0, int(x1)), max(0, int(y1))
    x2, y2 = min(w, int(x2)), min(h, int(y2))
    if x2 - x1 < 5 or y2 - y1 < 5: return
    try:
        roi = img[y1:y2, x1:x2]
        img[y1:y2, x1:x2] = cv2.GaussianBlur(roi, (99, 99), 30)
    except: pass

def start_smart_city_engine():
    global total_entries, total_exits, person_state, last_switch_time

    print(f"--- 🏙️ FINAL ENGINE: Precision Buffer Logic ---")

    db = DatabaseHandler()
    id_offset = db.get_last_max_id()
    print(f"🔄 Resuming IDs from: {id_offset + 1}")

    consumer = KafkaConsumer(TOPIC_NAME, bootstrap_servers=KAFKA_SERVER, auto_offset_reset='latest')
    
    body_model = YOLO("yolo11n.pt") 
    face_model = YOLO("yolov11n-face.pt") 

    for msg in consumer:
        nparr = np.frombuffer(msg.value, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None: continue

        h, w, _ = frame.shape
        
        # Line Coords
        line_start = (int(w * LINE_START_REL[0]), int(h * LINE_START_REL[1]))
        line_end   = (int(w * LINE_END_REL[0]),   int(h * LINE_END_REL[1]))

        # DRAW THE BUFFER ZONE (Visual Debugging)
        # We draw faint lines to show the "No Count" area
        cv2.line(frame, line_start, line_end, (0, 0, 255), 2) # Center Red Line
        cv2.putText(frame, "GATE", (line_end[0]-40, line_end[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)

        # 1. RUN AI MODELS
        face_results = face_model.track(frame, persist=True, conf=FACE_CONF, verbose=False, tracker="custom_tracker.yaml")
        body_results = body_model.track(frame, persist=True, classes=[0], verbose=False, tracker="custom_tracker.yaml")

        detected_faces = []
        if face_results[0].boxes.id is not None or face_results[0].boxes.xyxy is not None:
            boxes = face_results[0].boxes.xyxy.cpu()
            for box in boxes: detected_faces.append(box.numpy())

        # 2. MAIN LOGIC LOOP
        if body_results[0].boxes.id is not None:
            boxes = body_results[0].boxes.xyxy.cpu()
            raw_track_ids = body_results[0].boxes.id.int().cpu().tolist()

            for box, raw_id in zip(boxes, raw_track_ids):
                bx1, by1, bx2, by2 = map(int, box)
                real_track_id = raw_id + id_offset
                
                #  A. PRECISION COUNTING LOGIC 
                feet_x, feet_y = int((bx1 + bx2) / 2), by2
                
                # Get precise distance in pixels (+ is Right/Outside, - is Left/Inside)
                distance = get_distance_from_line(feet_x, feet_y, line_start, line_end)

                # Determine Zone based on Buffer
                current_zone_detection = None
                
                if distance < -CROSSING_BUFFER:
                    current_zone_detection = "INSIDE"
                elif distance > CROSSING_BUFFER:
                    current_zone_detection = "OUTSIDE"
                else:
                    # Person is IN THE BUFFER ZONE (Touching line)
                    # We treat this as "Unknown" or "Keep Previous State"
                    current_zone_detection = "BUFFER"

                # Init State
                if real_track_id not in person_state:
                    # Only assign state if they are clearly on one side
                    if current_zone_detection != "BUFFER":
                        person_state[real_track_id] = current_zone_detection
                        last_switch_time[real_track_id] = time.time()
                
                # Update State
                else:
                    known_state = person_state[real_track_id]
                    time_since_last = time.time() - last_switch_time.get(real_track_id, 0)

                    # Only process if they are NOT in the buffer zone
                    if current_zone_detection != "BUFFER" and current_zone_detection != known_state:
                        if time_since_last > STATE_SWITCH_COOLDOWN:
                            
                            # ENTRY (Must have cleared the buffer)
                            if known_state == "OUTSIDE" and current_zone_detection == "INSIDE":
                                total_entries += 1
                                cv2.line(frame, line_start, line_end, (0, 255, 0), 4) # Flash Green
                                db.log_event("ENTRY", real_track_id)
                            
                            # EXIT (Must have cleared the buffer)
                            elif known_state == "INSIDE" and current_zone_detection == "OUTSIDE":
                                total_exits += 1
                                cv2.line(frame, line_start, line_end, (0, 255, 255), 4) # Flash Yellow
                                db.log_event("EXIT", real_track_id)

                            # Commit Change
                            person_state[real_track_id] = current_zone_detection
                            last_switch_time[real_track_id] = time.time()

                # --- B. PRIVACY BLUR ---
                face_matched = False
                for fbox in detected_faces:
                    fx1, fy1, fx2, fy2 = map(int, fbox)
                    f_cx, f_cy = (fx1 + fx2) / 2, (fy1 + fy2) / 2
                    if bx1 < f_cx < bx2 and by1 < f_cy < by2:
                        apply_heavy_blur(frame, fx1 - BLUR_PADDING, fy1 - BLUR_PADDING, 
                                                fx2 + BLUR_PADDING, fy2 + BLUR_PADDING)
                        face_matched = True

                if not face_matched:
                    head_h = int((by2 - by1) * HEAD_RATIO)
                    apply_heavy_blur(frame, bx1, by1, bx2, by1 + head_h)

                # Visualization
                color = (0, 255, 0) if person_state.get(real_track_id) == "INSIDE" else (0, 165, 255)
                # If in buffer, show Grey color
                if current_zone_detection == "BUFFER": color = (200, 200, 200)

                cv2.rectangle(frame, (bx1, by1), (bx2, by2), color, 2)
                cv2.putText(frame, f"ID:{real_track_id}", (bx1, by1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        cv2.rectangle(frame, (0, 0), (250, 90), (0, 0, 0), -1)
        cv2.putText(frame, f"Entries: {total_entries}", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, f"Exits:   {total_exits}", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        cv2.imshow("PrivacyVision - Precision Mode", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_smart_city_engine()
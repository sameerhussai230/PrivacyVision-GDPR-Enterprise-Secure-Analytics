
***
# PrivacyVision-GDPR: Enterprise Secure Analytics

**Real-Time, Privacy-Preserving Computer Vision Pipeline powered by YOLO11 & Kafka.**

![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![YOLO11](https://img.shields.io/badge/AI-YOLO11-magenta) ![Kafka](https://img.shields.io/badge/Engineering-Apache%20Kafka-red) ![Docker](https://img.shields.io/badge/Infrastructure-Docker-blue) 
![License](https://img.shields.io/badge/License-GPLv3-green)

## 📖 Overview
**PrivacyVision** is a scalable, end-to-end computer vision architecture designed for Smart Cities, Construction Sites, and High-Security Zones. It addresses the critical gap between **Operational Analytics** and **Privacy Compliance (GDPR/CCPA)**.

The system processes video feeds in real-time to generate precise event analytics (Zone Entry/Exit, Occupancy) while automatically anonymizing individuals using a "Zero-Trust" hybrid tracking engine. Built on **Apache Kafka**, it decouples video ingestion from processing, allowing it to scale from a single camera to a city-wide network.

---

## 🎥 System Demonstration

![Demo GIF](demo_video.gif)

### 2. Privacy Mode Comparisons

<!-- ORIGINAL VIDEO (Full Width / Large) -->
<h4 align="center">Original Input (Raw Footage)</h4>
<div align="center">
  <img src="https://github.com/sameerhussai230/PrivacyVision-GDPR-Enterprise-Secure-Analytics/releases/download/assests/test_video_original.gif" width="80%">
</div>

<br>

<!-- COMPARISON (2 Columns / Medium) -->
| **Mode A: Face Blur** | **Mode B: Body Blur** |
| :---: | :---: |
| <img src="https://github.com/sameerhussai230/PrivacyVision-GDPR-Enterprise-Secure-Analytics/releases/download/assests/privacy_vision_demo_face.gif" width="100%"> | <img src="https://github.com/sameerhussai230/PrivacyVision-GDPR-Enterprise-Secure-Analytics/releases/download/assests/privacy_vision_demo_body.gif" width="100%"> |


**System In Action:**
1.  **Ingestion:** Raw video is streamed via Kafka.
2.  **Processing:** The AI tracks individuals, blurring faces/heads dynamically while counting zone crossings.
3.  **Visualization:** A live Streamlit dashboard reports Key Performance Indicators (KPIs) stored in PostgreSQL.

## 📸 Dashboard Screenshot

![Dashboard Screenshot](https://github.com/sameerhussai230/PrivacyVision-GDPR-Enterprise-Secure-Analytics/raw/main/dashboard.png)

---

## 🏗️ Architecture Diagram

<img src="https://raw.githubusercontent.com/sameerhussai230/PrivacyVision-GDPR-Enterprise_Secure_Analytics/main/PrivacyVision_GDPR.svg" width="100%" />


---

## 🚀 Key Features
*   **GDPR "Zero-Trust" Privacy:** Implements a configurable hybrid protection layer.
    *   **Face Privacy:** Detects and blurs faces; includes specific logic to calculate head geometry based on body pose if the face is occluded (looking away).
    *   **Body Privacy:** Offers a **Full Body Blur** mode to completely mask individuals for high-security or strict anonymity environments.
*   **Hysteresis Counting (Precision Logic):** Utilizes a **Buffer Zone (+/- 30px)** technique. An object is only counted when it definitively clears the threshold, eliminating false positives from loitering or jitter.
*   **Stateful Tracking:** Leverages **ByteTrack** with a custom 4-second memory buffer (`track_buffer: 120`) to maintain identity continuity across temporary occlusions.
*   **Enterprise Persistence:** Events are logged with unique Tracker IDs to **PostgreSQL**, enabling historical analysis and audit trails.
*   **Fault Tolerant:** Includes auto-recovery mechanisms for Kafka connections and video stream interruptions.

---

## 🛠️ Technology Stack
| Layer | Technology | Role |
| :--- | :--- | :--- |
| **Model** | **YOLO11** (Ultralytics) | Object Detection & Segmentation |
| **Tracking** | **ByteTrack** | Persistent Multi-Object Tracking (MOT) |
| **Streaming** | **Apache Kafka** | High-throughput, low-latency messaging |
| **Database** | **PostgreSQL** | Structured Event Logging |
| **Container** | **Docker Compose** | Infrastructure Orchestration |
| **Frontend** | **Streamlit** | Real-time Business Intelligence |

---

## 🧠 Core Techniques

### 1. Ingestion Pipeline
*   **Bandwidth Optimization:** Frames are serialized and compressed (JPEG Q=70) before transmission, reducing network load by ~90% compared to raw bitmaps.
*   **Async Buffering:** The producer decouples camera framerate from AI processing speed, preventing bottlenecks.

### 2. AI Processing Pipeline
*   **Hybrid Anonymization:**
    *   *Primary:* Face Detection confidence threshold at 0.15 (High Sensitivity).
    *   *Fallback:* "Head Ratio" calculation (Top 20% of Body Bounding Box) applied when Face AI returns null.
*   **Linear Algebra Logic:** Calculates the precise pixel distance of a subject's feet relative to the vector of the entry gate to determine state (Inside/Outside/Buffer).

### 3. Data Pipeline
*   **ID Offset Strategy:** On startup, the engine queries `MAX(id)` from the database to offset current tracking IDs, ensuring unique identifiers across system restarts.
*   **Smart Polling:** The dashboard uses a lightweight "Row Count Check" every 0.5s, only fetching heavy datasets when new events are committed to the DB.

---

## 🔮 Improvements & Scalability

### Hardware Acceleration (GPU)
Currently, this demo uses the **YOLO11 Nano (`yolo11n.pt`)** model optimized for CPU.
*   **Performance:** Running this on an NVIDIA GPU (CUDA) allows upgrading to **YOLO11 Large (`yolo11l.pt`)** or **Extra-Large (`yolo11x.pt`)**.
*   **Impact:** This dramatically increases accuracy for small faces, blurry motion, and long-distance detection, ensuring 99.9% anonymization coverage even in 4K streams.

### Flexible Deployment (Docker/Cloud)
The current `docker-compose` setup can be deployed to AWS/Azure/GCP. The Kafka architecture allows multiple "AI Consumer" containers to run in parallel, processing hundreds of camera feeds simultaneously.

---

## 🌍 Industry Use Cases (Beyond Retail)

The tech stack is modular. By changing the Model Weights and Logic Rules, this system adapts to various industries:

### 1. Construction & Insurance (Safety Compliance)
*   **Goal:** Automated PPE Monitoring.
*   **Change:** Swap `yolo11n.pt` for a custom-trained model detecting **Helmets** and **Safety Vests**.
*   **Logic:** Flag workers inside the "Construction Zone" (Geofence) without gear. This reduces insurance premiums and prevents accidents.

### 2. Full Body Anonymization (High Security)
*   **Goal:** Complete identity protection for sensitive environments (Hospitals, Schools).
*   **Change:** Switch the blur logic from `face_box` to `body_box`.
*   **Logic:** Apply Gaussian blur to the entire detected person, preserving only movement data (flow/occupancy) without revealing gender, clothing, or identity.

### 3. Smart Traffic Management
*   **Goal:** Urban Planning.
*   **Change:** Detect classes `Car`, `Bus`, `Truck` instead of `Person`.
*   **Logic:** Count vehicle throughput on specific lanes to optimize traffic light timing.

---

## ⚡ Setup and Running

### 1. Prerequisites
*   **Docker Desktop** (Running)
*   **Python 3.9+**
*   **Git**

### 2. Installation
```bash
# Clone the repo
git clone https://github.com/sameerhussai230/PrivacyVision-GDPR-Enterprise-Secure-Analytics.git
cd PrivacyVision-GDPR-Enterprise_Secure_Analytics

# Install dependencies
pip install -r requirements.txt
```

### 3. Add Media
Place your CCTV video file in the root folder and name it:
`test_video.mp4`

### 4. Running the Project
Use the **One-Click Orchestrator** to launch the Infrastructure, Database, AI, and Dashboard simultaneously.

```bash
python main.py
```

*The script will:*
1.  *Verify Docker status.*
2.  *Launch the AI Processing Unit.*
3.  *Start the Analytics Dashboard.*
4.  *Begin the Video Stream.*

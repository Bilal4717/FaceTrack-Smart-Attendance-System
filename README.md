# FaceTrack: Smart Attendance System 🚀

**FaceTrack** is a high-performance, cloud-integrated attendance management solution that leverages **Facial Recognition (AI)** and **Liveness Detection** to automate classroom tracking. Built with a focus on Software Engineering principles, it provides a seamless experience for Administrators, Teachers, and Students.

---

## 🌟 Key Features

### 🔐 Security & AI
* **Facial Recognition:** Utilizes the LBPH (Local Binary Patterns Histograms) algorithm for high-speed, local face matching.
* **Liveness Detection:** Implements a "Blink Check" verification to prevent proxy attendance via photos or videos.
* **Enrollment Validation:** Automatically rejects students not registered for a specific course during marking.

### 📊 Administrative Oversight
* **Role-Based Access Control (RBAC):** Distinct portals for Admin, Teacher, and Student roles.
* **Session-Based Management:** Attendance is linked to specific class sessions rather than just dates.
* **Management Information System (MIS):** Admin tools to register Teachers, create Courses, and assign Students.

### 📈 Data & Analytics
* **Cloud Persistence:** Real-time synchronization with Google Firebase Cloud Firestore.
* **Interactive Analytics:** Visualizes attendance trends using Chart.js line graphs.
* **Progress Tracking:** Students view personal attendance percentages and session-by-session history.

---

## 🛠️ Tech Stack

* **Frontend:** HTML5, CSS3 (Glassmorphism UI), Bootstrap 5, Jinja2.
* **Backend:** Python 3.10+, Flask (Web Framework).
* **AI/Vision:** OpenCV, LBPH Face Recognizer.
* **Database:** Google Firebase Cloud Firestore (NoSQL).

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10 or higher.
* A Firebase Project with a `ServiceAccount.json` key.
* `haarcascade_frontalface_default.xml` and `haarcascade_eye.xml` in the root folder.

### Installation
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/yourusername/FaceTrack.git](https://github.com/yourusername/FaceTrack.git)
    cd FaceTrack
    ```
2.  **Install dependencies:**
    ```bash
    pip install flask firebase-admin opencv-python numpy Pillow
    ```
3.  **Setup Database:**
    Place your `ServiceAccount.json` in the root directory.
4.  **Run the Application:**
    ```bash
    python app.py
    ```

---

## 📐 System Architecture

FaceTrack follows a **Client-Server Architecture**. The Flask backend handles the business logic and AI processing, while Firebase Firestore acts as the real-time data layer.



---

## 👥 Contributors
* Muhammad Bilal Shaikh- Lead Developer & AI Integration.

---

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

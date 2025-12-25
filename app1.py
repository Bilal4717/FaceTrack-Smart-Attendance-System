import os, cv2, numpy as np, firebase_admin
from flask import Flask, render_template, Response, request, redirect, url_for, session, flash
from firebase_admin import credentials, firestore
from datetime import datetime
from PIL import Image

app = Flask(__name__)
app.secret_key = "full_system_se_project_2025"

if not firebase_admin._apps:
    cred = credentials.Certificate("ServiceAccount.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

TRAINER_PATH = 'trainer/trainer.yml'
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
eye_cascade = cv2.CascadeClassifier("haarcascade_eye.xml") # NEW: For Liveness

def get_recognizer():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    if os.path.exists(TRAINER_PATH):
        recognizer.read(TRAINER_PATH)
    return recognizer
@app.route('/start_session/<course_id>')
def start_session(course_id):
    # Create a unique session for this specific class occurrence
    session_ref = db.collection('sessions').add({
        'course_id': course_id,
        'date': datetime.now().strftime("%Y-%m-%d"),
        'start_time': firestore.SERVER_TIMESTAMP,
        'status': 'active',
        'teacher_id': session['user_id']
    })
    session_id = session_ref[1].id
    return redirect(url_for('mark_session', session_id=session_id, course_id=course_id))

@app.route('/course_analytics/<course_id>')
def course_analytics(course_id):

    sessions_ref = db.collection('sessions').where('course_id', '==', course_id).where('status', '==', 'completed').stream()
    
    labels = []
    values = []
    
    for sess in sessions_ref:
        s_id = sess.id
        s_data = sess.to_dict()
        labels.append(s_data['date'])
        # Count attendance
        att_count = len(list(db.collection('attendance').where('session_id', '==', s_id).stream()))
        values.append(att_count)

    return render_template('analytics.html', labels=labels, values=values, course_id=course_id)


@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    u = request.form.get('username').strip()
    p = request.form.get('password').strip()
    
    query = db.collection('users').where('username', '==', u).stream()
    
    user_data = None
    for doc in query:
        temp = doc.to_dict()
        if str(temp.get('password')) == str(p):
            user_data = temp
            user_data['id'] = doc.id
            break

    if user_data:
        session['user_id'] = user_data['id']
        session['role'] = user_data['role']
        session['name'] = user_data['username']
        
        flash(f"Welcome {session['name']}!", "success")
        if user_data['role'] == 'admin': return redirect(url_for('admin_dash'))
        if user_data['role'] == 'teacher': return redirect(url_for('teacher_dash'))
        return redirect(url_for('student_dash'))
    
    flash("Invalid Credentials", "danger")
    return redirect(url_for('login_page'))

#Admin Dashboard
@app.route('/admin_dash')
def admin_dash():
    
    students_ref = db.collection('users').where('role', '==', 'student').stream()
    all_students = [{'id': doc.id, 'name': doc.to_dict().get('username')} for doc in students_ref]
    
 
    courses_ref = db.collection('courses').stream()
    all_courses = [{'id': doc.id, 'name': doc.to_dict().get('name')} for doc in courses_ref]
    
    
    teachers = [d.to_dict() for d in db.collection('users').where('role', '==', 'teacher').stream()]
    attendance = [d.to_dict() for d in db.collection('attendance').limit(20).stream()]
    
    return render_template('admin.html', 
                           student_list=all_students, 
                           course_list=all_courses, 
                           teachers=teachers, 
                           attendance=attendance)


@app.route('/register_student', methods=['POST'])
def register_student():
    sid = request.form.get('id').strip()
    name = request.form.get('username').strip()
    email = request.form.get('email').strip()
    pwd = request.form.get('password').strip()

   
    db.collection('users').document(sid).set({
        'username': name,
        'password': pwd,
        'email': email,
        'role': 'student'
    })
    flash(f"Student {name} registered in system! Now you can assign them to a course.", "success")
    return redirect(url_for('admin_dash'))


@app.route('/assign_student', methods=['POST'])
def assign_student():
    sid = request.form.get('student_id')
    cid = request.form.get('course_id')
    
    
    db.collection('courses').document(cid).update({
        'students': firestore.ArrayUnion([sid])
    })
    
    
    return render_template('capture.html', student_id=sid)

@app.route('/capture_face/<sid>')
def capture_face(sid):
    cam = cv2.VideoCapture(0)
    detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    count = 0
    
    if not os.path.exists('dataset'): 
        os.makedirs('dataset')

    while True:
        ret, img = cam.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)

        for (x,y,w,h) in faces:
            count += 1
        
            cv2.imwrite(f"dataset/User.{sid}.{count}.jpg", gray[y:y+h,x:x+w])
            cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 2)
            cv2.putText(img, f"Captured: {count}/50", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
            cv2.imshow('Capturing Face Data - Keep looking at the camera', img)

        if cv2.waitKey(1) & 0xFF == ord('q') or count >= 50:
            break

    cam.release()
    cv2.destroyAllWindows()
    
    return redirect(url_for('train_model'))

@app.route('/train')
def train_model():
    path = 'dataset'
    if not os.path.exists(path) or len(os.listdir(path)) == 0:
        flash("No face data found in dataset folder!", "danger")
        return redirect(url_for('admin_dash'))

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

    imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
    faceSamples = []
    ids = []

    for imagePath in imagePaths:
        PIL_img = Image.open(imagePath).convert('L')
        img_numpy = np.array(PIL_img, 'uint8')

        try:
            id = int(os.path.split(imagePath)[-1].split(".")[1])
            faces = detector.detectMultiScale(img_numpy)
            for (x, y, w, h) in faces:
                faceSamples.append(img_numpy[y:y+h, x:x+w])
                ids.append(id)
        except Exception as e:
            print(f"Skipping file {imagePath} due to error: {e}")
            continue

    if len(faceSamples) > 0:
        recognizer.train(faceSamples, np.array(ids))
        if not os.path.exists('trainer'):
            os.makedirs('trainer')
        recognizer.save('trainer/trainer.yml')
        
        
        flash("Model Training Complete! Student is now recognizable.", "success")
    else:
        flash("Training failed: No faces detected in the images.", "warning")

    return redirect(url_for('admin_dash'))

@app.route('/add_teacher', methods=['POST'])
def add_teacher():
    u = request.form.get('username')
    p = request.form.get('password')
    e = request.form.get('email')
    db.collection('users').add({
        'username': u, 'password': p, 'role': 'teacher', 'email': e
    })
    flash(f"Teacher {u} added!", "success")
    return redirect(url_for('admin_dash'))
@app.route('/add_course', methods=['POST'])
def add_course():
    c_id = request.form.get('course_id').strip().upper()
    c_name = request.form.get('course_name').strip()
    
    db.collection('courses').document(c_id).set({
        'name': c_name,
        'teacher_id': None,
        'students': []
    })
    flash(f"Course {c_name} created!", "success")
    return redirect(url_for('admin_dash'))

@app.route('/assign_teacher', methods=['POST'])
def assign_teacher():
    tid = request.form.get('teacher_id')
    cid = request.form.get('course_id')
    
    db.collection('courses').document(cid).update({
        'teacher_id': tid
    })
    flash("Teacher assigned to course successfully!", "success")
    return redirect(url_for('admin_dash'))

#TEACHER DASHBOARD
@app.route('/teacher_dash')
def teacher_dash():
    
    courses_ref = db.collection('courses').where('teacher_id', '==', session['user_id']).stream()
    my_courses = [doc.to_dict() | {'id': doc.id} for doc in courses_ref]
    return render_template('teacher.html', courses=my_courses)

@app.route('/add_student_to_db', methods=['POST'])
def add_student_to_db():
    sid = request.form.get('id')
    name = request.form.get('name')
    email = request.form.get('email')
    db.collection('users').document(sid).set({
        'username': name, 'password': '123', 'role': 'student', 'email': email
    })
    flash(f"Student {name} added to system!", "success")
    return redirect(url_for('teacher_dash'))

@app.route('/attendance_log/<course_id>')
def attendance_log(course_id):
    logs = db.collection('attendance').where('course_id', '==', course_id).stream()
    records = [doc.to_dict() for doc in logs]
    return render_template('log.html', records=records, course_id=course_id)
@app.route('/video_feed/<session_id>/<course_id>')
def mark_session(session_id, course_id):
    cam = cv2.VideoCapture(0)
    rec = get_recognizer()
    
    course_doc = db.collection('courses').document(course_id).get()
    if not course_doc.exists:
        flash("Course not found!", "danger")
        return redirect(url_for('teacher_dash'))
    
    enrolled_students = course_doc.to_dict().get('students', [])
    
    while True:
        ret, frame = cam.read()
        if not ret: break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)
        
        trigger_prompt = False
        display_msg = ""
        msg_type = "info"

        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            Id, conf = rec.predict(roi_gray)
            
            if conf < 70:
                if str(Id) in enrolled_students:
                    stu_doc = db.collection('users').document(str(Id)).get()
                    name = stu_doc.to_dict().get('username') if stu_doc.exists else "Unknown"
                    
                
                    date_today = datetime.now().strftime("%Y-%m-%d")
                    db.collection('attendance').document(f"{Id}_{session_id}").set({
                        'student_id': str(Id), 'course_id': course_id, 'session_id': session_id,
                        'date': date_today, 'status': 1, 'timestamp': firestore.SERVER_TIMESTAMP
                    })
                    
                    display_msg = f"Attendance marked for {name}."
                    trigger_prompt = True
                    msg_type = "success"
                else:
                    #UNREGISTERED CASE
                    display_msg = f"ID {Id} is NOT registered for this course!"
                    trigger_prompt = True
                    msg_type = "error"
                
                color = (0,255,0) if msg_type == "success" else (0,0,255)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                break 

        if trigger_prompt:
            cv2.imshow("Validation Result", frame)
            cv2.waitKey(1000)
            cam.release()
            cv2.destroyAllWindows()
            
            import ctypes
            title = "Success" if msg_type == "success" else "Enrollment Error"
            full_prompt = f"{display_msg}\n\nWould you like to mark another student?"
            
            res = ctypes.windll.user32.MessageBoxW(0, full_prompt, title, 4)
            
            if res == 6:
                return redirect(url_for('mark_session', session_id=session_id, course_id=course_id))
            else: 
            
                db.collection('sessions').document(session_id).update({'status': 'completed'})
              
                return redirect(url_for('session_summary', session_id=session_id))

        cv2.imshow("Marking Attendance - ESC to Close", frame)
        if cv2.waitKey(1) == 27: break

    cam.release()
    cv2.destroyAllWindows()
    return redirect(url_for('teacher_dash'))

@app.route('/session_summary/<session_id>')
def session_summary(session_id):

    sess_doc = db.collection('sessions').document(session_id).get()
    if not sess_doc.exists:
        return redirect(url_for('teacher_dash'))
    
    sess_data = sess_doc.to_dict()
    
    attendance_ref = db.collection('attendance').where('session_id', '==', session_id).stream()
    
    present_students = []
    for log in attendance_ref:
        sid = log.to_dict().get('student_id')
        stu_doc = db.collection('users').document(sid).get()
        if stu_doc.exists:
            present_students.append(stu_doc.to_dict().get('username'))
            
    return render_template('session_summary.html', 
                           course_id=sess_data['course_id'], 
                           date=sess_data['date'], 
                           students=present_students)

# STUDENT DASHBOARD
@app.route('/student_dash')
def student_dash():
    student_id = session.get('user_id')
    courses = db.collection('courses').where('students', 'array_contains', student_id).stream()
    
    course_list = []
    for doc in courses:
        c_id = doc.id
        c_data = doc.to_dict()
        
        sessions = db.collection('sessions').where('course_id', '==', c_id).where('status', '==', 'completed').stream()
        
        history = []
        present_count = 0
        total_sessions = 0
        
        for sess in sessions:
            total_sessions += 1
            s_id = sess.id
            s_data = sess.to_dict()
            att_check = db.collection('attendance').document(f"{student_id}_{s_id}").get()
            is_present = att_check.exists
            if is_present: present_count += 1
            
            history.append({'date': s_data['date'], 'status': 'Present' if is_present else 'Absent'})

        perc = (present_count / total_sessions * 100) if total_sessions > 0 else 0
        course_list.append({
            'name': c_data['name'],
            'perc': round(perc, 1),
            'history': history,
            'color': 'success' if perc >= 80 else 'danger'
        })
        
    total_perc = sum([c['perc'] for c in course_list])
    avg_perc = round(total_perc / len(course_list), 1) if course_list else 0
    
    return render_template('student.html', courses=course_list, avg_attendance=avg_perc)

@app.route('/alert_system')
def alert_system():
    at_risk = []
    sessions_ref = db.collection('sessions').where('status', '==', 'completed').stream()
    course_totals = {}
    for s in sessions_ref:
        cid = s.to_dict().get('course_id')
        course_totals[cid] = course_totals.get(cid, 0) + 1

    students = db.collection('users').where('role', '==', 'student').stream()
    for s_doc in students:
        sid = s_doc.id
        s_data = s_doc.to_dict()
        
        courses = db.collection('courses').where('students', 'array_contains', sid).stream()
        for c_doc in courses:
            cid = c_doc.id
            c_name = c_doc.to_dict().get('name')
            total_classes = course_totals.get(cid, 0)
            
            if total_classes > 0:
                presence = len(list(db.collection('attendance').where('session_id', '!=', '').where('student_id', '==', sid).where('course_id', '==', cid).stream()))
                perc = (presence / total_classes) * 100
                
                if perc < 80:
                    at_risk.append({
                        'id': sid, 'name': s_data['username'], 'email': s_data['email'],
                        'course': c_name, 'percentage': round(perc, 1)
                    })
    
    return render_template('alert.html', at_risk=at_risk)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)
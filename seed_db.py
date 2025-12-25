import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate("ServiceAccount.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def seed_data():
    print("Starting Database Seeding...")

    # 1. Create Admin
    db.collection('users').document('admin_user').set({
        'username': 'Admin',
        'password': '123',
        'role': 'admin',
        'email': 'admin@system.edu'
    })

    # 2. Create Teachers
    teachers = [
        {'id': 'T1', 'name': 'Dr. Smith', 'pass': 'smith123', 'email': 'smith@system.edu'},
        {'id': 'T2', 'name': 'Prof. Johnson', 'pass': 'john123', 'email': 'johnson@system.edu'},
        {'id': 'T3', 'name': 'Ms. Davis', 'pass': 'davis123', 'email': 'davis@system.edu'}
    ]

    for t in teachers:
        db.collection('users').document(t['id']).set({
            'username': t['name'],
            'password': t['pass'],
            'role': 'teacher',
            'email': t['email']
        })

    # 3. Create Courses & Assign Teachers
    # Note: In Firestore, we store the teacher_id to create a relationship
    courses = [
        {'id': 'CS101', 'name': 'Intro to AI', 'teacher_id': 'T1', 'class': 'Section-A'},
        {'id': 'CS102', 'name': 'Software Engineering', 'teacher_id': 'T2', 'class': 'Section-B'},
        {'id': 'CS103', 'name': 'Database Systems', 'teacher_id': 'T3', 'class': 'Section-A'}
    ]

    for c in courses:
        db.collection('courses').document(c['id']).set(c)

    # 4. Create Students (Pre-added 2 for testing)
    students = [
        {'id': '101', 'name': 'Alice', 'pass': 'alice123', 'role': 'student', 'class': 'Section-A'},
        {'id': '102', 'name': 'Bob', 'pass': 'bob123', 'role': 'student', 'class': 'Section-B'}
    ]

    for s in students:
        db.collection('users').document(s['id']).set(s)

    print("Seeding Complete! Admin, 3 Teachers, 3 Courses, and Students created.")

if __name__ == "__main__":
    seed_data()
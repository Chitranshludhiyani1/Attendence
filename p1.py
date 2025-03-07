import cv2
import tkinter as tk
from tkinter import messagebox, simpledialog
from tkcalendar import Calendar, DateEntry
from PIL import Image, ImageTk
import csv
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from tkinter import ttk

class FaceAttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Detection Attendance System")
        self.video_stream = None
        self.running = False
        self.students = {}

        self.load_students()

        self.label = tk.Label(root, bg='#2c3e50')
        self.label.pack(padx=20, pady=20)

        self.start_button = tk.Button(root, text="Start Attendance", command=self.start_attendance, bg="#27ae60", fg="white", font=("Helvetica", 12, "bold"), padx=10, pady=5)
        self.start_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.stop_button = tk.Button(root, text="Stop Attendance", command=self.stop_attendance, bg="#c0392b", fg="white", font=("Helvetica", 12, "bold"), padx=10, pady=5)
        self.stop_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.add_student_button = tk.Button(root, text="Add Student", command=self.add_student, bg="#2980b9", fg="white", font=("Helvetica", 12, "bold"), padx=10, pady=5)
        self.add_student_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.view_attendance_button = tk.Button(root, text="View Attendance", command=self.view_attendance, bg="#8e44ad", fg="white", font=("Helvetica", 12, "bold"), padx=10, pady=5)
        self.view_attendance_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.search_attendance_button = tk.Button(root, text="Search Attendance", command=self.search_attendance, bg="#d35400", fg="white", font=("Helvetica", 12, "bold"), padx=10, pady=5)
        self.search_attendance_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.status_label = tk.Label(root, text="", bg='#34495e', fg="white", font=("Helvetica", 12, "bold"))
        self.status_label.pack(pady=10)

        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def load_students(self):
        if os.path.exists("students.csv"):
            with open("students.csv", "r") as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) == 4:
                        self.students[row[0]] = {'name': row[1], 'email': row[2], 'photo': row[3].split('|')}

    def save_student(self, student_id, student_name, student_email, student_photos):
        with open("students.csv", "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([student_id, student_name, student_email, '|'.join(student_photos)])

    def add_student(self):
        student_id = simpledialog.askstring("Input", "Enter Student ID:")
        student_name = simpledialog.askstring("Input", "Enter Student Name:")
        student_email = simpledialog.askstring("Input", "Enter Student Email:")

        if student_id and student_name and student_email:
            cap = cv2.VideoCapture(0)
            messagebox.showinfo("Capture", "Press 's' to capture a photo. Press 'q' to finish.")

            photos = []
            os.makedirs("photos", exist_ok=True)

            while True:
                ret, frame = cap.read()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

                cv2.imshow("Capture Student Photos", frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('s'):
                    photo_path = f"photos/{student_id}_{len(photos)+1}.jpg"
                    cv2.imwrite(photo_path, frame)
                    photos.append(photo_path)
                    messagebox.showinfo("Captured", f"Captured photo {len(photos)}")
                elif key == ord('q'):
                    break

            cap.release()
            cv2.destroyAllWindows()

            self.students[student_id] = {'name': student_name, 'email': student_email, 'photo': photos}
            self.save_student(student_id, student_name, student_email, photos)
            messagebox.showinfo("Success", f"Student {student_name} added with {len(photos)} photos!")

    def mark_attendance(self, student_id):
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"attendance_{date_str}.csv"
        already_marked = set()

        if os.path.exists(filename):
            with open(filename, "r") as file:
                reader = csv.reader(file)
                for row in reader:
                    already_marked.add(row[0])

        if student_id not in already_marked:
            with open(filename, "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([student_id, self.students[student_id]['name'], datetime.now().strftime("%H:%M:%S")])
            self.status_label.config(text=f"Marked Present: {self.students[student_id]['name']}")
            messagebox.showinfo("Attendance Marked", f"{self.students[student_id]['name']} marked present.")

    def start_attendance(self):
        if not self.running:
            self.running = True
            self.video_stream = cv2.VideoCapture(0)
            self.update_frame()

    def stop_attendance(self):
        if self.running:
            self.running = False
            self.video_stream.release()
            self.label.config(image='')
            self.send_absent_alerts()

    def update_frame(self):
        if self.running:
            ret, frame = self.video_stream.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                    # Here you would compare detected faces with stored student photos using face recognition
                    # For now, we'll assume any detected face is a student and mark attendance

                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img)
                imgtk = ImageTk.PhotoImage(image=img)
                self.label.imgtk = imgtk
                self.label.configure(image=imgtk)

            self.root.after(10, self.update_frame)

    def view_attendance(self):
        cal_window = tk.Toplevel(self.root)
        cal_window.title("Select Date")
        cal = Calendar(cal_window, selectmode='day')
        cal.pack(pady=20)

        def show_attendance():
            date_str = cal.get_date()
            filename = f"attendance_{date_str}.csv"

            if os.path.exists(filename):
                with open(filename, "r") as file:
                    data = file.read()
                messagebox.showinfo("Attendance", data)
            else:
                messagebox.showwarning("Not Found", f"No attendance record found for {date_str}")

            cal_window.destroy()

        tk.Button(cal_window, text="View Attendance", command=show_attendance, bg="#27ae60", fg="white", font=("Helvetica", 12, "bold"), padx=10, pady=5).pack(pady=10)

    def search_attendance(self):
        search_window = tk.Toplevel(self.root)
        search_window.title("Search Attendance")

        tk.Label(search_window, text="Enter Student ID or Name:").pack(pady=5)
        search_entry = tk.Entry(search_window)
        search_entry.pack(pady=5)

        def search():
            query = search_entry.get().strip()
            results = []

            for file in os.listdir('.'):
                if file.startswith("attendance_") and file.endswith(".csv"):
                    with open(file, "r") as f:
                        reader = csv.reader(f)
                        for row in reader:
                            if query.lower() in row[0].lower() or query.lower() in row[1].lower():
                                results.append((file, row))

            if results:
                result_text = "\n".join([f"{file}: {row}" for file, row in results])
                messagebox.showinfo("Search Results", result_text)
            else:
                messagebox.showinfo("No Results", "No matching attendance records found.")

        tk.Button(search_window, text="Search", command=search, bg="#27ae60", fg="white", font=("Helvetica", 12, "bold"), padx=10, pady=5).pack(pady=10)

    def send_absent_alerts(self):
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"attendance_{date_str}.csv"
        marked_students = set()

        if os.path.exists(filename):
            with open(filename, "r") as file:
                reader = csv.reader(file)
                for row in reader:
                    marked_students.add(row[0])

        absent_students = [sid for sid in self.students if sid not in marked_students]

        for student_id in absent_students:
            self.send_email_alert(self.students[student_id]['name'], self.students[student_id]['email'])

    def send_email_alert(self, student_name, student_email):
        sender_email = "your_email@example.com"
        sender_password = "your_password"

        message = MIMEMultipart("alternative")
        message["Subject"] = "Attendance Alert"
        message["From"] = sender_email
        message["To"] = student_email

        text = f"Dear {student_name},\n\nYou were marked absent today. Please ensure your attendance in future classes.\n\nRegards,\nAttendance System"
        part = MIMEText(text, "plain")
        message.attach(part)

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, student_email, message.as_string())
            print(f"Email sent to {student_name}")
        except Exception as e:
            print(f"Failed to send email to {student_name}: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg='#34495e')
    app = FaceAttendanceApp(root)
    root.mainloop()

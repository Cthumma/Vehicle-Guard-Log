
from tkinter import ttk
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
import csv
import os
import win32api
import win32print
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageTk
import speech_recognition as sr
import cv2
import threading


USERS_FILE = "users.csv"
LOG_FILE = "vehicle_log.csv"
SNAPSHOT_DIR = "snapshots"
# The format should be like this: rtsp://<username>:<password>@<ip_address>:<port>/<path>
# The code is implemented with HIKVISION Camera
FRONT_RTSP = ""
BACK_RTSP = ""

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows([["username", "password"], ["guard1", "1234"]])
# Create an excel file for logging data
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([
            "License Plate", "Username", "Entry Time", "Type", 
            "Other Detail", "Barcode ID", "Exit Time", 
            "Front Snapshot", "Back Snapshot", "House No."
        ])


if not os.path.exists(SNAPSHOT_DIR):
    os.makedirs(SNAPSHOT_DIR)

def load_users():
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return {row['username']: row['password'] for row in csv.DictReader(f)}
    

class VehicleLoggerApp:
    def __init__(self, root):
        self.front_rtsp = FRONT_RTSP
        self.back_rtsp = BACK_RTSP
        self.logo_img = None
        self.root = root
        self.root.configure(bg="white")
        self.username = None
        self.users = load_users()
        self.show_login_ui()

    def show_login_ui(self):
        self.clear_ui()
        try:
            img = Image.open("x1.jpg").resize((200, 250))
            self.logo_img = ImageTk.PhotoImage(img)
            tk.Label(self.root, image=self.logo_img, bg="white").pack(pady=10)
        except:
            print("Logo not found")
        tk.Label(self.root, text="หมู่บ้าน คุณาลัย-รัตนาธิเบศร์", font=("THSarabun", 28, "bold"), bg="white").pack(pady=15)
        tk.Label(self.root, text="ชื่อผู้ใช้งาน", font=("THSarabun", 24, "bold"), bg="white").pack()
        self.username_entry = tk.Entry(self.root, font=("THSarabun", 18), width=28)
        self.username_entry.pack(pady=5)
        tk.Label(self.root, text="รหัสผ่าน", font=("THSarabun", 24, "bold"), bg="white").pack()
        self.password_entry = tk.Entry(self.root, show="*", font=("THSarabun", 18), width=28)
        self.password_entry.pack(pady=5)
        tk.Button(self.root, text="เข้าสู่ระบบ", font=("THSarabun", 18, "bold"), command=self.authenticate_user, width=20).pack(pady=15)
        
    # authenticate the user
    def authenticate_user(self):
        u, p = self.username_entry.get(), self.password_entry.get()
        if self.users.get(u) == p:
            self.username = u
            self.show_main_ui()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

    def start_listening(self, event=None):
        threading.Thread(target=self.listen_and_process, daemon=True).start()

    # A function for voice recognition
    # After observing how the text-to-speech works, the syllalbal of each word has been added also, 
    def listen_and_process(self):
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            with self.microphone as source:
                print("🎤 เริ่มฟัง...")
                self.audio = self.recognizer.listen(source, phrase_time_limit=10)
            with open("speech_plate.wav", "wb") as f:
                f.write(self.audio.get_wav_data())
            text = self.recognizer.recognize_google(self.audio, language="th-TH")
            print(f"🎧 ระบบเข้าใจว่า: {text}")

            consonant_map = {
                "กไก่": "ก", "ขไข่": "ข", "ฃขวด": "ฃ", "คควาย": "ค", "ฅคน": "ฅ",
                "ฆระฆัง": "ฆ", "งงู": "ง", "จจาน": "จ", "ฉฉิ่ง": "ฉ", "ชช้าง": "ช",
                "ซโซ่": "ซ", "ฌเฌอ": "ฌ", "ญหญิง": "ญ", "ฎชฎา": "ฎ", "ฏปฏัก": "ฏ",
                "ฐฐาน": "ฐ", "ฑมณโฑ": "ฑ", "ฒผู้เฒ่า": "ฒ", "ณเณร": "ณ", "ดเด็ก": "ด",
                "ตเต่า": "ต", "ถถุง": "ถ", "ททหาร": "ท", "ธธง": "ธ", "นหนู": "น",
                "บใบไม้": "บ", "ปปลา": "ป", "ผผึ้ง": "ผ", "ฝฝา": "ฝ", "พพาน": "พ",
                "ฟฟัน": "ฟ", "ภสำเภา": "ภ", "มม้า": "ม", "ยยักษ์": "ย", "รเรือ": "ร",
                "ฤๅษี": "ฤ", "ลลิง": "ล", "ฦฦา": "ฦ", "วแหวน": "ว", "ศศาลา": "ศ",
                "ษฤๅษี": "ษ", "สเสือ": "ส", "หหีบ": "ห", "ฬจุฬา": "ฬ", "ออ่าง": "อ", "ฮนกฮูก": "ฮ",
                "กอไก่": "ก", "ขอไข่": "ข", "ฃอขวด": "ฃ", "คอควาย": "ค", "ฅอคน": "ฅ",
                "ฆอระฆัง": "ฆ", "งองู": "ง", "จอจาน": "จ", "ฉอฉิ่ง": "ฉ", "ชอช้าง": "ช",
                "ซอโซ่": "ซ", "ฌอเฌอ": "ฌ", "ญอหญิง": "ญ", "ฎอชฎา": "ฎ", "ฏอปฏัก": "ฏ",
                "ฐอฐาน": "ฐ", "ฑอมณโฑ": "ฑ", "ฒอผู้เฒ่า": "ฒ", "ณอเณร": "ณ", "ดอเด็ก": "ด",
                "ตอเต่า": "ต", "ถอถุง": "ถ", "ทอทหาร": "ท", "ธอธง": "ธ", "นอหนู": "น",
                "บอใบไม้": "บ", "ปอปลา": "ป", "ผอผึ้ง": "ผ", "ฝอฝา": "ฝ", "พอพาน": "พ",
                "ฟอฟัน": "ฟ", "ภอสำเภา": "ภ", "มอม้า": "ม", "ยอยักษ์": "ย", "รอเรือ": "ร",
                "ฤอๅษี": "ฤ", "ลอลิง": "ล", "ฦอฦา": "ฦ", "วอแหวน": "ว", "ศอศาลา": "ศ",
                "ษอฤๅษี": "ษ", "สอเสือ": "ส", "หอหีบ": "ห", "ฬอจุฬา": "ฬ", "อออ่าง": "อ", "ฮอนกฮูก": "ฮ"
            }
            for full, short in consonant_map.items():
                text = text.replace(full, short)

            self.plate_entry.delete(0, tk.END)
            self.plate_entry.insert(0, text)

        except Exception as e:
            print(f"❌ Speech recognition error: {e}")

    

    def show_main_ui(self):
        self.clear_ui()
        tk.Button(self.root, text="ออกจากระบบ", fg="red", font=("THSarabun", 14, "bold"), command=self.show_login_ui).place(x=1910, y=5)
        tk.Label(self.root, text=f"ยินดีต้อนรับ, คุณ {self.username}", font=("THSarabun", 30), bg="white").pack(pady=(15, 10))

        # Camera feed row container
        cam_frame = tk.Frame(self.root, bg="white")
        cam_frame.pack(pady=(0, 10))

        # Front camera
        front_frame = tk.Frame(cam_frame, bg="white")
        front_frame.pack(side="left", padx=20)

        tk.Label(front_frame, text="📷 กล้องหน้า", font=("THSarabun", 16), bg="white").pack()
        self.front_cam_label = tk.Label(front_frame, bg="white")
        self.front_cam_label.pack()

        # Back camera
        back_frame = tk.Frame(cam_frame, bg="white")
        back_frame.pack(side="left", padx=20)

        tk.Label(back_frame, text="📷 กล้องหลัง", font=("THSarabun", 16), bg="white").pack()
        self.back_cam_label = tk.Label(back_frame, bg="white")
        self.back_cam_label.pack()


        self.content_frame = tk.Frame(self.root, bg="white")
        self.content_frame.pack(pady=10)
        plate_row = tk.Frame(self.content_frame, bg="white")
        plate_row.pack(pady=30)

        tk.Label(plate_row, text="ป้ายทะเบียน:", font=("THSarabun", 26, "bold"), bg="white").pack(side="left", padx=(0, 10))
        self.plate_entry = tk.Entry(plate_row, font=("THSarabun", 26), bg="#baf5eb", width=25)
        self.plate_entry.pack(side="left")

        self.speech_button = tk.Button(plate_row, text="🎤 พูดทะเบียน", font=("THSarabun", 16))
        self.speech_button.pack(side="left", padx=(10, 0))

        self.speech_button.bind("<ButtonPress-1>", self.start_listening)

        self.house_row = tk.Frame(self.content_frame, bg="white")
        self.house_row.pack(pady=(0, 20))

        tk.Label(self.house_row, text="บ้านเลขที่:", font=("THSarabun", 24), bg="white").pack(side="left", padx=(10, 20))
        self.house_number = tk.StringVar()
        self.house_combobox = ttk.Combobox(self.house_row, textvariable=self.house_number, font=("THSarabun", 18), width=10)
        self.house_combobox['values'] = [str(i) for i in range(1, 121)]
        self.house_combobox.set("1")  # Default
        self.house_combobox.pack(side="left")



        self.selected_type = tk.StringVar(value="Taxi")
        vehicle_type_row = tk.Frame(self.content_frame, bg="white")
        vehicle_type_row.pack(pady=(0, 20), anchor="w")

        tk.Label(vehicle_type_row, text="ประเภทรถ:", font=("THSarabun", 24), bg="white").pack(side="left", padx=(10, 20))
        radio_frame = tk.Frame(vehicle_type_row, bg="white")
        radio_frame.pack(side="left")
        self.vehicle_types = ["รถส่งของ", "ผู้มาติดต่อ", "ส่งอาหาร", "Taxi", "อื่นๆ"]
        self.vehicle_type_buttons = {}
        for txt in self.vehicle_types:
            btn = tk.Button(radio_frame, text=txt, font=("THSarabun", 14), width=20, pady=10, relief="raised", bg="white",
                            command=lambda t=txt: self.select_vehicle_type(t))
            btn.pack(side="left", padx=50, pady=5)
            self.vehicle_type_buttons[txt] = btn
        self.update_button_highlight()

        self.other_text_label = tk.Label(self.content_frame, text="รายละเอียดเพิ่มเติม:", font=("THSarabun", 14), bg="white")
        self.other_text = tk.Text(self.content_frame, height=1, width=40, font=("THSarabun", 13), bg="#e8e6e3")

        self.log_button = tk.Button(self.root, text="บันทึก (รถเข้า)", font=("THSarabun", 20), height=2, width=20, command=self.log_vehicle)
        self.log_button.pack(pady=10)

        self.exit_button = tk.Button(self.root, text="สแกน รถออก", font=("THSarabun", 14), command=self.log_exit)
        self.exit_button.place(x=10, y=10)

        self.start_live_feeds()

    def start_live_feeds(self):
        self.front_cap = cv2.VideoCapture(self.front_rtsp)
        self.back_cap = cv2.VideoCapture(self.back_rtsp)
        self.update_live_frames()

    def update_live_frames(self):
        ret1, frame1 = self.front_cap.read()
        ret2, frame2 = self.back_cap.read()

        if ret1:
            frame1 = cv2.resize(frame1, (800, 500))
            frame1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)
            img1 = Image.fromarray(frame1)
            self.front_imgtk = ImageTk.PhotoImage(image=img1)
            self.front_cam_label.configure(image=self.front_imgtk)

        if ret2:
            frame2 = cv2.resize(frame2, (800,500))
            frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)
            img2 = Image.fromarray(frame2)
            self.back_imgtk = ImageTk.PhotoImage(image=img2)
            self.back_cam_label.configure(image=self.back_imgtk)

        self.root.after(30, self.update_live_frames)

    def capture_snapshots(self, snapshot_id):
        front_path = back_path = ""
        if hasattr(self, 'front_cap') and hasattr(self, 'back_cap'):
            ret1, frame1 = self.front_cap.read()
            ret2, frame2 = self.back_cap.read()
            front_path = os.path.join(SNAPSHOT_DIR, f"{snapshot_id}_front.jpg")
            back_path = os.path.join(SNAPSHOT_DIR, f"{snapshot_id}_back.jpg")
            if ret1:
                cv2.imwrite(front_path, frame1)
                # Show front image in new window
                win_front = tk.Toplevel(self.root)
                win_front.title("ภาพจากกล้องหน้า")
                img = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)))
                lbl = tk.Label(win_front, image=img)
                lbl.image = img
                lbl.pack()
            if ret2:
                cv2.imwrite(back_path, frame2)
                # Show back image in new window
                win_back = tk.Toplevel(self.root)
                win_back.title("ภาพจากกล้องหลัง")
                img = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)))
                lbl = tk.Label(win_back, image=img)
                lbl.image = img
                lbl.pack()
        return front_path, back_path


    def select_vehicle_type(self, vehicle_type):
        self.selected_type.set(vehicle_type)
        self.update_button_highlight()
        self.check_type()
        self.check_house_number_visibility()


    def update_button_highlight(self):
        for t, btn in self.vehicle_type_buttons.items():
            if t == self.selected_type.get():
                btn.config(bg="#6899fc", relief="sunken", font=("THSarabun", 14, "bold"))
            else:
                btn.config(bg="white", relief="raised", font=("THSarabun", 14))
    # if อื่นๆ there will be a text box showing for operator to input necessary information
    def check_type(self):
        if self.selected_type.get() == "อื่นๆ":
            self.other_text_label.pack()
            self.other_text.pack()
        else:
            self.other_text_label.pack_forget()
            self.other_text.pack_forget()

    def check_house_number_visibility(self):
        if self.selected_type.get() == "รถส่งของ":
            self.house_row.pack_forget()
        else:
            self.house_row.pack(pady=(0, 20))

    # generate the data and save it to the logging file with snapshot of the vehicle entering the village
    def log_vehicle(self):
        
        plate = self.plate_entry.get().strip()

        house_no = "" if self.selected_type.get() == "รถส่งของ" else self.house_number.get()


        v_type = self.selected_type.get()
        other = self.other_text.get("1.0", tk.END).strip() if v_type == "อื่นๆ" else ""

        if not plate:
            return messagebox.showwarning("Input Error", "Please enter a license plate.")
        if v_type == "อื่นๆ" and not other:
            return messagebox.showwarning("Input Error", "Please enter details for 'อื่นๆ'")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp_id = datetime.now().strftime('%Y%m%d%H%M%S')
        barcode_id = f"{self.username}_{timestamp_id}" if v_type == "ผู้มาติดต่อ" else ""

        front_path, back_path = self.capture_snapshots(timestamp_id)

        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow([plate, self.username, now, v_type, other, barcode_id, "", front_path, back_path, house_no])


        # Show logged info in a popup
        messagebox.showinfo("Success", f"บันทึกสำเร็จ\n\nทะเบียน: {plate}\nติดต่อบ้านเลขที่ : 69 / {house_no}\nประเภท: {v_type}\nเวลา: {now}\nผู้ใช้: {self.username}\n\n📸 รูปกล้องหน้า: {front_path}\n📸 รูปกล้องหลัง: {back_path}")

        if v_type == "ผู้มาติดต่อ":
            self.generate_pdf_receipt(plate, v_type, other, now, barcode_id,house_no)

        self.plate_entry.delete(0, tk.END)
        self.other_text.delete("1.0", tk.END)
        self.selected_type.set("รถส่งของ")
        self.update_button_highlight()
        self.check_type()
        
    # The slip for visitor should be generated with necessary information for the owner of the house
    # when the confirm button, the app will automatically sends the command to designated printer
    # if no specific printer specified, it will send the command to default printer as set in the settion of pc running this program
    def generate_pdf_receipt(self, plate, v_type, other, time, barcode_id,house_no):
        pdf_path = "visitorID.pdf"
        barcode_filename = f"barcode_{barcode_id}"
        barcode_path = f"{barcode_filename}.png"
        Code128(barcode_id, writer=ImageWriter()).save(barcode_filename)
        c = canvas.Canvas(pdf_path, pagesize=(8 * cm, 14 * cm))
        w, h = (8 * cm, 14 * cm)
        try:
            c.drawImage("x1.jpg", 80, h - 100, width=80, height=80)
        except:
            pass
        pdfmetrics.registerFont(TTFont("THSarabun", "THSarabunNew.ttf"))
        c.setFont("THSarabun", 18)
        y = h - 130
        line_h = 20
        for txt in [f"ผู้ใช้: {self.username}", f"เวลา: {time}", f"ทะเบียนรถ: {plate}",f"ติดต่อบ้านเลขที่: 69 / {house_no}", f"ประเภท: {v_type}"]:
            c.drawString(40, y, txt)
            y -= line_h
        if other:
            c.drawString(40, y, f"รายละเอียด: {other}")
            y -= line_h
        y -= 120
        c.rect(40, 100, w - 80, 70)
        c.setFont("THSarabun", 14)
        c.drawCentredString(w / 2, 135, "ช่องสำหรับลูกบ้านประทับตรา/เซ็น")
        c.drawImage(barcode_path, 15, y - 50, width=200, height=65)
        c.showPage()
        c.save()
        win32api.ShellExecute(0, "print", pdf_path, f'/d:"{win32print.GetDefaultPrinter()}"', ".", 0)

    def log_exit(self):
        barcode = simpledialog.askstring("Scan Barcode", "Enter barcode ID:")
        if not barcode:
            return
        updated = []
        found = False
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            rows = list(csv.reader(f))
            headers = rows[0]
            for row in rows[1:]:
                if row[5] == barcode and not row[6]:
                    row[6] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    found = True
                updated.append(row)
        if found:
            with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow(headers)
                csv.writer(f).writerows(updated)
            messagebox.showinfo("Success", "Exit time logged successfully")
        else:
            messagebox.showerror("Not Found", "Barcode not found or already logged")

    def clear_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

root = tk.Tk()
root.title("Vehicle Logger with Live Feed")
root.geometry("1920x1080")
root.configure(bg="white")
app = VehicleLoggerApp(root)
root.mainloop()

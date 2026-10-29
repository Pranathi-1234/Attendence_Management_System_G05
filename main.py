"""Tkinter GUI for the Python-Based Attendance Management System.

Run:  python main.py
First login:  admin / admin123
New students and faculty get a login equal to their username (e.g. stu1 / stu1, fac1 / fac1).
"""
import tkinter as tk
from datetime import date
from tkinter import ttk, messagebox

from manager import AttendanceManager, LOW_ATTENDANCE_LIMIT
from models import AttendanceError


def make_table(parent, columns, widths=None, height=12):
    """Create a Treeview with scrollbar; returns the tree."""
    frame = ttk.Frame(parent)
    frame.pack(fill="both", expand=True, pady=6)
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=height)
    for i, c in enumerate(columns):
        tree.heading(c, text=c)
        tree.column(c, width=(widths[i] if widths else 110), anchor="w")
    bar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=bar.set)
    tree.pack(side="left", fill="both", expand=True)
    bar.pack(side="right", fill="y")
    return tree


def fill_table(tree, rows):
    tree.delete(*tree.get_children())
    for r in rows:
        tree.insert("", "end", values=r)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Attendance Management System")
        self.geometry("900x620")
        self.manager = AttendanceManager()
        self.user = None
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_login()

    def on_close(self):
        self.manager.close()
        self.destroy()

    def clear(self):
        for w in self.winfo_children():
            w.destroy()

    def run_safely(self, action):
        """Run an action and show any AttendanceError as a message box (exception handling)."""
        try:
            return action()
        except AttendanceError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:                      # unexpected problems
            messagebox.showerror("Unexpected error", f"{type(e).__name__}: {e}")
        return None

    # ---------------- login ----------------
    def show_login(self):
        self.clear()
        self.user = None
        box = ttk.Frame(self, padding=30)
        box.place(relx=0.5, rely=0.4, anchor="center")
        ttk.Label(box, text="Attendance Management System", font=("Arial", 18, "bold")).grid(columnspan=2, pady=10)
        ttk.Label(box, text="Username").grid(row=1, column=0, sticky="e", pady=4)
        ttk.Label(box, text="Password").grid(row=2, column=0, sticky="e", pady=4)
        self.e_user, self.e_pass = ttk.Entry(box, width=25), ttk.Entry(box, width=25, show="*")
        self.e_user.grid(row=1, column=1, padx=6)
        self.e_pass.grid(row=2, column=1, padx=6)
        ttk.Button(box, text="Login", command=self.do_login).grid(row=3, columnspan=2, pady=12)
        self.e_user.focus()
        self.bind("<Return>", lambda e: self.do_login())

    def do_login(self):
        user = self.run_safely(lambda: self.manager.authenticate(self.e_user.get(), self.e_pass.get()))
        if user:
            self.user = user
            self.unbind("<Return>")
            self.run_safely(self.show_dashboard)

    # ---------------- dashboard ----------------
    def show_dashboard(self):
        self.clear()
        top = ttk.Frame(self, padding=6)
        top.pack(fill="x")
        ttk.Label(top, text=f"Logged in as {self.user}", font=("Arial", 11, "bold")).pack(side="left")
        ttk.Button(top, text="Logout", command=self.show_login).pack(side="right")
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, padx=8, pady=4)
        builders = {"Students": self.tab_students, "Faculty & Subjects": self.tab_faculty_subjects,
                    "Mark Attendance": self.tab_mark, "Reports": self.tab_reports,
                    "My Attendance": self.tab_my_attendance}
        for name in self.user.menu_options():      # polymorphism: each role shows its own tabs
            frame = ttk.Frame(tabs, padding=10)
            tabs.add(frame, text=name)
            builders[name](frame)

    # ---------------- Admin: students ----------------
    def tab_students(self, f):
        form = ttk.Frame(f)
        form.pack(fill="x")
        self.sv = {k: tk.StringVar() for k in ("id", "name", "department", "semester", "contact")}
        for i, (k, label) in enumerate([("name", "Name"), ("department", "Department"),
                                        ("semester", "Semester"), ("contact", "Contact")]):
            ttk.Label(form, text=label).grid(row=0, column=i * 2, padx=3)
            ttk.Entry(form, textvariable=self.sv[k], width=14).grid(row=0, column=i * 2 + 1, padx=3)
        btns = ttk.Frame(f)
        btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="Add", command=self.add_student).pack(side="left", padx=3)
        ttk.Button(btns, text="Update", command=self.update_student).pack(side="left", padx=3)
        ttk.Button(btns, text="Delete", command=self.delete_student).pack(side="left", padx=3)
        ttk.Button(btns, text="Clear", command=self.clear_student_form).pack(side="left", padx=3)
        self.search_var = tk.StringVar()
        ttk.Button(btns, text="Search", command=self.refresh_students).pack(side="right", padx=3)
        ttk.Entry(btns, textvariable=self.search_var, width=20).pack(side="right")
        ttk.Label(btns, text="Search (name / dept / id):").pack(side="right", padx=4)
        self.stu_tree = make_table(f, ("ID", "Name", "Department", "Semester", "Contact"), [60, 200, 140, 80, 140])
        self.stu_tree.bind("<<TreeviewSelect>>", self.on_student_select)
        self.refresh_students()

    def refresh_students(self):
        rows = self.run_safely(lambda: self.manager.list_students(self.search_var.get())) or []
        fill_table(self.stu_tree, [(s.student_id, s.name, s.department, s.semester, s.contact) for s in rows])

    def on_student_select(self, _event=None):
        sel = self.stu_tree.selection()
        if sel:
            v = self.stu_tree.item(sel[0], "values")
            for k, val in zip(("id", "name", "department", "semester", "contact"), v):
                self.sv[k].set(val)

    def clear_student_form(self):
        for var in self.sv.values():
            var.set("")

    def add_student(self):
        def act():
            sid, login = self.manager.add_student(self.sv["name"].get(), self.sv["department"].get(),
                                                  self.sv["semester"].get(), self.sv["contact"].get())
            messagebox.showinfo("Student added", f"Student ID {sid} added.\nLogin: {login} / {login}")
            self.clear_student_form()
            self.refresh_students()
        self.run_safely(act)

    def update_student(self):
        def act():
            if not self.sv["id"].get():
                raise AttendanceError("Select a student from the table first.")
            self.manager.update_student(int(self.sv["id"].get()), self.sv["name"].get(),
                                        self.sv["department"].get(), self.sv["semester"].get(), self.sv["contact"].get())
            self.refresh_students()
        self.run_safely(act)

    def delete_student(self):
        def act():
            if not self.sv["id"].get():
                raise AttendanceError("Select a student from the table first.")
            if messagebox.askyesno("Confirm", "Delete this student and all attendance records?"):
                self.manager.delete_student(int(self.sv["id"].get()))
                self.clear_student_form()
                self.refresh_students()
        self.run_safely(act)

    # ---------------- Admin: faculty and subjects ----------------
    def tab_faculty_subjects(self, f):
        left = ttk.LabelFrame(f, text="Add faculty", padding=8)
        left.pack(side="left", fill="both", expand=True, padx=4)
        self.fv = {k: tk.StringVar() for k in ("name", "department", "email")}
        for i, (k, label) in enumerate([("name", "Name"), ("department", "Department"), ("email", "Email")]):
            ttk.Label(left, text=label).grid(row=i, column=0, sticky="e", pady=3)
            ttk.Entry(left, textvariable=self.fv[k], width=22).grid(row=i, column=1, padx=4)
        ttk.Button(left, text="Add faculty", command=self.add_faculty).grid(row=3, columnspan=2, pady=6)
        holder_l = ttk.Frame(left)
        holder_l.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=6)
        left.rowconfigure(4, weight=1)
        self.fac_tree = make_table(holder_l, ("ID", "Name", "Department"), [40, 140, 100], height=10)

        right = ttk.LabelFrame(f, text="Add subject", padding=8)
        right.pack(side="left", fill="both", expand=True, padx=4)
        self.subj_name, self.subj_dept, self.subj_fac = tk.StringVar(), tk.StringVar(), tk.StringVar()
        for i, (var, label) in enumerate([(self.subj_name, "Subject"), (self.subj_dept, "Department"),
                                          (self.subj_fac, "Faculty ID (optional)")]):
            ttk.Label(right, text=label).grid(row=i, column=0, sticky="e", pady=3)
            ttk.Entry(right, textvariable=var, width=20).grid(row=i, column=1, padx=4)
        ttk.Button(right, text="Add subject", command=self.add_subject).grid(row=3, columnspan=2, pady=6)
        holder_r = ttk.Frame(right)
        holder_r.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=6)
        right.rowconfigure(4, weight=1)
        self.subj_tree = make_table(holder_r, ("ID", "Subject", "Department"), [40, 140, 100], height=10)
        self.refresh_fac_subj()

    def refresh_fac_subj(self):
        fill_table(self.fac_tree, [(r["faculty_id"], r["name"], r["department"]) for r in self.manager.list_faculty()])
        fill_table(self.subj_tree, [(r["subject_id"], r["subject_name"], r["department"]) for r in self.manager.list_subjects()])

    def add_faculty(self):
        def act():
            fid, login = self.manager.add_faculty(self.fv["name"].get(), self.fv["department"].get(), self.fv["email"].get())
            messagebox.showinfo("Faculty added", f"Faculty ID {fid} added.\nLogin: {login} / {login}")
            for v in self.fv.values():
                v.set("")
            self.refresh_fac_subj()
        self.run_safely(act)

    def add_subject(self):
        def act():
            fac = self.subj_fac.get().strip()
            self.manager.add_subject(self.subj_name.get(), self.subj_dept.get(), int(fac) if fac else None)
            self.subj_name.set("")
            self.subj_dept.set("")
            self.subj_fac.set("")
            self.refresh_fac_subj()
        self.run_safely(act)

    # ---------------- Faculty: mark attendance ----------------
    def tab_mark(self, f):
        top = ttk.Frame(f)
        top.pack(fill="x")
        self.subjects = {f"{r['subject_id']} - {r['subject_name']}": r["subject_id"] for r in self.manager.list_subjects()}
        ttk.Label(top, text="Subject").pack(side="left")
        self.cmb_subject = ttk.Combobox(top, values=list(self.subjects), state="readonly", width=28)
        self.cmb_subject.pack(side="left", padx=6)
        ttk.Label(top, text="Date (YYYY-MM-DD)").pack(side="left")
        self.date_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(top, textvariable=self.date_var, width=12).pack(side="left", padx=6)
        ttk.Button(top, text="Load students", command=self.load_students_for_marking).pack(side="left", padx=6)
        ttk.Label(f, text="Tick the box for students who are PRESENT. Unticked students are saved as Absent.").pack(anchor="w", pady=4)
        canvas = tk.Canvas(f, height=380)
        bar = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)
        self.mark_frame = ttk.Frame(canvas)
        self.mark_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.mark_frame, anchor="nw")
        canvas.configure(yscrollcommand=bar.set)
        canvas.pack(side="left", fill="both", expand=True)
        bar.pack(side="left", fill="y")
        ttk.Button(f, text="Save attendance", command=self.save_attendance).pack(side="bottom", pady=8)
        self.present_vars = {}

    def load_students_for_marking(self):
        def act():
            if not self.cmb_subject.get():
                raise AttendanceError("Select a subject first.")
            sid = self.subjects[self.cmb_subject.get()]
            existing = {r["student_id"]: r["status"] == "Present" for r in self.manager.records_for_date(sid, self.date_var.get())}
            for w in self.mark_frame.winfo_children():
                w.destroy()
            self.present_vars = {}
            for i, s in enumerate(self.manager.list_students()):
                var = tk.BooleanVar(value=existing.get(s.student_id, True))
                self.present_vars[s.student_id] = var
                ttk.Checkbutton(self.mark_frame, text=str(s), variable=var).grid(row=i, column=0, sticky="w", pady=1)
            if existing:
                messagebox.showinfo("Existing records", "Attendance already exists for this date; saving will update it.")
        self.run_safely(act)

    def save_attendance(self):
        def act():
            if not self.present_vars:
                raise AttendanceError("Load the students first.")
            sid = self.subjects[self.cmb_subject.get()]
            d = self.date_var.get()
            for student_id, var in self.present_vars.items():
                status = "Present" if var.get() else "Absent"
                if self.manager.attendance_exists(student_id, sid, d):
                    self.manager.update_attendance(student_id, sid, d, status)
                else:
                    self.manager.mark_attendance(student_id, sid, d, status)
            messagebox.showinfo("Saved", f"Attendance saved for {len(self.present_vars)} students.")
        self.run_safely(act)

    # ---------------- Admin / Faculty: reports ----------------
    def tab_reports(self, f):
        top = ttk.Frame(f)
        top.pack(fill="x")
        for text, cmd in [("Class-wise", self.rep_class), ("Subject-wise", self.rep_subject),
                          ("Low attendance (<%d%%)" % LOW_ATTENDANCE_LIMIT, self.rep_low)]:
            ttk.Button(top, text=text, command=lambda c=cmd: self.run_safely(c)).pack(side="left", padx=4)
        ttk.Label(top, text="Student ID").pack(side="left", padx=(16, 2))
        self.rep_sid = tk.StringVar()
        ttk.Entry(top, textvariable=self.rep_sid, width=8).pack(side="left")
        ttk.Button(top, text="Student-wise", command=lambda: self.run_safely(self.rep_student)).pack(side="left", padx=4)
        self.rep_holder = ttk.Frame(f)
        self.rep_holder.pack(fill="both", expand=True)
        self.rep_tree = None

    def show_report(self, columns, rows):
        for w in self.rep_holder.winfo_children():
            w.destroy()
        self.rep_tree = make_table(self.rep_holder, columns, [140] * len(columns), height=16)
        fill_table(self.rep_tree, rows)

    def rep_class(self):
        self.show_report(("Student ID", "Name", "Classes", "Attended", "Percent"), self.manager.class_report())

    def rep_subject(self):
        self.show_report(("Subject", "Records", "Present", "Percent"), self.manager.subject_report())

    def rep_low(self):
        self.show_report(("Student ID", "Name", "Classes", "Attended", "Percent"), self.manager.find_low_attendance())

    def rep_student(self):
        if not self.rep_sid.get().strip().isdigit():
            raise AttendanceError("Enter a numeric student ID.")
        self.show_report(("Subject", "Classes", "Attended", "Absent", "Percent"),
                         self.manager.student_report(int(self.rep_sid.get())))

    # ---------------- Student: own attendance ----------------
    def tab_my_attendance(self, f):
        sid = self.user.ref_id
        student = self.run_safely(lambda: self.manager.get_student(sid))
        if not student:
            return
        ttk.Label(f, text=str(student), font=("Arial", 12, "bold")).pack(anchor="w")
        overall = self.manager.overall_percentage(sid)
        colour = "red" if overall < LOW_ATTENDANCE_LIMIT else "green"
        tk.Label(f, text=f"Overall attendance: {overall}%", fg=colour, font=("Arial", 12)).pack(anchor="w", pady=4)
        if overall < LOW_ATTENDANCE_LIMIT and self.manager.student_report(sid):
            tk.Label(f, text=f"Warning: below the required {LOW_ATTENDANCE_LIMIT:.0f}%", fg="red").pack(anchor="w")
        tree = make_table(f, ("Subject", "Classes", "Attended", "Absent", "Percent"), [200, 90, 90, 90, 90])
        fill_table(tree, self.manager.student_report(sid))


if __name__ == "__main__":
    App().mainloop()

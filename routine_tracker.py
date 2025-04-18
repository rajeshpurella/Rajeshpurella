import sqlite3
from tkinter import *
from tkinter import ttk, messagebox
import time
import os
from datetime import datetime

# Initialize database
def init_db():
    conn = sqlite3.connect('routine.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 time TEXT NOT NULL,
                 task TEXT NOT NULL,
                 done BOOLEAN DEFAULT 0,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Main Application
class RoutineTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Daily Routine Tracker")
        self.root.geometry("600x400")
        
        # Style
        self.style = ttk.Style()
        self.style.configure('TButton', font=('Helvetica', 10))
        self.style.configure('TLabel', font=('Helvetica', 11))
        
        # Variables
        self.task_var = StringVar()
        self.time_var = StringVar(value=datetime.now().strftime("%H:%M"))
        
        # GUI Elements
        self.setup_ui()
        self.load_tasks()
        
        # Check reminders every minute
        self.root.after(60000, self.check_reminders)
    
    def setup_ui(self):
        # Main Frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=BOTH, expand=True)
        
        # Input Frame
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=X, pady=5)
        
        ttk.Label(input_frame, text="Time:").pack(side=LEFT, padx=5)
        self.time_entry = ttk.Entry(input_frame, textvariable=self.time_var, width=10)
        self.time_entry.pack(side=LEFT, padx=5)
        
        ttk.Label(input_frame, text="Task:").pack(side=LEFT, padx=5)
        self.task_entry = ttk.Entry(input_frame, textvariable=self.task_var, width=30)
        self.task_entry.pack(side=LEFT, padx=5, expand=True, fill=X)
        
        add_btn = ttk.Button(input_frame, text="Add Task", command=self.add_task)
        add_btn.pack(side=LEFT, padx=5)
        
        # Task List
        self.tree = ttk.Treeview(main_frame, columns=('time', 'task', 'status'), show='headings')
        self.tree.heading('time', text='Time')
        self.tree.heading('task', text='Task')
        self.tree.heading('status', text='Status')
        self.tree.column('time', width=100)
        self.tree.column('task', width=350)
        self.tree.column('status', width=100)
        self.tree.pack(fill=BOTH, expand=True, pady=10)
        
        # Action Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=X)
        
        complete_btn = ttk.Button(btn_frame, text="Mark Complete", command=self.mark_complete)
        complete_btn.pack(side=LEFT, padx=5)
        
        delete_btn = ttk.Button(btn_frame, text="Delete Task", command=self.delete_task)
        delete_btn.pack(side=LEFT, padx=5)
        
        export_btn = ttk.Button(btn_frame, text="Export to TXT", command=self.export_tasks)
        export_btn.pack(side=RIGHT, padx=5)
    
    def add_task(self):
        task_time = self.time_var.get()
        task_text = self.task_var.get()
        
        if not task_time or not task_text:
            messagebox.showwarning("Warning", "Please enter both time and task!")
            return
        
        try:
            conn = sqlite3.connect('routine.db')
            c = conn.cursor()
            c.execute("INSERT INTO tasks (time, task) VALUES (?, ?)", (task_time, task_text))
            conn.commit()
            conn.close()
            
            self.load_tasks()
            self.task_var.set("")
            self.time_var.set(datetime.now().strftime("%H:%M"))
            self.task_entry.focus()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add task: {str(e)}")
    
    def load_tasks(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            conn = sqlite3.connect('routine.db')
            c = conn.cursor()
            c.execute("SELECT id, time, task, done FROM tasks ORDER BY time")
            tasks = c.fetchall()
            conn.close()
            
            for task in tasks:
                status = "✓ Done" if task[3] else "Pending"
                self.tree.insert('', 'end', values=(task[1], task[2], status), iid=task[0])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tasks: {str(e)}")
    
    def mark_complete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a task!")
            return
            
        try:
            conn = sqlite3.connect('routine.db')
            c = conn.cursor()
            for item in selected:
                current_status = self.tree.item(item)['values'][2]
                new_status = not ("Done" in current_status)
                c.execute("UPDATE tasks SET done = ? WHERE id = ?", (new_status, item))
                self.tree.item(item, values=(
                    self.tree.item(item)['values'][0],
                    self.tree.item(item)['values'][1],
                    "✓ Done" if new_status else "Pending"
                ))
            conn.commit()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update task: {str(e)}")
    
    def delete_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a task!")
            return
            
        if messagebox.askyesno("Confirm", "Delete selected task(s)?"):
            try:
                conn = sqlite3.connect('routine.db')
                c = conn.cursor()
                for item in selected:
                    c.execute("DELETE FROM tasks WHERE id = ?", (item,))
                    self.tree.delete(item)
                conn.commit()
                conn.close()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete task: {str(e)}")
    
    def check_reminders(self):
        try:
            current_time = datetime.now().strftime("%H:%M")
            
            conn = sqlite3.connect('routine.db')
            c = conn.cursor()
            c.execute("SELECT task FROM tasks WHERE time = ? AND done = 0", (current_time,))
            tasks = c.fetchall()
            conn.close()
            
            if tasks:
                reminder_text = "\n".join([f"• {task[0]}" for task in tasks])
                messagebox.showinfo("Reminder", f"It's time for:\n{reminder_text}")
        
        except Exception as e:
            print(f"Reminder error: {str(e)}")
        
        # Check again in 1 minute
        self.root.after(60000, self.check_reminders)
    
    def export_tasks(self):
        try:
            filename = f"routine_export_{datetime.now().strftime('%Y%m%d')}.txt"
            with open(filename, 'w') as f:
                f.write("Daily Routine Export\n")
                f.write("===================\n\n")
                
                conn = sqlite3.connect('routine.db')
                c = conn.cursor()
                c.execute("SELECT time, task, done FROM tasks ORDER BY time")
                tasks = c.fetchall()
                conn.close()
                
                for task in tasks:
                    status = "✓" if task[2] else "◻"
                    f.write(f"{task[0]} - {task[1]} {status}\n")
            
            messagebox.showinfo("Success", f"Tasks exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")

# Initialize and run
if __name__ == "__main__":
    init_db()
    root = Tk()
    app = RoutineTracker(root)
    root.mainloop()
import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime, timedelta
import os
import sys
from PIL import Image, ImageTk  # Add PIL for better image handling
from tkcalendar import DateEntry  # For date/time picker

print("Starting Crystal Lizard Desktop Pet...")

class DeskPet:
    LOCK_FILE = "deskpet.lock"
    POMODORO_WORK = 25  # minutes
    POMODORO_BREAK = 5  # minutes
    POMODORO_LONG_BREAK = 15  # minutes
    WALK_SPEED = 2  # pixels per frame
    WALK_DISTANCE = 100  # pixels to walk before turning
    WALK_FRAME_DELAY = 200  # milliseconds between animation frames

    def __init__(self):
        print("Initializing...")
        # Check for other instances first
        if self.is_already_running():
            print("Another instance is already running. Closing it...")
            self.cleanup_previous_instance()
        
        # Create lock file
        self.create_lock_file()
        print("Lock file created")
        
        self.root = tk.Tk()
        print("Tkinter window created")
        self.root.overrideredirect(True)  # Remove window decorations
        self.root.attributes('-topmost', True)  # Keep window on top
        self.root.attributes('-alpha', 1.0)  # Full opacity
        self.root.attributes('-transparentcolor', 'SystemButtonFace')
        self.root.configure(bg='SystemButtonFace')
        print("Window attributes set")
        
        # Create a transparent frame for the pet
        self.pet_frame = tk.Frame(self.root, bg='SystemButtonFace')
        self.pet_frame.pack()
        
        # Initialize all state variables
        self._initialize_state_variables()
        print("Variables initialized")
        
        try:
            print("Loading images...")
            self._load_images()
            print("Images loaded successfully")
        except Exception as e:
            print(f"Error loading images: {e}")
            self._create_error_label()

        print("Setting up UI elements...")
        self.create_popup_menu()
        self._setup_bindings()
        self._initialize_windows()
        
        # Initialize reminders
        self.reminders = self.load_reminders()
        self.check_reminders()

    def _initialize_state_variables(self):
        """Initialize all state variables"""
        self._drag_data = {"x": 0, "y": 0, "dragging": False}
        self._popup_visible = False
        self._settings_window = None
        self._reminder_window = None
        self._current_reminder_label = None
        self._ignore_next_click = False
        self._popup_timer = None
        self._sleep_timer = None
        self._current_state = "normal"
        
        # Walking animation state
        self._walking = False
        self._walk_direction = 1  # 1 for right, -1 for left
        self._walk_distance = 0
        self._walk_frame = 1  # 1 or 2 for animation frame
        self._walk_timer = None
        
        # Pomodoro state
        self._pomodoro_active = False
        self._pomodoro_state = "inactive"
        self._pomodoro_time_left = 0
        self._pomodoro_sessions = 0
        self._pomodoro_timer = None
        
        # Initialize statistics
        self.stats = self.load_stats()

    def _load_images(self):
        """Load and resize all images"""
        self.pet_images = {}
        for state, filename in [
            ("normal", "pet.png"),
            ("hover", "petopen.png"),
            ("sleep", "petsleep.png"),
            ("walk1", "petwalk1.png"),
            ("walk2", "petwalk2.png")
        ]:
            print(f"Loading {filename}...")
            try:
                original_image = Image.open(filename)
                resized_image = original_image.resize(
                    (200, 200),
                    Image.Resampling.BICUBIC
                )
                self.pet_images[state] = ImageTk.PhotoImage(resized_image)
                
                # Create flipped versions for walking images
                if state in ["walk1", "walk2"]:
                    flipped_image = resized_image.transpose(Image.FLIP_LEFT_RIGHT)
                    self.pet_images[f"{state}_flipped"] = ImageTk.PhotoImage(flipped_image)
            except Exception as e:
                print(f"Warning: Could not load {filename}: {e}")
                # Use normal image as fallback for walking frames
                if state in ["walk1", "walk2"]:
                    self.pet_images[state] = self.pet_images["normal"]
                    self.pet_images[f"{state}_flipped"] = self.pet_images["normal"]
        
        print("Loading speech bubble...")
        bubble_image = Image.open("speechbubble.png")
        resized_bubble = bubble_image.resize(
            (250, 100),
            Image.Resampling.BICUBIC
        )
        self.speech_bubble_image = ImageTk.PhotoImage(resized_bubble)
        
        self.pet_label = tk.Label(
            self.pet_frame,
            image=self.pet_images["normal"],
            bg='SystemButtonFace'
        )
        self.pet_label.pack()

    def _create_error_label(self):
        """Create error label when image loading fails"""
        self.pet_label = tk.Label(
            self.pet_frame,
            text="ERROR",
            font=("Arial", 40),
            bg='SystemButtonFace'
        )
        self.pet_label.pack()

    def _setup_bindings(self):
        """Set up all event bindings"""
        # Bind mouse events
        self.pet_label.bind('<Button-1>', self.on_drag_start)
        self.pet_label.bind('<B1-Motion>', self.on_drag_motion)
        self.pet_label.bind('<ButtonRelease-1>', self.on_drag_stop)
        self.pet_label.bind('<Button-3>', self.show_reminders)
        self.pet_label.bind('<Double-Button-1>', self.show_popup)
        self.pet_label.bind('<Enter>', self.on_enter)
        self.pet_label.bind('<Leave>', self.on_leave)
        
        # Bind popup events
        self.popup.bind('<Enter>', self.reset_popup_timer)
        self.popup.bind('<Leave>', self.start_popup_timer)

    def _initialize_windows(self):
        """Initialize voice bubble and timer windows"""
        self._create_voice_bubble()
        self._create_timer_window()

    def _create_voice_bubble(self):
        """Create the voice bubble window"""
        self.voice_bubble = tk.Toplevel(self.root)
        self.voice_bubble.withdraw()
        self.voice_bubble.overrideredirect(True)
        self.voice_bubble.attributes('-topmost', True)
        self.voice_bubble.attributes('-alpha', 1.0)
        self.voice_bubble.attributes('-transparentcolor', 'SystemButtonFace')
        self.voice_bubble.configure(bg='SystemButtonFace')
        
        bubble_frame = tk.Frame(self.voice_bubble, bg='SystemButtonFace')
        bubble_frame.pack(fill=tk.BOTH, expand=True)
        
        self.bubble_label = tk.Label(
            bubble_frame,
            image=self.speech_bubble_image,
            bg='SystemButtonFace'
        )
        self.bubble_label.pack()
        
        self.voice_label = tk.Label(
            bubble_frame,
            text="",
            wraplength=200,
            font=('Arial', 12, 'bold'),
            bg='#bdbdbd',  # Light gray background
            fg='black'
        )
        self.voice_label.place(relx=0.5, rely=0.5, anchor="center")

    def _create_timer_window(self):
        """Create the timer window"""
        self.timer_window = tk.Toplevel(self.root)
        self.timer_window.withdraw()
        self.timer_window.overrideredirect(True)
        self.timer_window.attributes('-topmost', True)
        self.timer_window.configure(bg='white')
        
        timer_frame = ttk.Frame(self.timer_window)
        timer_frame.pack(fill=tk.BOTH, expand=True)
        
        self.timer_label = ttk.Label(
            timer_frame,
            text="",
            font=('Arial', 16, 'bold'),
            background='white'
        )
        self.timer_label.pack(padx=10, pady=(5, 0))
        
        ttk.Button(
            timer_frame,
            text="✖",
            width=3,
            command=self.stop_pomodoro
        ).pack(pady=(0, 5))

        # Bind cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup_and_exit)

    def is_already_running(self):
        """Check if another instance is running"""
        return os.path.exists(self.LOCK_FILE)

    def cleanup_previous_instance(self):
        """Kill the previous instance"""
        try:
            # Try to remove the lock file
            if os.path.exists(self.LOCK_FILE):
                os.remove(self.LOCK_FILE)
            
            # On Windows, use taskkill to force close previous Python instances
            if os.name == 'nt':  # Windows
                os.system('taskkill /F /IM python.exe /T')
        except Exception as e:
            print(f"Error cleaning up previous instance: {e}")

    def create_lock_file(self):
        """Create a lock file to indicate this instance is running"""
        try:
            with open(self.LOCK_FILE, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            print(f"Error creating lock file: {e}")

    def cleanup_and_exit(self):
        """Clean up resources before exiting"""
        try:
            if os.path.exists(self.LOCK_FILE):
                os.remove(self.LOCK_FILE)
            if self._walk_timer:
                self.root.after_cancel(self._walk_timer)
            if self.timer_window:
                self.timer_window.destroy()
            if self.root:
                self.root.quit()
                self.root.destroy()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            sys.exit(0)

    def reset_popup_timer(self, event=None):
        """Reset the popup timer when mouse enters popup"""
        if self._popup_timer:
            self.root.after_cancel(self._popup_timer)
            self._popup_timer = None

    def start_popup_timer(self, event=None):
        """Start the timer to hide popup after 10 seconds"""
        self.reset_popup_timer()
        self._popup_timer = self.root.after(10000, self.hide_popup)

    def show_popup(self, event):
        """Show the popup menu and start the timer"""
        if not self._popup_visible and not self._drag_data["dragging"]:
            x = self.root.winfo_x()
            y = self.root.winfo_y() - 50
            self.popup.geometry(f'+{x}+{y}')
            self.popup.deiconify()
            self._popup_visible = True
            
            # Update Pomodoro button text based on state
            if self._pomodoro_active:
                self.pomodoro_btn.configure(text="⏹")
            else:
                self.pomodoro_btn.configure(text="▶")

    def hide_popup(self, event=None):
        """Hide the popup menu"""
        if self._popup_visible:
            self.popup.withdraw()
            self._popup_visible = False
            self.reset_popup_timer()

    def handle_click(self, event):
        """Handle clicks on the main window"""
        if not self._ignore_next_click and self._popup_visible:
            # Check if click is outside popup
            px = self.popup.winfo_x()
            py = self.popup.winfo_y()
            pw = self.popup.winfo_width()
            ph = self.popup.winfo_height()
            
            mouse_x = self.root.winfo_pointerx()
            mouse_y = self.root.winfo_pointery()
            
            if not (px <= mouse_x <= px + pw and py <= mouse_y <= py + ph):
                self.hide_popup()
        self._ignore_next_click = False

    def handle_popup_click(self, event):
        """Handle clicks on the popup menu"""
        self._ignore_next_click = True
        return "break"  # Prevent event propagation

    def on_settings_click(self):
        """Handle settings button click"""
        self._ignore_next_click = True
        self.toggle_settings()

    def on_add_reminder_click(self):
        """Handle add reminder button click"""
        self._ignore_next_click = True
        self.add_reminder()

    def load_reminders(self):
        try:
            with open('reminders.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_reminders(self):
        with open('reminders.json', 'w') as f:
            json.dump(self.reminders, f)

    def on_enter(self, event):
        """When mouse enters pet area"""
        self.update_pet_state("hover")
        if self.reminders:  # Only show bubble if there are reminders
            latest = self.reminders[-1]  # Get the most recent reminder
            self.voice_label.configure(text=latest['text'])
            self.show_voice_bubble()
        self.reset_sleep_timer()

    def on_leave(self, event):
        """When mouse leaves pet area"""
        if self._current_state != "sleep":
            self.update_pet_state("normal")
        self.hide_voice_bubble()
        self.start_sleep_timer()

    def show_latest_reminder(self):
        """Show the latest reminder above the pet"""
        if self.reminders and not self._current_reminder_label:
            # Change pet state to open mouth when showing reminder
            self.update_pet_state("hover")
            self.show_voice_bubble()

    def delete_reminder(self, reminder):
        """Delete a specific reminder"""
        if reminder in self.reminders:
            self.reminders.remove(reminder)
            self.save_reminders()
            if self._current_reminder_label:
                self._current_reminder_label.destroy()
                self._current_reminder_label = None
            if self.reminders:  # Show next reminder if available
                self.show_latest_reminder()

    def toggle_settings(self):
        """Toggle settings window"""
        if self._settings_window:
            self._settings_window.destroy()
            self._settings_window = None
        else:
            self._settings_window = tk.Toplevel(self.root)
            self._settings_window.title("Settings")
            self._settings_window.attributes('-topmost', True)
            
            ttk.Button(
                self._settings_window,
                text="Toggle Draw Over Windows",
                command=self.toggle_always_on_top
            ).pack(padx=10, pady=5)

    def toggle_always_on_top(self):
        """Toggle if pet draws over other windows"""
        current = self.root.attributes('-topmost')
        self.root.attributes('-topmost', not current)
        self.popup.attributes('-topmost', not current)
        if self._current_reminder_label:
            self._current_reminder_label.attributes('-topmost', not current)

    def add_reminder(self):
        """Create a new reminder with date and time"""
        if self._reminder_window:
            self._reminder_window.focus_force()
            return
            
        self._reminder_window = tk.Toplevel(self.root)
        self._reminder_window.title("Add Reminder")
        self._reminder_window.attributes('-topmost', True)
        
        frame = ttk.Frame(self._reminder_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Reminder text:").pack(pady=(0, 5))
        
        reminder_text = tk.Text(frame, width=40, height=4)
        reminder_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        reminder_text.focus()
        
        ttk.Label(frame, text="Due date and time:").pack(pady=(5, 0))
        
        # Add DateEntry for picking date
        due_datetime = DateEntry(frame, width=20)
        due_datetime.pack(pady=5)
        
        # Add time selection with AM/PM
        time_frame = ttk.Frame(frame)
        time_frame.pack(pady=5)
        
        # Initialize with 12-hour format
        hour_var = tk.StringVar(value="12")
        minute_var = tk.StringVar(value="00")
        ampm_var = tk.StringVar(value="AM")
        
        # Hour spinbox (1-12)
        hour_spinbox = ttk.Spinbox(
            time_frame,
            from_=1,
            to=12,
            width=2,
            format="%02.0f",
            textvariable=hour_var
        )
        hour_spinbox.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        
        # Minute spinbox (00-59)
        minute_spinbox = ttk.Spinbox(
            time_frame,
            from_=0,
            to=59,
            width=2,
            format="%02.0f",
            textvariable=minute_var
        )
        minute_spinbox.pack(side=tk.LEFT, padx=2)
        
        # AM/PM toggle
        ampm_menu = ttk.OptionMenu(
            time_frame,
            ampm_var,
            "AM",
            "AM",
            "PM"
        )
        ampm_menu.pack(side=tk.LEFT, padx=5)
        
        def save_and_close(event=None):
            text = reminder_text.get("1.0", tk.END).strip()
            if text:
                # Convert 12-hour to 24-hour format
                hour = int(hour_var.get())
                minute = int(minute_var.get())
                
                # Adjust hour based on AM/PM
                if ampm_var.get() == "PM" and hour != 12:
                    hour += 12
                elif ampm_var.get() == "AM" and hour == 12:
                    hour = 0
                
                # Combine date and time
                date = due_datetime.get_date()
                due = datetime(
                    date.year,
                    date.month,
                    date.day,
                    hour,
                    minute
                )
                
                reminder = {
                    "text": text,
                    "due_datetime": due.strftime("%Y-%m-%d %H:%M"),
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                self.reminders.append(reminder)
                self.save_reminders()
                self.show_voice_bubble(text="Reminder set!")
            
            if self._reminder_window:
                self._reminder_window.destroy()
                self._reminder_window = None
            
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(
            button_frame,
            text="Save",
            command=save_and_close
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=lambda: self._reminder_window.destroy()
        ).pack(side=tk.LEFT, padx=5)
        
        self._reminder_window.protocol(
            "WM_DELETE_WINDOW",
            lambda: self.on_reminder_window_close()
        )

    def on_reminder_window_close(self):
        """Handle reminder window closing"""
        if self._reminder_window:
            self._reminder_window.destroy()
            self._reminder_window = None

    def show_reminders(self, event):
        """Show all reminders in a window"""
        reminders_window = tk.Toplevel(self.root)
        reminders_window.title("All Reminders")
        reminders_window.attributes('-topmost', True)
        
        # Add a frame with padding
        frame = ttk.Frame(reminders_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Add a label
        ttk.Label(frame, text="Your Reminders:").pack(pady=(0, 10))
        
        # Create a frame for the list
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        for reminder in self.reminders:
            reminder_frame = ttk.Frame(list_frame)
            reminder_frame.pack(fill=tk.X, pady=2)
            
            # Convert datetime to 12-hour format
            dt = datetime.strptime(
                reminder['due_datetime'],
                "%Y-%m-%d %H:%M"
            )
            hour = dt.hour
            ampm = "AM"
            
            if hour >= 12:
                ampm = "PM"
                if hour > 12:
                    hour -= 12
            elif hour == 0:
                hour = 12
            
            time_str = dt.strftime(f"%m/%d/%Y {hour:02d}:%M {ampm}")
            
            # Create reminder text label
            reminder_text = f"{time_str} - {reminder['text']}"
            ttk.Label(
                reminder_frame,
                text=reminder_text,
                wraplength=300
            ).pack(side=tk.LEFT)
            
            # Create delete button
            ttk.Button(
                reminder_frame,
                text="🗑️",
                width=3,
                command=lambda r=reminder: self.delete_reminder(r)
            ).pack(side=tk.RIGHT)

    def check_reminders(self):
        """Check for due reminders"""
        current_time = datetime.now()
        # Use slice copy to allow modification during iteration
        for reminder in self.reminders[:]:
            reminder_time = datetime.strptime(
                reminder['due_datetime'],
                "%Y-%m-%d %H:%M"
            )
            if current_time >= reminder_time:
                self.show_notification(f"REMINDER: {reminder['text']}")
                # Ask if user wants to dismiss or snooze
                self.show_reminder_actions(reminder)
        
        # Check again in 30 seconds
        self.root.after(30000, self.check_reminders)

    def show_notification(self, message):
        notification = tk.Toplevel(self.root)
        notification.attributes('-topmost', True)
        ttk.Label(notification, text=message).pack()
        notification.after(5000, notification.destroy)  # Close after 5 seconds

    def on_drag_start(self, event):
        """Begin drag of the pet"""
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self._drag_data["dragging"] = False
        self.update_pet_state("normal")
        self.reset_sleep_timer()
        if self._current_reminder_label:
            self._current_reminder_label.destroy()
            self._current_reminder_label = None

    def on_drag_motion(self, event):
        """Handle dragging of the pet"""
        if self._drag_data["dragging"]:
            x = self.root.winfo_x() + (event.x - self._drag_data["x"])
            y = self.root.winfo_y() + (event.y - self._drag_data["y"])
            self.root.geometry(f"+{x}+{y}")
            
            # Move timer window if visible
            if self._pomodoro_active:
                timer_x = x + 50
                timer_y = y - 50
                self.timer_window.geometry(f'+{timer_x}+{timer_y}')
            
            # Move voice bubble if visible
            if self.voice_bubble.winfo_viewable():
                bubble_x = x + 180
                bubble_y = y + 40
                self.voice_bubble.geometry(f'+{bubble_x}+{bubble_y}')
        else:
            # Start dragging if moved more than 5 pixels
            dx = abs(event.x - self._drag_data["x"])
            dy = abs(event.y - self._drag_data["y"])
            if dx > 5 or dy > 5:
                self._drag_data["dragging"] = True

    def on_drag_stop(self, event):
        """End drag of the pet"""
        self._drag_data["dragging"] = False

    def update_pet_state(self, state):
        """Update the pet's image based on its state"""
        if state != self._current_state and state in self.pet_images:
            self._current_state = state
            self.pet_label.configure(image=self.pet_images[state])
            
            # Show/hide voice bubble based on state
            if state == "hover" and self.reminders:
                latest = self.reminders[-1]  # Get the most recent reminder
                self.voice_label.configure(text=latest['text'])
                self.show_voice_bubble()
            elif state != "hover":
                self.hide_voice_bubble()

    def show_voice_bubble(self, text=None):
        """Show the voice bubble with optional text or latest reminder"""
        if text:
            bubble_text = text
        elif self.reminders:
            bubble_text = self.reminders[-1]['text']
        else:
            return  # Don't show bubble if no text and no reminders
            
        self.voice_label.configure(text=bubble_text)
        
        # Position the bubble to the right of the pet
        x = self.root.winfo_x() + 180
        y = self.root.winfo_y() + 40
        self.voice_bubble.geometry(f'+{x}+{y}')
        self.voice_bubble.deiconify()

    def hide_voice_bubble(self):
        """Hide the voice bubble"""
        self.voice_bubble.withdraw()

    def start_sleep_timer(self):
        """Start the timer to put the pet to sleep"""
        if self._sleep_timer:
            self.root.after_cancel(self._sleep_timer)
        # Set timer for 30 seconds
        self._sleep_timer = self.root.after(
            30000,
            self.sleep_pet
        )

    def reset_sleep_timer(self):
        """Reset the sleep timer"""
        if self._sleep_timer:
            self.root.after_cancel(self._sleep_timer)
            self._sleep_timer = None
        if self._current_state == "sleep":
            self.update_pet_state("normal")
        self.start_sleep_timer()

    def sleep_pet(self):
        """Put the pet to sleep"""
        self.update_pet_state("sleep")
        self.hide_voice_bubble()

    def load_stats(self):
        """Load Pomodoro statistics"""
        try:
            with open("pomodoro_stats.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "total_work_sessions": 0,
                "total_work_minutes": 0,
                "total_break_minutes": 0,
                "daily_sessions": {}
            }

    def save_stats(self):
        """Save Pomodoro statistics"""
        with open("pomodoro_stats.json", "w") as f:
            json.dump(self.stats, f)

    def start_pomodoro(self):
        """Start a Pomodoro session"""
        if not self._pomodoro_active:
            self._pomodoro_active = True
            self._pomodoro_state = "work"
            self._pomodoro_time_left = self.POMODORO_WORK * 60
            self._pomodoro_sessions = 0
            self.update_pomodoro_timer()
            self.update_pet_state("work")
            self.show_notification("Pomodoro started! Time to focus!")

    def update_pomodoro_timer(self):
        """Update Pomodoro timer"""
        if not self._pomodoro_active:
            return

        if self._pomodoro_time_left > 0:
            # Update display and decrement timer
            self.update_timer_display(
                self._pomodoro_state,
                self._pomodoro_time_left
            )
            self._pomodoro_time_left -= 1
            # Schedule next update in 1 second
            self._pomodoro_timer = self.root.after(
                1000,
                self.update_pomodoro_timer
            )
        else:
            self.handle_pomodoro_completion()

    def handle_pomodoro_completion(self):
        """Handle completion of a Pomodoro interval"""
        if self._pomodoro_state == "work":
            self._pomodoro_sessions += 1
            self.stats["total_work_sessions"] += 1
            self.stats["total_work_minutes"] += self.POMODORO_WORK
            
            today = datetime.now().strftime("%Y-%m-%d")
            if today not in self.stats["daily_sessions"]:
                self.stats["daily_sessions"][today] = 0
            self.stats["daily_sessions"][today] += 1
            
            if self._pomodoro_sessions % 4 == 0:
                self._pomodoro_state = "long_break"
                self._pomodoro_time_left = self.POMODORO_LONG_BREAK * 60
                self.show_notification("Great work! Time for a long break!")
            else:
                self._pomodoro_state = "break"
                self._pomodoro_time_left = self.POMODORO_BREAK * 60
                self.show_notification("Good job! Take a short break!")
        else:
            self._pomodoro_state = "work"
            self._pomodoro_time_left = self.POMODORO_WORK * 60
            self.show_notification("Break's over! Back to work!")
        
        self.update_pet_state(self._pomodoro_state)
        self.save_stats()
        self.update_pomodoro_timer()

    def stop_pomodoro(self):
        """Stop the Pomodoro timer"""
        if self._pomodoro_active:
            self._pomodoro_active = False
            if self._pomodoro_timer:
                self.root.after_cancel(self._pomodoro_timer)
            self.timer_window.withdraw()
            self.update_pet_state("normal")
            self.show_notification("Pomodoro session ended!")

    def show_reminder_actions(self, reminder):
        """Show actions for a due reminder"""
        action_window = tk.Toplevel(self.root)
        action_window.title("Reminder")
        action_window.attributes('-topmost', True)
        
        frame = ttk.Frame(action_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Show reminder text with word wrap
        ttk.Label(
            frame,
            text=reminder['text'],
            wraplength=300
        ).pack(pady=10)
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        def snooze_reminder():
            # Snooze for 5 minutes
            new_time = datetime.now() + timedelta(minutes=5)
            reminder['due_datetime'] = new_time.strftime("%Y-%m-%d %H:%M")
            self.save_reminders()
            action_window.destroy()
            self.show_notification("Reminder snoozed for 5 minutes")
        
        def dismiss_reminder():
            self.reminders.remove(reminder)
            self.save_reminders()
            action_window.destroy()
        
        ttk.Button(
            button_frame,
            text="Snooze (5 min)",
            command=snooze_reminder
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Dismiss",
            command=dismiss_reminder
        ).pack(side=tk.LEFT, padx=5)

    def show_stats(self):
        """Show Pomodoro statistics"""
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Pomodoro Stats")
        stats_window.attributes('-topmost', True)
        
        frame = ttk.Frame(stats_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            frame,
            text="Pomodoro Statistics",
            font=('Arial', 14, 'bold')
        ).pack(pady=10)
        
        # Get today's date for stats
        today = datetime.now().strftime("%Y-%m-%d")
        today_sessions = self.stats['daily_sessions'].get(today, 0)
        
        stats_text = f"""
Total Work Sessions: {self.stats['total_work_sessions']}
Total Work Minutes: {self.stats['total_work_minutes']}
Total Break Minutes: {self.stats['total_break_minutes']}

Today's Sessions: {today_sessions}
"""
        ttk.Label(frame, text=stats_text).pack(pady=10)
        
        ttk.Button(
            frame,
            text="Close",
            command=stats_window.destroy
        ).pack(pady=10)

    def update_timer_display(self, state, time_left):
        """Update the timer window with current state and time"""
        if not self._pomodoro_active:
            self.timer_window.withdraw()
            return

        mins, secs = divmod(time_left, 60)
        timer_text = f"{state.title()}\n{mins:02d}:{secs:02d}"
        self.timer_label.configure(text=timer_text)
        
        # Position timer above the pet
        x = self.root.winfo_x() + 50
        y = self.root.winfo_y() - 50
        self.timer_window.geometry(f'+{x}+{y}')
        self.timer_window.deiconify()

    def create_popup_menu(self):
        """Create the popup menu with all controls"""
        self.popup = tk.Toplevel(self.root)
        self.popup.withdraw()
        self.popup.overrideredirect(True)
        self.popup.attributes('-topmost', True)
        self.popup.configure(bg='SystemButtonFace')

        button_frame = ttk.Frame(self.popup)
        button_frame.pack(padx=2, pady=2)
        
        self.settings_btn = ttk.Button(button_frame, text="⚙️", width=3,
            command=self.on_settings_click)
        self.settings_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.add_reminder_btn = ttk.Button(button_frame, text="➕", width=3,
            command=self.on_add_reminder_click)
        self.add_reminder_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Create Pomodoro button with dynamic text
        self.pomodoro_btn = ttk.Button(button_frame, text="▶", width=3,
            command=self.toggle_pomodoro)
        self.pomodoro_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(button_frame, text="📊", width=3,
            command=self.show_stats).pack(side=tk.LEFT, padx=5, pady=5)

        # Add walking toggle button
        self.walk_btn = ttk.Button(button_frame, text="🚶", width=3,
            command=self.toggle_walking)
        self.walk_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.close_btn = ttk.Button(button_frame, text="❌", width=3,
            command=self.cleanup_and_exit)
        self.close_btn.pack(side=tk.LEFT, padx=5, pady=5)

    def toggle_pomodoro(self):
        """Toggle Pomodoro timer on/off"""
        if self._pomodoro_active:
            self.stop_pomodoro()
        else:
            self.start_pomodoro()
        self.popup.withdraw()
        self._popup_visible = False

    def toggle_walking(self):
        """Toggle the walking animation"""
        self._walking = not self._walking
        if self._walking:
            self.start_walking()
        else:
            self.stop_walking()
        self.popup.withdraw()
        self._popup_visible = False

    def start_walking(self):
        """Start the walking animation"""
        if not self._walking:
            return
        self._walk_direction = 1
        self._walk_distance = 0
        self._walk_frame = 1
        self.update_walking()

    def stop_walking(self):
        """Stop the walking animation"""
        if self._walk_timer:
            self.root.after_cancel(self._walk_timer)
            self._walk_timer = None
        self.update_pet_state("normal")

    def update_walking(self):
        """Update the walking animation"""
        if not self._walking:
            return

        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        pet_width = 200  # Width of the pet image

        # Update position
        current_x = self.root.winfo_x()
        new_x = current_x + (self.WALK_SPEED * self._walk_direction)
        self._walk_distance += self.WALK_SPEED

        # Check if we need to turn around at screen edges
        if new_x <= 0 or new_x >= screen_width - pet_width:
            self._walk_direction *= -1
            self._walk_distance = 0

        # Update position
        self.root.geometry(f"+{new_x}+{self.root.winfo_y()}")

        # Update animation frame with correct direction
        self._walk_frame = 3 - self._walk_frame  # Toggle between 1 and 2
        frame_key = f"walk{self._walk_frame}"
        if self._walk_direction < 0:
            frame_key += "_flipped"
        self.pet_label.configure(image=self.pet_images[frame_key])
        self.pet_label.image = self.pet_images[frame_key]

        # Schedule next update
        self._walk_timer = self.root.after(self.WALK_FRAME_DELAY, self.update_walking)

    def run(self):
        try:
            print("Positioning window...")
            # Position the pet at the bottom right of the screen
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            print(f"Screen dimensions: {screen_width}x{screen_height}")
            self.root.geometry(f'+{screen_width-250}+{screen_height-250}')
            print("Starting main loop...")
            self.root.mainloop()
        except Exception as e:
            print(f"Error during run: {e}")
        finally:
            self.cleanup_and_exit()

if __name__ == "__main__":
    try:
        print("Creating pet instance...")
        pet = DeskPet()
        print("Running pet...")
        pet.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        input("Press Enter to exit...")

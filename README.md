# Crystal Lizard Desktop Pet

A desktop pet application that helps you stay productive with Pomodoro timer and reminders!

## Features

- Interactive desktop pet that responds to your interactions
- Built-in Pomodoro timer for productivity
- Reminder system with notifications
- Auto-sleep when inactive
- Walking animation (requires walking animation images)
- Pomodoro statistics tracking
- Customizable settings

## Requirements

- Python 3.7 or higher
- Pillow (PIL) >= 10.0.0
- tkcalendar >= 1.6.1

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/crystal-lizard-desk-pet.git
cd crystal-lizard-desk-pet
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python desk_pet.py
```

## Image Requirements

The application requires the following images in the same directory:
- `pet.png` - Normal state
- `petopen.png` - Hover state
- `petsleep.png` - Sleep state
- `speechbubble.png` - Speech bubble background
- `petwalk1.png` and `petwalk2.png` (optional) - Walking animation frames

## Usage

### Basic Interactions
- Drag the pet to move it around
- Double-click to open the control menu
- Right-click to view reminders
- Hover over the pet to see the latest reminder

### Control Menu
- ⚙️ Settings - Toggle window behavior
- ➕ Add Reminder - Create a new reminder
- ▶/⏹ Pomodoro - Start/stop Pomodoro timer
- 📊 Stats - View Pomodoro statistics
- 🚶 Walking - Toggle walking animation
- ❌ Close - Exit the application

### Pomodoro Timer
- 25-minute work sessions
- 5-minute short breaks
- 15-minute long breaks after 4 sessions
- Automatic notifications

### Reminders
- Set reminders with date and time
- Snooze or dismiss notifications
- View all reminders in a list


## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Thanks to all contributors who help improve this project
- Inspired by desktop pet applications and productivity tools 

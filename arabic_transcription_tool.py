import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import speech_recognition as sr
from pydub import AudioSegment, silence
import pygame
import os
import threading
from PIL import Image, ImageTk
import webbrowser
import logging


play_icon_path = "path_to_icons/play_icon.png"
stop_icon_path = "path_to_icons/stop_icon.png"


def browse_file():
    # Define the action for the browse_file_button
    pass

def browse_output_folder():
    # Define the action for the browse_output_button
    pass

# Initialize segment counter
segment_counter = 0

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='transcription_tool.log',
    filemode='w'
)

# Initialize the main Tkinter window
root = tk.Tk()
root.title("Arabic Transcription Tool")
root.configure(bg="#28282e")
root.resizable(False, False)

# Frame Definitions
file_frame = tk.Frame(root, bg="#272727")
output_frame = tk.Frame(root, bg="#272727")
controls_frame = tk.Frame(root, bg="#272727")
transcription_frame = tk.Frame(root, bg="#272727")

def load_image(image_path):
    try:
        image = Image.open(image_path)
        return ImageTk.PhotoImage(image)
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None

def get_resource_path(filename):
    path = os.path.join(os.path.dirname(__file__), filename)
    if not os.path.isfile(path):
        print(f"Warning: File {path} does not exist.")
    return path

# Load images
play_icon = load_image(get_resource_path("play_icon.png"))
stop_icon = load_image(get_resource_path("stop_icon.png"))
paypal_logo = load_image(get_resource_path("paypal_logo.png"))
icon_path = get_resource_path("my_icon.ico")

# Initialize pygame mixer
pygame.mixer.init()

# Modernized colors
bg_color = "#28282e"
fg_color = "#e0e0e0"
accent_color = "#e64b3d"
button_color = "#17181a"
hover_color = "#444444"
entry_bg = "#17181a"
entry_fg = "#e0e0e0"
toggle_color = "#17181a"

class Tooltip:
    def __init__(self, widget, text, offset_x=10, offset_y=10):
        self.widget = widget
        self.text = text
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
        self.widget.bind("<Motion>", self.update_tooltip_position)

    def show_tooltip(self, event):
        if self.tooltip:
            return
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{event.x_root + self.offset_x}+{event.y_root + self.offset_y}")
        label = tk.Label(self.tooltip, text=self.text, background="lightyellow", relief="solid", borderwidth=1, font=("Segoe UI", 10))
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def update_tooltip_position(self, event):
        if self.tooltip:
            self.tooltip.wm_geometry(f"+{event.x_root + self.offset_x}+{event.y_root + self.offset_y}")

def on_enter(e):
    e.widget['background'] = hover_color

def on_leave(e):
    e.widget['background'] = button_color

def run_transcription():
    global segment_counter

    audio_file = entry_file_path.get()
    output_folder = entry_output_folder.get()

    if not audio_file or not output_folder:
        messagebox.showerror("Error", "Please select both audio file and output folder.")
        return

    # Start the progress bar
    progress_bar.start()
    root.update_idletasks()

    # Define the path for the output .srt file
    base_name = os.path.basename(audio_file).replace('.wav', '_transcription.srt')
    output_file = os.path.join(output_folder, base_name)

    # Load and preprocess audio file
    audio = AudioSegment.from_wav(audio_file)
    
    # Get sensitivity parameters from the GUI
    silence_thresh = audio.dBFS - float(entry_silence_thresh.get())
    min_silence_len = int(entry_min_silence_len.get())
    segments = silence.split_on_silence(audio, silence_thresh=silence_thresh, min_silence_len=min_silence_len, keep_silence=250)

    recognizer = sr.Recognizer()
    transcriptions = []

    # Initialize start time
    start_time = 0

    for i, segment in enumerate(segments):
        segment_file = "temp_segment.wav"
        segment.export(segment_file, format="wav")

        with sr.AudioFile(segment_file) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language='ar')
            except sr.UnknownValueError:
                text = "[Unrecognized Speech]"
            except sr.RequestError as e:
                text = f"[Error: {e}]"
        
        # Calculate segment duration
        end_time = start_time + len(segment) / 1000

        # Format times for SRT file
        start_time_str = format_time(start_time)
        end_time_str = format_time(end_time)
        
        transcriptions.append(f"{i+1}\n{start_time_str} --> {end_time_str}\n{text}\n\n")


        # Update start time for next segment
        start_time = end_time

        os.remove(segment_file)

        # Update the segment counter label in real-time
        segment_counter = i + 1
        update_segment_counter_label()

    # Save transcription to .srt file
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.writelines(transcriptions)
        messagebox.showinfo("Success", f"Transcription completed. File saved to {output_file}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

    # Final update of segment counter label
    segment_counter = len(segments)
    update_segment_counter_label()

    # Stop the progress bar
    progress_bar.stop()
    root.update_idletasks()

def format_time(seconds):
    """Format seconds as SRT timestamp."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def update_segment_counter_label():
    label_text = translations[current_language]['segment_counter_label'].format(segment_counter)
    segment_counter_label.config(text=label_text)
    root.update_idletasks()

def browse_file():
    file_path = filedialog.askopenfilename(
        title="Select Audio File",
        filetypes=(("WAV files", "*.wav"), ("All files", "*.*"))
    )
    if file_path:
        entry_file_path.delete(0, tk.END)
        entry_file_path.insert(0, file_path)
        load_audio_file(file_path)

def browse_output_folder():
    folder_path = filedialog.askdirectory(title="Select Output Folder")
    if folder_path:
        entry_output_folder.delete(0, tk.END)
        entry_output_folder.insert(0, folder_path)

def start_transcription():
    threading.Thread(target=run_transcription).start()

def load_audio_file(file_path):
    pygame.mixer.music.load(file_path)

def play_audio():
    pygame.mixer.music.play()

def stop_audio():
    pygame.mixer.music.stop()

def open_donation_link():
    webbrowser.open("https://paypal.me/azizalkharraz?country.x=BH&locale.x=en_US")

def toggle_language():
    global current_language
    current_language = 'ar' if current_language == 'en' else 'en'
    update_ui_text()

def update_ui_text():
    transcribe_button.config(text=translations[current_language]['transcribe'])
    browse_file_button.config(text=translations[current_language]['browse_file_button'])
    browse_output_button.config(text=translations[current_language]['browse_folder_button'])
    file_path_label.config(text=translations[current_language]['file_path_label'])
    output_folder_label.config(text=translations[current_language]['output_folder_label'])
    silence_threshold_label.config(text=translations[current_language]['silence_threshold_label'])
    min_silence_length_label.config(text=translations[current_language]['min_silence_length_label'])
    donate_button.config(text=translations[current_language]['donate_button'])
    toggle_button.config(text=translations[current_language]['toggle_language'])
    update_segment_counter_label()

    # Update tooltips
    Tooltip(entry_file_path, translations[current_language]['file_path_tooltip'])
    Tooltip(entry_output_folder, translations[current_language]['output_folder_tooltip'])
    Tooltip(entry_silence_thresh, translations[current_language]['silence_threshold_tooltip'])
    Tooltip(entry_min_silence_len, translations[current_language]['min_silence_length_tooltip'])
    Tooltip(transcribe_button, translations[current_language]['transcribe_button_tooltip'])
    Tooltip(donate_button, translations[current_language]['donate_button_tooltip'])
    Tooltip(play_button, translations[current_language]['play_button_tooltip'])
    Tooltip(stop_button, translations[current_language]['stop_button_tooltip'])

def set_silence_threshold(value):
    entry_silence_thresh.delete(0, tk.END)
    entry_silence_thresh.insert(0, value)

def set_min_silence_length(value):
    entry_min_silence_len.delete(0, tk.END)
    entry_min_silence_len.insert(0, value)

# Define translations
translations = {
    'en': {
        'transcribe': 'Transcribe',
        'browse_file_button': 'Select File',
        'browse_folder_button': 'Select Folder',
        'file_path_label': 'Audio File Path:',
        'output_folder_label': 'Output Folder:',
        'silence_threshold_label': 'Silence Threshold (dB):',
        'min_silence_length_label': 'Min Silence Length (ms):',
        'donate_button': 'Donate',
        'toggle_language': 'العربية',
        'file_path_tooltip': 'Select the audio file you want to transcribe.',
        'output_folder_tooltip': 'Select the folder where the transcription will be saved.',
        'silence_threshold_tooltip': 'Set the silence threshold in decibels.',
        'min_silence_length_tooltip': 'Set the minimum length of silence in milliseconds.',
        'transcribe_button_tooltip': 'Start the transcription process.',
        'donate_button_tooltip': 'Support the development of this tool.',
        'play_button_tooltip': 'Play the selected audio file.',
        'stop_button_tooltip': 'Stop playback of the audio file.',
        'segment_counter_label': 'Segments Processed: {}'
    },
    'ar': {
        'transcribe': 'ترجمة',
        'browse_file_button': 'إختار الملف',
        'browse_folder_button': 'إختار المجلد',
        'file_path_label': 'مسار ملف الصوت:',
        'output_folder_label': 'مجلد الإخراج:',
        'silence_threshold_label': 'عَتَبة الصمت (ديسيبل):',
        'min_silence_length_label': 'أقل طول للصمت (مللي ثانية):',
        'donate_button': 'تبرع',
        'toggle_language': 'English',
        'file_path_tooltip': 'اختر ملف الصوت الذي تريد نسخه.',
        'output_folder_tooltip': 'اختر المجلد الذي سيتم حفظ النسخ فيه.',
        'silence_threshold_tooltip': 'حدد عتبة الصمت بالديسيبل.',
        'min_silence_length_tooltip': 'حدد الحد الأدنى لطول الصمت بالمللي ثانية.',
        'transcribe_button_tooltip': 'ابدأ عملية النسخ.',
        'donate_button_tooltip': 'ادعم تطوير هذه الأداة.',
        'play_button_tooltip': 'تشغيل ملف الصوت المحدد.',
        'stop_button_tooltip': 'إيقاف تشغيل ملف الصوت.',
        'segment_counter_label': 'عدد القطع المعالجة: {}'
    }
}

current_language = 'en'

# Layout Configuration
file_frame.pack(padx=10, pady=10, fill='x')
output_frame.pack(padx=10, pady=10, fill='x')
controls_frame.pack(padx=10, pady=10, fill='x')
transcription_frame.pack(padx=10, pady=10, fill='x')

# Define a consistent width for the buttons
entry_width = 20  # Adjust this value as needed
button_width = 15  # Adjust this value as needed
label_width = 20  # Width for labels (adjust to fit the text properly)

# Configure grid columns for controls_frame
controls_frame.grid_columnconfigure(0, weight=0)  # Column 0 should not stretch
controls_frame.grid_columnconfigure(1, weight=1)  # Column 1 should expand to fill available space
controls_frame.grid_columnconfigure(2, weight=0)  # Column 2 should not stretch


# File frame widgets
file_path_label = tk.Label(file_frame, text=translations[current_language]['file_path_label'], bg=bg_color, fg=fg_color, font=("Arial", 10, "bold"), width=label_width, anchor='w')
file_path_label.grid(row=0, column=0, sticky='w')
entry_file_path = tk.Entry(file_frame, width=entry_width, bg=entry_bg, fg=entry_fg)
entry_file_path.grid(row=0, column=1, padx=5, sticky='ew')
browse_file_button = tk.Button(file_frame, text=translations[current_language]['browse_file_button'], command=browse_file, bg=button_color, fg=fg_color, font=("Arial", 10, "bold"), width=button_width)
browse_file_button.grid(row=0, column=2, padx=5, sticky='ew')
Tooltip(entry_file_path, translations[current_language]['file_path_tooltip'])

# Output frame widgets
output_folder_label = tk.Label(output_frame, text=translations[current_language]['output_folder_label'], bg=bg_color, fg=fg_color, font=("Arial", 10, "bold"), width=label_width, anchor='w')
output_folder_label.grid(row=0, column=0, sticky='w')
entry_output_folder = tk.Entry(output_frame, width=entry_width, bg=entry_bg, fg=entry_fg)
entry_output_folder.grid(row=0, column=1, padx=5, sticky='ew')
browse_output_button = tk.Button(output_frame, text=translations[current_language]['browse_folder_button'], command=browse_output_folder, bg=button_color, fg=fg_color, font=("Arial", 10, "bold"), width=button_width)
browse_output_button.grid(row=0, column=2, padx=5, sticky='ew')
Tooltip(entry_output_folder, translations[current_language]['output_folder_tooltip'])

# Controls frame widgets
silence_threshold_label = tk.Label(controls_frame, text=translations[current_language]['silence_threshold_label'], bg=bg_color, fg=fg_color, font=("Arial", 10, "bold"))
silence_threshold_label.grid(row=0, column=0, sticky='w')
entry_silence_thresh = tk.Entry(controls_frame, width=5, bg=entry_bg, fg=entry_fg)
entry_silence_thresh.grid(row=0, column=1, padx=5)
entry_silence_thresh.insert(0, '30')  # Set default value for silence threshold

min_silence_length_label = tk.Label(controls_frame, text=translations[current_language]['min_silence_length_label'], bg=bg_color, fg=fg_color, font=("Arial", 10, "bold"))
min_silence_length_label.grid(row=1, column=0, sticky='w')
entry_min_silence_len = tk.Entry(controls_frame, width=5, bg=entry_bg, fg=entry_fg)
entry_min_silence_len.grid(row=1, column=1, padx=5)
entry_min_silence_len.insert(0, '500')  # Set default value for minimum silence length


# Value suggestions
suggestion_values = {
    'silence_threshold': [30, 40, 50],
    'min_silence_length': [1000, 500, 250]
}
suggestion_labels = {
    'silence_threshold': ['Moderate', 'Quiet', 'Faint'],
    'min_silence_length': ['Slow', 'Subtle', 'Fast']
}


# Set a fixed width for all suggestion buttons
button_width = 10  # Adjust the width value as needed

for idx, value in enumerate(suggestion_values['silence_threshold']):
    button = tk.Button(controls_frame, text=suggestion_labels['silence_threshold'][idx], command=lambda v=value: set_silence_threshold(v), bg=toggle_color, fg=fg_color, width=button_width)
    button.grid(row=0, column=2+idx, padx=5)

for idx, value in enumerate(suggestion_values['min_silence_length']):
    button = tk.Button(controls_frame, text=suggestion_labels['min_silence_length'][idx], command=lambda v=value: set_min_silence_length(v), bg=toggle_color, fg=fg_color, width=button_width)
    button.grid(row=1, column=2+idx, padx=5)

transcribe_button = tk.Button(controls_frame, text=translations[current_language]['transcribe'], command=start_transcription, bg=accent_color, fg=fg_color, font=("Arial", 10, "bold"), width=button_width)
transcribe_button.grid(row=2, column=1, columnspan=3, pady=10)  # Should expand to fill available space
Tooltip(transcribe_button, translations[current_language]['transcribe_button_tooltip'])

play_button = tk.Button(controls_frame, image=play_icon, command=play_audio, bg=button_color, fg=fg_color)
play_button.grid(row=2, column=0, padx=(0, 2), pady=5, sticky='ew')  # Ensure proper padding
stop_button = tk.Button(controls_frame, image=stop_icon, command=stop_audio, bg=button_color, fg=fg_color)
stop_button.grid(row=2, column=1, padx=(2, 0), pady=5, sticky='ew')  # Ensure proper padding
Tooltip(play_button, translations[current_language]['play_button_tooltip'])
Tooltip(stop_button, translations[current_language]['stop_button_tooltip'])

# Transcription frame widgets
segment_counter_label = tk.Label(transcription_frame, text=translations[current_language]['segment_counter_label'].format(segment_counter), bg=bg_color, fg=fg_color, font=("Arial", 10, "bold"))
segment_counter_label.pack(side=tk.LEFT, padx=5)

donate_button = tk.Button(transcription_frame, text=translations[current_language]['donate_button'], command=open_donation_link, bg=accent_color, fg=fg_color, font=("Arial", 10, "bold"), width=button_width)
donate_button.pack(side=tk.RIGHT, padx=5)
Tooltip(donate_button, translations[current_language]['donate_button_tooltip'])

toggle_button = tk.Button(transcription_frame, text=translations[current_language]['toggle_language'], command=toggle_language, bg=toggle_color, fg=fg_color, font=("Arial", 10, "bold"), width=button_width)
toggle_button.pack(side=tk.RIGHT, padx=5)

progress_bar = ttk.Progressbar(controls_frame, orient='horizontal', length=300, mode='indeterminate')
progress_bar.grid(row=3, column=0, columnspan=5, pady=10)

update_ui_text()

# Set icon and run main loop
if icon_path:
    root.iconbitmap(icon_path)

root.mainloop()
#!/usr/bin/env python3
"""
Video Trimmer Application
A GUI application for trimming video files (.mp4, .ts, etc.) from start or end.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
from moviepy import VideoFileClip
import threading
from pathlib import Path
from ffmpeg_trimmer import FFmpegTrimmer


class VideoTrimmer:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Trimmer")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Variables
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.trim_duration = tk.StringVar(value="10")
        self.trim_from_start = tk.BooleanVar(value=True)
        self.video_duration = tk.StringVar(value="No video loaded")
        self.use_ffmpeg = tk.BooleanVar(value=True)
        self.ffmpeg_available = tk.BooleanVar(value=False)
        self.verbose_mode = tk.BooleanVar(value=False)
        
        # Initialize FFmpeg trimmer
        self.ffmpeg_trimmer = FFmpegTrimmer()
        self.ffmpeg_available.set(self.ffmpeg_trimmer.check_ffmpeg_available())
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Input file selection
        ttk.Label(main_frame, text="Input Video:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.input_file, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_input_file).grid(row=0, column=2, pady=5)
        
        # Video info
        ttk.Label(main_frame, text="Duration:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, textvariable=self.video_duration).grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        
        # Output file selection
        ttk.Label(main_frame, text="Output Video:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_file, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_output_file).grid(row=2, column=2, pady=5)
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20)
        
        # Trim options
        options_frame = ttk.LabelFrame(main_frame, text="Trim Options", padding="10")
        options_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        options_frame.columnconfigure(1, weight=1)
        
        # Duration input
        ttk.Label(options_frame, text="Duration to trim (seconds):").grid(row=0, column=0, sticky=tk.W, pady=5)
        duration_frame = ttk.Frame(options_frame)
        duration_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        ttk.Entry(duration_frame, textvariable=self.trim_duration, width=10).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(duration_frame, text="seconds").grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # Trim direction
        ttk.Label(options_frame, text="Trim from:").grid(row=1, column=0, sticky=tk.W, pady=5)
        direction_frame = ttk.Frame(options_frame)
        direction_frame.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Radiobutton(direction_frame, text="Start", variable=self.trim_from_start, value=True).grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(direction_frame, text="End", variable=self.trim_from_start, value=False).grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # Engine selection
        ttk.Label(options_frame, text="Engine:").grid(row=2, column=0, sticky=tk.W, pady=5)
        engine_frame = ttk.Frame(options_frame)
        engine_frame.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ffmpeg_check = ttk.Checkbutton(engine_frame, text="Use FFmpeg (faster)", 
                                     variable=self.use_ffmpeg, state='normal' if self.ffmpeg_available.get() else 'disabled')
        ffmpeg_check.grid(row=0, column=0, sticky=tk.W)
        
        if not self.ffmpeg_available.get():
            ttk.Label(engine_frame, text="(FFmpeg not found)", foreground='red').grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # Verbose mode option
        ttk.Label(options_frame, text="Options:").grid(row=3, column=0, sticky=tk.W, pady=5)
        options_sub_frame = ttk.Frame(options_frame)
        options_sub_frame.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        verbose_check = ttk.Checkbutton(options_sub_frame, text="Verbose output", 
                                      variable=self.verbose_mode)
        verbose_check.grid(row=0, column=0, sticky=tk.W)
        
        # Preview section
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding="10")
        preview_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        preview_frame.columnconfigure(0, weight=1)
        
        self.preview_text = tk.Text(preview_frame, height=6, width=70, wrap=tk.WORD)
        self.preview_text.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.preview_text.configure(yscrollcommand=scrollbar.set)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="Update Preview", command=self.update_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Trim Video", command=self.trim_video).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready")
        self.status_label.grid(row=8, column=0, columnspan=3, pady=5)
        
        # Console output area (hidden by default, shown in verbose mode)
        self.console_frame = ttk.LabelFrame(main_frame, text="Console Output", padding="5")
        self.console_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        self.console_frame.columnconfigure(0, weight=1)
        
        self.console_text = tk.Text(self.console_frame, height=8, width=70, wrap=tk.WORD, state=tk.DISABLED)
        self.console_text.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        
        console_scrollbar = ttk.Scrollbar(self.console_frame, orient=tk.VERTICAL, command=self.console_text.yview)
        console_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.console_text.configure(yscrollcommand=console_scrollbar.set)
        
        # Hide console by default
        self.console_frame.grid_remove()
        
    def browse_input_file(self):
        """Open file dialog to select input video file."""
        filetypes = [
            ("Video files", "*.mp4 *.ts *.avi *.mov *.mkv *.wmv *.flv *.webm"),
            ("MP4 files", "*.mp4"),
            ("TS files", "*.ts"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select input video file",
            filetypes=filetypes
        )
        
        if filename:
            self.input_file.set(filename)
            self.load_video_info()
            self.auto_generate_output_filename()
            
    def browse_output_file(self):
        """Open file dialog to select output video file."""
        filetypes = [
            ("MP4 files", "*.mp4"),
            ("TS files", "*.ts"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.asksaveasfilename(
            title="Save output video as",
            filetypes=filetypes,
            defaultextension=".mp4"
        )
        
        if filename:
            self.output_file.set(filename)
            
    def load_video_info(self):
        """Load video information and display duration."""
        try:
            input_path = self.input_file.get()
            if not input_path or not os.path.exists(input_path):
                return
                
            self.status_label.config(text="Loading video info...")
            self.root.update()
            
            # Try FFmpeg first if available, fallback to MoviePy
            if self.ffmpeg_available.get():
                try:
                    video_info = self.ffmpeg_trimmer.get_video_info(input_path)
                    duration = video_info['duration']
                    codec_info = f" ({video_info['codec']})"
                except Exception:
                    # Fallback to MoviePy if FFmpeg fails
                    video = VideoFileClip(input_path)
                    duration = video.duration
                    video.close()
                    codec_info = ""
            else:
                # Use MoviePy
                video = VideoFileClip(input_path)
                duration = video.duration
                video.close()
                codec_info = ""
            
            # Format duration
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = duration % 60
            
            if hours > 0:
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:06.2f}"
            else:
                duration_str = f"{minutes:02d}:{seconds:06.2f}"
                
            self.video_duration.set(f"{duration_str} ({duration:.2f} seconds){codec_info}")
            self.status_label.config(text="Video loaded successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load video: {str(e)}")
            self.status_label.config(text="Error loading video")
            
    def _sanitize_filename(self, filename):
        """Sanitize filename by removing invalid characters."""
        # Remove or replace invalid characters for filesystem
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, '_', filename)
        return sanitized
    
    def _show_console(self):
        """Show console output area."""
        self.console_frame.grid()
        self.root.geometry("600x700")  # Make window taller
        
    def _hide_console(self):
        """Hide console output area."""
        self.console_frame.grid_remove()
        self.root.geometry("600x500")  # Restore original size
        
    def _log_to_console(self, message):
        """Add message to console output."""
        self.console_text.config(state=tk.NORMAL)
        self.console_text.insert(tk.END, message + "\n")
        self.console_text.see(tk.END)
        self.console_text.config(state=tk.DISABLED)
        self.root.update()

    def auto_generate_output_filename(self):
        """Auto-generate output filename based on input filename."""
        input_path = self.input_file.get()
        if input_path:
            path = Path(input_path)
            # Sanitize the filename to avoid issues with special characters
            sanitized_stem = self._sanitize_filename(path.stem)
            output_path = path.parent / f"{sanitized_stem}_trimmed{path.suffix}"
            self.output_file.set(str(output_path))
            
    def update_preview(self):
        """Update the preview text with trim information."""
        try:
            input_path = self.input_file.get()
            output_path = self.output_file.get()
            duration = float(self.trim_duration.get())
            from_start = self.trim_from_start.get()
            
            if not input_path or not os.path.exists(input_path):
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(tk.END, "Please select a valid input video file.")
                return
                
            # Load video to get total duration
            video = VideoFileClip(input_path)
            total_duration = video.duration
            video.close()
            
            if from_start:
                start_time = duration
                end_time = total_duration
                trim_info = f"Trimming {duration} seconds from the START"
            else:
                start_time = 0
                end_time = total_duration - duration
                trim_info = f"Trimming {duration} seconds from the END"
                
            if end_time <= start_time:
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(tk.END, f"ERROR: Cannot trim {duration} seconds from {'start' if from_start else 'end'}.\n")
                self.preview_text.insert(tk.END, f"Video duration is only {total_duration:.2f} seconds.")
                return
                
            # Format times
            def format_time(seconds):
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = seconds % 60
                if hours > 0:
                    return f"{hours:02d}:{minutes:02d}:{secs:06.2f}"
                else:
                    return f"{minutes:02d}:{secs:06.2f}"
                    
            # Determine which engine will be used
            engine_info = "FFmpeg (stream copy - faster)" if (self.use_ffmpeg.get() and self.ffmpeg_available.get()) else "MoviePy (re-encoding - slower)"
            verbose_info = "Yes" if self.verbose_mode.get() else "No"
            
            preview_text = f"""TRIM PREVIEW:
{trim_info}

Input file: {os.path.basename(input_path)}
Output file: {os.path.basename(output_path) if output_path else 'Not specified'}
Engine: {engine_info}
Verbose: {verbose_info}

Original duration: {format_time(total_duration)} ({total_duration:.2f} seconds)
Trim duration: {duration} seconds
Resulting duration: {format_time(end_time - start_time)} ({(end_time - start_time):.2f} seconds)

Time range: {format_time(start_time)} to {format_time(end_time)}
"""
            
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, preview_text)
            
        except ValueError:
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, "ERROR: Please enter a valid number for duration.")
        except Exception as e:
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, f"ERROR: {str(e)}")
            
    def trim_video(self):
        """Trim the video in a separate thread."""
        if not self.input_file.get() or not self.output_file.get():
            messagebox.showerror("Error", "Please select both input and output files.")
            return
            
        try:
            duration = float(self.trim_duration.get())
            if duration <= 0:
                messagebox.showerror("Error", "Duration must be greater than 0.")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for duration.")
            return
            
        # Start trimming in a separate thread
        thread = threading.Thread(target=self._trim_video_thread)
        thread.daemon = True
        thread.start()
        
    def _trim_video_thread(self):
        """Trim video in a separate thread to avoid blocking UI."""
        try:
            self.progress.start()
            self.status_label.config(text="Trimming video...")
            
            # Show console if verbose mode is enabled
            if self.verbose_mode.get():
                self._show_console()
                self._log_to_console("=== Starting Video Trimming ===")
            
            self.root.update()
            
            input_path = self.input_file.get()
            output_path = self.output_file.get()
            duration = float(self.trim_duration.get())
            from_start = self.trim_from_start.get()
            
            if self.verbose_mode.get():
                self._log_to_console(f"Input file: {input_path}")
                self._log_to_console(f"Output file: {output_path}")
                self._log_to_console(f"Duration to trim: {duration} seconds")
                self._log_to_console(f"Trim from: {'start' if from_start else 'end'}")
            
            # Sanitize output path to avoid filesystem issues
            output_path_obj = Path(output_path)
            sanitized_stem = self._sanitize_filename(output_path_obj.stem)
            output_path_sanitized = str(output_path_obj.parent / f"{sanitized_stem}{output_path_obj.suffix}")
            
            # Choose trimming method based on user preference and availability
            if self.use_ffmpeg.get() and self.ffmpeg_available.get():
                # Use FFmpeg for fast trimming
                if self.verbose_mode.get():
                    self._log_to_console("Using FFmpeg (stream copy - faster)")
                    self._log_to_console(f"Sanitized output path: {output_path_sanitized}")
                
                self.ffmpeg_trimmer.trim_video_advanced(
                    input_path, output_path_sanitized, duration, from_start, verbose=self.verbose_mode.get()
                )
                engine_used = "FFmpeg (stream copy)"
            else:
                # Use MoviePy for re-encoding
                if self.verbose_mode.get():
                    self._log_to_console("Using MoviePy (re-encoding - slower)")
                    self._log_to_console(f"Sanitized output path: {output_path_sanitized}")
                
                video = VideoFileClip(input_path)
                total_duration = video.duration
                
                if self.verbose_mode.get():
                    self._log_to_console(f"Video duration: {total_duration:.2f} seconds")
                
                # Calculate trim parameters
                if from_start:
                    start_time = duration
                    end_time = total_duration
                else:
                    start_time = 0
                    end_time = total_duration - duration
                    
                if end_time <= start_time:
                    raise ValueError(f"Cannot trim {duration} seconds from {'start' if from_start else 'end'}. Video is only {total_duration:.2f} seconds long.")
                
                if self.verbose_mode.get():
                    self._log_to_console(f"Trimming from {start_time:.2f}s to {end_time:.2f}s")
                    self._log_to_console("Processing with MoviePy...")
                    
                # Trim video
                trimmed_video = video.subclipped(start_time, end_time)
                
                # Write output
                trimmed_video.write_videofile(
                    output_path_sanitized,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True
                )
                
                # Clean up
                trimmed_video.close()
                video.close()
                engine_used = "MoviePy (re-encoding)"
            
            self.progress.stop()
            self.status_label.config(text="Video trimmed successfully!")
            
            if self.verbose_mode.get():
                self._log_to_console("=== Trimming Complete ===")
                self._log_to_console(f"Successfully saved to: {output_path_sanitized}")
            
            messagebox.showinfo("Success", f"Video trimmed successfully using {engine_used}!\nSaved to: {output_path_sanitized}")
            
        except Exception as e:
            self.progress.stop()
            self.status_label.config(text="Error occurred")
            
            if self.verbose_mode.get():
                self._log_to_console(f"ERROR: {str(e)}")
            
            messagebox.showerror("Error", f"Failed to trim video: {str(e)}")
            
    def clear_all(self):
        """Clear all fields."""
        self.input_file.set("")
        self.output_file.set("")
        self.trim_duration.set("10")
        self.trim_from_start.set(True)
        self.video_duration.set("No video loaded")
        self.preview_text.delete(1.0, tk.END)
        self.status_label.config(text="Ready")
        
        # Clear and hide console
        self.console_text.config(state=tk.NORMAL)
        self.console_text.delete(1.0, tk.END)
        self.console_text.config(state=tk.DISABLED)
        self._hide_console()


def main():
    """Main function to run the application."""
    root = tk.Tk()
    app = VideoTrimmer(root)
    root.mainloop()


if __name__ == "__main__":
    main()

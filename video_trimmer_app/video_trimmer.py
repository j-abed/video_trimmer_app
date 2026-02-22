#!/usr/bin/env python3
"""
Enhanced Video Trimmer with Advanced Features
Modern GUI application with comprehensive video editing capabilities.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import threading
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Callable
from loguru import logger
import json

# Local imports
try:
    from .config_manager import ConfigManager
    from .video_preview import VideoPreview, AsyncVideoLoader
    from .processing_queue import ProcessingQueue, ProcessingJob, JobStatus
    from .ffmpeg_trimmer import FFmpegTrimmer
    from .ffmpeg_processor import AdvancedFFmpegTrimmer
except ImportError:
    # Fallback for direct script execution
    from config_manager import ConfigManager
    from video_preview import VideoPreview, AsyncVideoLoader
    from processing_queue import ProcessingQueue, ProcessingJob, JobStatus
    from ffmpeg_trimmer import FFmpegTrimmer
    from ffmpeg_processor import AdvancedFFmpegTrimmer
from moviepy import VideoFileClip

# Import PIL components for preview
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    # Don't set Image to None to avoid type annotation issues
    logger.warning("PIL not available - video preview will be limited")

# Constants
APP_TITLE = "Enhanced Video Trimmer"
APP_VERSION = "2.0.0"
MIN_WINDOW_WIDTH = 1200
MIN_WINDOW_HEIGHT = 800
DEFAULT_WINDOW_SIZE = (1400, 900)
SUPPORTED_VIDEO_FORMATS = [
    '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.m4v', '.3gp', '.ts'
]
MAX_RECENT_FILES = 10
AUTO_SAVE_INTERVAL = 30  # seconds
TIMELINE_HEIGHT = 80
PREVIEW_SIZE = (400, 300)
MAX_BATCH_SIZE = 50

# Initialize logging
logger.add("logs/video_trimmer.log", rotation="1 MB", retention="30 days", level="DEBUG")

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class TimelineWidget(ctk.CTkFrame):
    """Custom timeline widget for video trimming.
    
    Provides visual timeline with thumbnails, trim markers,
    and interactive controls for precise video trimming.
    
    Attributes:
        video_preview: VideoPreview instance for thumbnail generation
        duration: Total video duration in seconds
        trim_start: Start trim position in seconds
        trim_end: End trim position in seconds
        thumbnails: List of thumbnail images for timeline
        on_time_select: Callback for when a time position is selected
    """
    
    def __init__(self, master, video_preview: VideoPreview, **kwargs):
        """Initialize timeline widget.
        
        Args:
            master: Parent widget
            video_preview: VideoPreview instance
            **kwargs: Additional frame arguments
        """
        super().__init__(master, **kwargs)
        
        self.video_preview = video_preview
        self.duration = 0.0
        self.trim_start = 0.0
        self.trim_end = 0.0
        self.thumbnails: List[Any] = []
        self._pil_thumbnails: List[Image.Image] = []
        self._drag_mode: Optional[str] = None
        self._last_click_pos = 0
        self.on_time_select: Optional[Callable[[float], None]] = None
        self.on_trim_change: Optional[Callable[[float, float], None]] = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup timeline UI."""
        # Timeline canvas
        self.canvas = tk.Canvas(
            self, 
            height=80, 
            bg='#2b2b2b',
            highlightthickness=0
        )
        self.canvas.pack(fill="x", padx=5, pady=5)
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Motion>", self.on_hover)
        self.canvas.bind("<Configure>", lambda e: self._draw_timeline())

    def load_timeline(self, duration: float):
        """Load timeline for given video duration."""
        self.duration = duration
        self.trim_start = 0
        self.trim_end = duration
        
        # Generate thumbnails in background
        threading.Thread(target=self._generate_pil_thumbnails, daemon=True).start()

    def _generate_pil_thumbnails(self):
        """Generate thumbnails for timeline."""
        try:
            # Check if video is properly loaded
            if not self.video_preview.current_video and not self.video_preview._moviepy_clip:
                logger.warning("No video loaded for timeline thumbnails")
                return
            
            logger.debug("Generating timeline thumbnails...")
            # Generate 10 thumbnails
            pil_thumbs = self.video_preview.generate_timeline_thumbnails(count=10, as_pil=True)
            self._pil_thumbnails = pil_thumbs
            logger.debug(f"Generated {len(pil_thumbs)} PIL thumbnails.")

            # Schedule the PhotoImage creation and drawing on the main thread
            self.after(0, self._create_photo_images_and_draw)

        except Exception as e:
            logger.error(f"Error generating timeline thumbnails: {e}")
            self.thumbnails = []
            self.after(0, self._draw_timeline)

    def _create_photo_images_and_draw(self):
        """Create PhotoImage objects and draw them on the canvas."""
        try:
            # Clear canvas
            self.canvas.delete("all")
            
            # Create PhotoImage objects
            self.thumbnails = []
            if PIL_AVAILABLE:
                for i, pil_thumb in enumerate(self._pil_thumbnails):
                    photo = ImageTk.PhotoImage(pil_thumb)
                    self.thumbnails.append(photo)
            else:
                logger.warning("PIL not available - cannot create PhotoImage objects")
            
            logger.debug(f"Created {len(self.thumbnails)} PhotoImage objects.")
            self._draw_timeline()

        except Exception as e:
            logger.error(f"Error creating PhotoImage objects: {e}")
            self.thumbnails = []
            self.after(0, self._draw_timeline)
    
    def _draw_timeline(self):
        """Draw timeline with thumbnails and trim markers."""
        self.canvas.delete("all")
        
        if self.duration <= 0:
            return
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1:  # Canvas not ready
            return
        
        # Draw background
        self.canvas.create_rectangle(0, 0, width, height, fill="gray20", outline="gray30")
        
        # Draw selected region FIRST (behind thumbnails)
        start_x = (self.trim_start / self.duration) * width
        end_x = (self.trim_end / self.duration) * width
        self.canvas.create_rectangle(
            start_x, 0, end_x, height,
            fill="lightblue", outline="blue", width=1, tags="selection"
        )
        
        # Draw thumbnails on top of selection
        if self.thumbnails:
            thumb_width = width // len(self.thumbnails)
            for i, thumb in enumerate(self.thumbnails):
                x = i * thumb_width
                try:
                    # Handle both PhotoImage and PIL Image objects
                    if thumb:  # Check if thumbnail exists
                        # Try to display as PhotoImage first
                        if hasattr(thumb, 'width'):  # PhotoImage or PIL Image
                            # Draw with small margin
                            self.canvas.create_image(x + 2, 5, anchor="nw", image=thumb)
                        else:
                            logger.debug(f"Invalid thumbnail at position {i}")
                            
                except Exception as e:
                    logger.debug(f"Error drawing thumbnail {i}: {e}")
                    # Draw placeholder rectangle for failed thumbnails
                    self.canvas.create_rectangle(
                        x + 2, 5, x + thumb_width - 2, height - 5,
                        fill="gray40", outline="gray50"
                    )
                    # Add text indicating loading/error
                    self.canvas.create_text(
                        x + thumb_width // 2, height // 2,
                        text="...", fill="white", anchor="center"
                    )
        else:
            # No thumbnails - show loading message
            self.canvas.create_text(
                width // 2, height // 2,
                text="Generating thumbnails...", fill="white", anchor="center"
            )
        
        # Draw trim markers on top
        self.canvas.create_line(start_x, 0, start_x, height, fill="green", width=4, tags="start_marker")
        self.canvas.create_rectangle(start_x-5, 0, start_x+5, 20, fill="green", outline="darkgreen", width=1, tags="start_handle")
        self.canvas.create_text(start_x + 8, 15, text="Start", fill="green", anchor="w")
        
        self.canvas.create_line(end_x, 0, end_x, height, fill="red", width=4, tags="end_marker") 
        self.canvas.create_rectangle(end_x-5, 0, end_x+5, 20, fill="red", outline="darkred", width=1, tags="end_handle")
        self.canvas.create_text(end_x - 8, 15, text="End", fill="red", anchor="e")
    
    def on_click(self, event):
        """Handle timeline click."""
        if self.duration <= 0:
            return
        
        width = self.canvas.winfo_width()
        if width <= 1:
            return
            
        time_pos = max(0, min((event.x / width) * self.duration, self.duration))
        
        # Determine if we are dragging a marker
        start_x = (self.trim_start / self.duration) * width
        end_x = (self.trim_end / self.duration) * width

        if abs(event.x - start_x) < 15:
            self._drag_mode = "start"
        elif abs(event.x - end_x) < 15:
            self._drag_mode = "end"
        else:
            self._drag_mode = "playhead" # Not dragging a marker, so move playhead

        # Update position based on click
        if self._drag_mode in ["start", "end"]:
            self.on_drag(event)

    def on_drag(self, event):
        """Handle timeline drag."""
        if self.duration <= 0:
            return
        
        width = self.canvas.winfo_width()
        if width <= 1:
            return
            
        time_pos = max(0, min((event.x / width) * self.duration, self.duration))
        
        if self._drag_mode == "start":
            self.trim_start = max(0, min(time_pos, self.trim_end - 0.5)) # Ensure start < end with minimum gap
        elif self._drag_mode == "end":
            self.trim_end = min(self.duration, max(time_pos, self.trim_start + 0.5)) # Ensure end > start with minimum gap
        elif self._drag_mode == "playhead":
            # Just update the preview position without changing trim markers
            pass
        
        self._draw_timeline()

        # Notify about changes after drawing
        if self.on_trim_change and (self._drag_mode == "start" or self._drag_mode == "end"):
            self.on_trim_change(self.trim_start, self.trim_end)

        if self.on_time_select:
            # If dragging a marker, send that marker's time. Otherwise, send the raw time_pos.
            if self._drag_mode == "start":
                self.on_time_select(self.trim_start)
            elif self._drag_mode == "end":
                self.on_time_select(self.trim_end)
            else:
                # Ensure time_pos is within bounds for preview
                preview_time = max(0, min(time_pos, self.duration - 0.1))
                self.on_time_select(preview_time)
    
    def on_release(self, event):
        """Handle mouse button release."""
        self._drag_mode = None
    
    def on_hover(self, event):
        """Handle mouse hover for tooltip."""
        if self.duration <= 0:
            return
        
        width = self.canvas.winfo_width()
        time_pos = (event.x / width) * self.duration
        
        # Show time tooltip
        self.canvas.delete("tooltip")
        self.canvas.create_text(
            event.x, 10, 
            text=f"{time_pos:.2f}s", 
            fill="white", 
            tags="tooltip"
        )

    def get_trim_settings(self) -> Dict[str, float]:
        """Get current trim settings."""
        return {
            'start': self.trim_start,
            'end': self.trim_end,
            'duration': self.trim_end - self.trim_start
        }


class BatchProcessingDialog(ctk.CTkToplevel):
    """Dialog for batch processing multiple videos."""
    
    def __init__(self, parent, queue_manager: ProcessingQueue):
        super().__init__(parent)
        
        self.queue_manager = queue_manager
        self.setup_ui()
        
    def setup_ui(self):
        """Setup batch processing UI."""
        self.title("Batch Processing")
        self.geometry("800x600")
        
        # File list
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(self.file_frame, text="Video Files:").pack(pady=5)
        
        # Files listbox
        self.files_listbox = tk.Listbox(self.file_frame, height=10)
        self.files_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self.file_frame)
        button_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(button_frame, text="Add Files", command=self.add_files).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Remove Selected", command=self.remove_selected).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Clear All", command=self.clear_all).pack(side="left", padx=5)
        
        # Settings
        settings_frame = ctk.CTkFrame(self)
        settings_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(settings_frame, text="Batch Settings:").pack(pady=5)
        
        # Trim duration
        duration_frame = ctk.CTkFrame(settings_frame)
        duration_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(duration_frame, text="Trim Duration (seconds):").pack(side="left")
        self.duration_var = tk.StringVar(value="10")
        ctk.CTkEntry(duration_frame, textvariable=self.duration_var, width=100).pack(side="right")
        
        # Trim direction
        direction_frame = ctk.CTkFrame(settings_frame)
        direction_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(direction_frame, text="Trim From:").pack(side="left")
        self.direction_var = tk.StringVar(value="start")
        ctk.CTkRadioButton(direction_frame, text="Start", variable=self.direction_var, value="start").pack(side="right", padx=5)
        ctk.CTkRadioButton(direction_frame, text="End", variable=self.direction_var, value="end").pack(side="right")
        
        # Process buttons
        process_frame = ctk.CTkFrame(self)
        process_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(process_frame, text="Start Batch Processing", command=self.start_processing).pack(side="left", padx=5)
        ctk.CTkButton(process_frame, text="Close", command=self.destroy).pack(side="right", padx=5)
    
    def add_files(self):
        """Add files to batch list."""
        filetypes = [
            ("Video files", "*.mp4 *.ts *.avi *.mov *.mkv *.wmv *.flv *.webm"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select video files for batch processing",
            filetypes=filetypes
        )
        
        for file in files:
            self.files_listbox.insert(tk.END, file)
    
    def remove_selected(self):
        """Remove selected files from list."""
        selected = self.files_listbox.curselection()
        for i in reversed(selected):
            self.files_listbox.delete(i)
    
    def clear_all(self):
        """Clear all files."""
        self.files_listbox.delete(0, tk.END)
    
    def start_processing(self):
        """Start batch processing."""
        files = list(self.files_listbox.get(0, tk.END))
        if not files:
            messagebox.showwarning("Warning", "No files selected for processing.")
            return
        
        try:
            duration = float(self.duration_var.get())
            from_start = self.direction_var.get() == "start"
            
            # Add jobs to queue
            for file_path in files:
                output_path = self._generate_output_path(file_path)
                self.queue_manager.create_and_add_job(
                    input_path=file_path,
                    output_path=output_path,
                    trim_duration=duration,
                    from_start=from_start
                )
            
            messagebox.showinfo("Info", f"Added {len(files)} jobs to processing queue.")
            self.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid duration.")
    
    def _generate_output_path(self, input_path: str) -> str:
        """Generate output path for input file."""
        path = Path(input_path)
        return str(path.parent / f"{path.stem}_trimmed{path.suffix}")


class AdvancedVideoTrimmer(TkinterDnD.Tk):
    """Advanced Video Trimmer with modern UI and enhanced features."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.config_manager = ConfigManager()
        self.video_preview = VideoPreview()
        self.async_loader = AsyncVideoLoader(self.video_preview)
        self.queue_manager = ProcessingQueue(max_workers=self.config_manager.get("processing.concurrent_jobs", 2))
        self.ffmpeg_trimmer = FFmpegTrimmer()
        
        # Register processing engines
        self.queue_manager.register_engine("ffmpeg", self.ffmpeg_trimmer)
        # MoviePy engine is handled specially in processing queue (no registration needed)
        
        # Setup queue callbacks
        self.queue_manager.on_job_completed = self.on_job_completed
        self.queue_manager.on_job_failed = self.on_job_failed
        self.queue_manager.on_job_progress = self.on_job_progress
        
        # State variables
        self.current_video_info = None
        self.processing_jobs = {}
        
        # Load theme settings before creating UI
        self.load_theme_settings()
        
        self.setup_ui()
        self.setup_drag_drop()
        self.load_settings()
        
        # Start queue processing
        self.queue_manager.start_processing()
        
        logger.info("Advanced Video Trimmer started")
    
    def setup_ui(self):
        """Setup the main user interface."""
        self.title("Advanced Video Trimmer Pro")
        self.geometry(self.config_manager.get("appearance.window_geometry", "1200x900"))
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self.setup_menu()
        self.setup_main_content()
        self.setup_status_bar()
        
    def setup_menu(self):
        """Setup menu bar."""
        # Note: CustomTkinter doesn't have a built-in menu, so we'll use buttons in a frame
        menu_frame = ctk.CTkFrame(self.main_frame, height=40)
        menu_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        menu_frame.grid_columnconfigure(0, weight=1)
        
        # Left menu items
        left_menu = ctk.CTkFrame(menu_frame)
        left_menu.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        ctk.CTkButton(left_menu, text="Open", command=self.open_file, width=60).pack(side="left", padx=2)
        ctk.CTkButton(left_menu, text="Recent", command=self.show_recent_files, width=60).pack(side="left", padx=2)
        ctk.CTkButton(left_menu, text="Batch", command=self.open_batch_dialog, width=60).pack(side="left", padx=2)
        
        # Right menu items
        right_menu = ctk.CTkFrame(menu_frame)
        right_menu.grid(row=0, column=1, sticky="e", padx=5, pady=5)
        
        ctk.CTkButton(right_menu, text="Queue", command=self.show_queue_dialog, width=60).pack(side="right", padx=2)
        ctk.CTkButton(right_menu, text="Settings", command=self.show_settings_dialog, width=70).pack(side="right", padx=2)
        
    def setup_main_content(self):
        """Setup main content area."""
        # Left panel - File info and controls
        self.left_panel = ctk.CTkScrollableFrame(self.main_frame, width=320)
        self.left_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=5)
        
        # Right panel - Preview and timeline
        self.right_panel = ctk.CTkFrame(self.main_frame)
        self.right_panel.grid(row=1, column=1, sticky="nsew", padx=(5, 0), pady=5)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)
        
        self.setup_left_panel()
        self.setup_right_panel()
    
    def setup_left_panel(self):
        """Setup left control panel."""
        # File selection section
        file_section = ctk.CTkFrame(self.left_panel)
        file_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(file_section, text="Input Video", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        self.file_label = ctk.CTkLabel(file_section, text="No file selected", wraplength=250)
        self.file_label.pack(pady=5)
        
        ctk.CTkButton(file_section, text="Select Video File", command=self.open_file).pack(pady=5)
        
        # Video info section
        info_section = ctk.CTkFrame(self.left_panel)
        info_section.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(info_section, text="Video Information", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        self.info_text = ctk.CTkTextbox(info_section, height=150)
        self.info_text.pack(fill="x", padx=5, pady=5)
        self.info_text.insert("0.0", "No video loaded")
        
        # Trim settings section
        trim_section = ctk.CTkFrame(self.left_panel)
        trim_section.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(trim_section, text="Trim Settings", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        # Duration input
        duration_frame = ctk.CTkFrame(trim_section)
        duration_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(duration_frame, text="Duration (seconds):").pack(anchor="w")
        self.duration_var = tk.StringVar(value="10")
        self.duration_entry = ctk.CTkEntry(duration_frame, textvariable=self.duration_var)
        self.duration_entry.pack(fill="x", pady=2)
        
        # Trim direction
        direction_frame = ctk.CTkFrame(trim_section)
        direction_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(direction_frame, text="Trim From:").pack(anchor="w")
        self.direction_var = tk.StringVar(value="start")
        
        radio_frame = ctk.CTkFrame(direction_frame)
        radio_frame.pack(fill="x", pady=2)
        
        ctk.CTkRadioButton(radio_frame, text="Start", variable=self.direction_var, value="start").pack(side="left", padx=5)
        ctk.CTkRadioButton(radio_frame, text="End", variable=self.direction_var, value="end").pack(side="left", padx=5)
        
        # Quality settings
        quality_frame = ctk.CTkFrame(trim_section)
        quality_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(quality_frame, text="Quality:").pack(anchor="w")
        self.quality_var = tk.StringVar(value="original")
        quality_menu = ctk.CTkOptionMenu(quality_frame, variable=self.quality_var, 
                                       values=["original", "high", "medium", "low"])
        quality_menu.pack(fill="x", pady=2)
        
        # Engine selection
        engine_frame = ctk.CTkFrame(trim_section)
        engine_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(engine_frame, text="Processing Engine:").pack(anchor="w")
        self.engine_var = tk.StringVar(value="ffmpeg")
        engine_menu = ctk.CTkOptionMenu(engine_frame, variable=self.engine_var,
                                      values=["ffmpeg", "moviepy"])
        engine_menu.pack(fill="x", pady=2)
        
        # Process button
        ctk.CTkButton(trim_section, text="Add to Queue", command=self.add_to_queue,
                     font=ctk.CTkFont(size=14, weight="bold"), height=40).pack(fill="x", padx=5, pady=10)
        
        # Quick actions
        actions_section = ctk.CTkFrame(self.left_panel)
        actions_section.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(actions_section, text="Quick Actions", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        ctk.CTkButton(actions_section, text="Save Preset", command=self.save_preset).pack(fill="x", padx=5, pady=2)
        ctk.CTkButton(actions_section, text="Load Preset", command=self.load_preset).pack(fill="x", padx=5, pady=2)
        ctk.CTkButton(actions_section, text="Preview Trim", command=self.preview_trim).pack(fill="x", padx=5, pady=2)
    
    def setup_right_panel(self):
        """Setup right preview panel."""
        # Preview section
        preview_section = ctk.CTkFrame(self.right_panel)
        preview_section.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        preview_section.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(preview_section, text="Video Preview", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        # Video preview canvas
        self.preview_frame = ctk.CTkFrame(preview_section, height=300)
        self.preview_frame.pack(fill="x", padx=5, pady=5)
        
        # Create canvas for video preview
        self.preview_canvas = tk.Canvas(self.preview_frame, bg="black", height=280)
        self.preview_canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Placeholder text (will be hidden when video loads)
        self.preview_placeholder = ctk.CTkLabel(
            self.preview_frame, 
            text="Video preview will appear here\n(Drop video files anywhere)",
            text_color="gray"
        )
        self.preview_placeholder.place(relx=0.5, rely=0.5, anchor="center")
        
        # Store current preview image reference
        self.current_preview_image = None
        
        # Timeline section
        timeline_section = ctk.CTkFrame(self.right_panel)
        timeline_section.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        timeline_section.grid_rowconfigure(1, weight=1)
        timeline_section.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(timeline_section, text="Timeline", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        # Timeline widget
        self.timeline = TimelineWidget(timeline_section, self.video_preview)
        self.timeline.pack(fill="both", expand=True, padx=5, pady=5)
        self.timeline.on_time_select = self.update_video_preview
        self.timeline.on_trim_change = self.on_timeline_trim_changed

    def setup_status_bar(self):
        """Setup status bar."""
        self.status_frame = ctk.CTkFrame(self.main_frame, height=30)
        self.status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        # Status text
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ctk.CTkLabel(self.status_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.status_frame, width=200)
        self.progress_bar.grid(row=0, column=1, sticky="e", padx=10, pady=5)
        self.progress_bar.set(0)
        
    def setup_drag_drop(self):
        """Setup drag and drop functionality."""
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.on_file_drop)
        
        # Also register for the preview frame
        self.preview_frame.drop_target_register(DND_FILES)
        self.preview_frame.dnd_bind('<<Drop>>', self.on_file_drop)
    
    def on_file_drop(self, event):
        """Handle dropped files."""
        files = event.data.split()
        if files:
            # Clean up file path (remove curly braces if present)
            file_path = files[0].strip('{}')
            self.load_video_file(file_path)
    
    def open_file(self):
        """Open file dialog to select video."""
        filetypes = [
            ("Video files", "*.mp4 *.ts *.avi *.mov *.mkv *.wmv *.flv *.webm"),
            ("All files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Select video file",
            filetypes=filetypes
        )
        
        if file_path:
            self.load_video_file(file_path)
    
    def load_video_file(self, file_path: str):
        """Load video file asynchronously."""
        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"File not found: {file_path}")
            return
        
        self.status_var.set("Loading video...")
        self.file_label.configure(text=os.path.basename(file_path))
        
        # Load video asynchronously
        self.async_loader.load_video_async(file_path, self.on_video_loaded)
        
        # Add to recent files
        self.config_manager.add_recent_file(file_path)
    
    def on_video_loaded(self, success: bool, video_info: Optional[dict]):
        """Callback when video is loaded."""
        if success and video_info:
            self.current_video_info = video_info
            
            # Update timeline
            self.timeline.load_timeline(video_info['duration'])
            
            # Update video preview
            self.update_video_preview()
            
            # Update info display
            info_text = f"""Duration: {self.format_duration(video_info['duration'])}
Resolution: {video_info['width']}x{video_info['height']}
FPS: {video_info['fps']:.2f}
Frame Count: {video_info['frame_count']}
Estimated Bitrate: {video_info.get('bitrate', 0):.0f} kbps"""
            
            self.info_text.delete("0.0", "end")
            self.info_text.insert("0.0", info_text)
            
            self.status_var.set(f"Video loaded: {self.format_duration(video_info['duration'])}")
        else:
            messagebox.showerror("Error", "Failed to load video file")
            self.status_var.set("Error loading video")
    
    def update_video_preview(self, time_pos: float = 0.0):
        """Update video preview with frame at given time position."""
        try:
            if not self.video_preview.current_video and not self.video_preview._moviepy_clip:
                return
            
            # Get canvas dimensions
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                # Canvas not ready, try again later
                self.after(100, lambda: self.update_video_preview(time_pos))
                return
            
            # Calculate display size maintaining aspect ratio
            if self.current_video_info:
                video_width = self.current_video_info['width']
                video_height = self.current_video_info['height']
                
                # Calculate scaling to fit canvas while maintaining aspect ratio
                scale_w = (canvas_width - 20) / video_width  # 10px margin each side
                scale_h = (canvas_height - 20) / video_height  # 10px margin each side
                scale = min(scale_w, scale_h)
                
                display_width = int(video_width * scale)
                display_height = int(video_height * scale)
            else:
                display_width = canvas_width - 20
                display_height = canvas_height - 20
            
            # Get frame from video
            frame = self.video_preview.get_frame_at_time(time_pos, (display_width, display_height))
            
            if frame is not None:
                # Convert numpy array to PIL Image
                if PIL_AVAILABLE:
                    pil_image = Image.fromarray(frame)
                    # Convert to PhotoImage
                    photo = ImageTk.PhotoImage(pil_image)
                    
                    # Clear canvas and display image
                    self.preview_canvas.delete("all")
                    self.preview_canvas.create_image(
                        canvas_width // 2, canvas_height // 2,
                        image=photo, anchor="center"
                    )
                    
                    # Store reference to prevent garbage collection
                    self.current_preview_image = photo
                    
                    # Hide placeholder text
                    self.preview_placeholder.place_forget()
                    
                else:
                    # Fallback: show text if PIL not available
                    self.preview_canvas.delete("all")
                    self.preview_canvas.create_text(
                        canvas_width // 2, canvas_height // 2,
                        text="Video loaded\n(PIL required for preview)",
                        fill="white", anchor="center"
                    )
                    self.preview_placeholder.place_forget()
            else:
                # Failed to get frame
                self.preview_canvas.delete("all")
                self.preview_canvas.create_text(
                    canvas_width // 2, canvas_height // 2,
                    text="Preview not available", fill="red", anchor="center"
                )
                
        except Exception as e:
            logger.error(f"Error updating video preview: {e}")
            # Show error in canvas
            try:
                self.preview_canvas.delete("all")
                self.preview_canvas.create_text(
                    self.preview_canvas.winfo_width() // 2,
                    self.preview_canvas.winfo_height() // 2,
                    text="Preview error", fill="red", anchor="center"
                )
            except:
                pass
    
    def on_timeline_trim_changed(self, trim_start: float, trim_end: float):
        """Handle timeline trim changes and update UI controls."""
        try:
            if not self.current_video_info:
                return
                
            total_duration = self.current_video_info['duration']
            
            # Calculate how much is being trimmed from each end
            trim_from_start = trim_start
            trim_from_end = total_duration - trim_end
            
            # Update controls based on which end has more trimming
            if trim_from_start > trim_from_end:
                # More trimmed from start
                self.direction_var.set("start")
                self.duration_var.set(f"{trim_from_start:.2f}")
            else:
                # More trimmed from end (or equal)
                self.direction_var.set("end")
                self.duration_var.set(f"{trim_from_end:.2f}")
                
        except Exception as e:
            logger.error(f"Error updating trim controls: {e}")
    
    def add_to_queue(self):
        """Add current video to processing queue."""
        if not self.current_video_info:
            messagebox.showwarning("Warning", "Please load a video first.")
            return
        
        try:
            duration = float(self.duration_var.get())
            from_start = self.direction_var.get() == "start"
            engine = self.engine_var.get()
            
            # Generate output path
            input_path = self.video_preview.video_path
            output_path = self.generate_output_path(input_path)
            
            # Add job to queue
            job_id = self.queue_manager.create_and_add_job(
                input_path=input_path,
                output_path=output_path,
                trim_duration=duration,
                from_start=from_start,
                engine=engine,
                quality=self.quality_var.get()
            )
            
            self.status_var.set(f"Added job {job_id[:8]}... to queue")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid duration.")
    
    def generate_output_path(self, input_path: str) -> str:
        """Generate output path for video."""
        path = Path(input_path)
        counter = 1
        
        # Find unique filename
        while True:
            if counter == 1:
                output_path = path.parent / f"{path.stem}_trimmed{path.suffix}"
            else:
                output_path = path.parent / f"{path.stem}_trimmed_{counter}{path.suffix}"
            
            if not output_path.exists():
                return str(output_path)
            
            counter += 1
    
    def preview_trim(self):
        """Preview trim settings."""
        if not self.current_video_info:
            messagebox.showwarning("Warning", "Please load a video first.")
            return
        
        try:
            duration = float(self.duration_var.get())
            from_start = self.direction_var.get() == "start"
            total_duration = self.current_video_info['duration']
            
            if from_start:
                start_time = duration
                end_time = total_duration
                trim_info = f"Trimming {duration}s from START"
            else:
                start_time = 0
                end_time = total_duration - duration
                trim_info = f"Trimming {duration}s from END"
            
            if end_time <= start_time:
                messagebox.showerror("Error", f"Invalid trim: resulting video would be too short!")
                return
            
            result_duration = end_time - start_time
            
            preview_text = f"""{trim_info}

Original Duration: {self.format_duration(total_duration)}
Start Time: {self.format_duration(start_time)}
End Time: {self.format_duration(end_time)}
Result Duration: {self.format_duration(result_duration)}

Engine: {self.engine_var.get().upper()}
Quality: {self.quality_var.get().title()}"""
            
            messagebox.showinfo("Trim Preview", preview_text)
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid duration.")
    
    def show_recent_files(self):
        """Show recent files menu."""
        recent_files = self.config_manager.get_recent_files()
        
        if not recent_files:
            messagebox.showinfo("Info", "No recent files found.")
            return
        
        # Create recent files dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Recent Files")
        dialog.geometry("500x400")
        
        ctk.CTkLabel(dialog, text="Recent Files", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Files list
        listbox_frame = ctk.CTkFrame(dialog)
        listbox_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        files_listbox = tk.Listbox(listbox_frame)
        files_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        for file_path in recent_files:
            files_listbox.insert(tk.END, file_path)
        
        # Buttons
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        def open_selected():
            selection = files_listbox.curselection()
            if selection:
                file_path = recent_files[selection[0]]
                dialog.destroy()
                self.load_video_file(file_path)
        
        ctk.CTkButton(button_frame, text="Open Selected", command=open_selected).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)
    
    def open_batch_dialog(self):
        """Open batch processing dialog."""
        BatchProcessingDialog(self, self.queue_manager)
    
    def show_queue_dialog(self):
        """Show processing queue dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Processing Queue")
        dialog.geometry("700x500")
        
        # Queue stats
        stats_frame = ctk.CTkFrame(dialog)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        stats = self.queue_manager.get_queue_stats()
        stats_text = f"Pending: {stats['pending']} | Processing: {stats['processing']} | Completed: {stats['completed']} | Failed: {stats['failed']}"
        
        ctk.CTkLabel(stats_frame, text="Queue Statistics", font=ctk.CTkFont(size=14, weight="bold")).pack()
        ctk.CTkLabel(stats_frame, text=stats_text).pack()
        
        # Jobs list
        jobs_frame = ctk.CTkFrame(dialog)
        jobs_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ctk.CTkLabel(jobs_frame, text="Jobs", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        # Simple text display for jobs (in a real app, you'd want a proper table)
        jobs_text = ctk.CTkTextbox(jobs_frame)
        jobs_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Populate jobs list
        jobs_info = "ID\t\tStatus\t\tInput File\n" + "="*60 + "\n"
        for job in self.queue_manager.jobs.values():
            job_id_short = job.id[:8]
            input_name = os.path.basename(job.input_path)[:30]
            jobs_info += f"{job_id_short}...\t{job.status.value}\t\t{input_name}\n"
        
        jobs_text.insert("0.0", jobs_info)
        
        # Controls
        controls_frame = ctk.CTkFrame(dialog)
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(controls_frame, text="Pause Queue", 
                     command=self.queue_manager.pause_processing).pack(side="left", padx=5)
        ctk.CTkButton(controls_frame, text="Resume Queue", 
                     command=self.queue_manager.resume_processing).pack(side="left", padx=5)
        ctk.CTkButton(controls_frame, text="Clear Completed", 
                     command=self.queue_manager.clear_completed_jobs).pack(side="left", padx=5)
        ctk.CTkButton(controls_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)
    
    def show_settings_dialog(self):
        """Show application settings dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Settings")
        dialog.geometry("600x500")
        
        # Settings notebook (tabs)
        notebook_frame = ctk.CTkFrame(dialog)
        notebook_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Simple tab implementation using buttons and frames
        tab_frame = ctk.CTkFrame(notebook_frame)
        tab_frame.pack(fill="x", padx=5, pady=5)
        
        content_frame = ctk.CTkFrame(notebook_frame)
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Tab variables
        self.current_tab = tk.StringVar(value="appearance")
        
        def show_tab(tab_name):
            self.current_tab.set(tab_name)
            self.update_settings_tab(content_frame, tab_name)
        
        # Tab buttons
        ctk.CTkButton(tab_frame, text="Appearance", command=lambda: show_tab("appearance")).pack(side="left", padx=2)
        ctk.CTkButton(tab_frame, text="Processing", command=lambda: show_tab("processing")).pack(side="left", padx=2)
        ctk.CTkButton(tab_frame, text="Advanced", command=lambda: show_tab("advanced")).pack(side="left", padx=2)
        
        # Show initial tab
        show_tab("appearance")
        
        # Buttons
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(button_frame, text="Save", command=self.save_settings).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="Reset to Defaults", 
                     command=self.reset_settings).pack(side="left", padx=5)
    
    def update_settings_tab(self, parent, tab_name):
        """Update settings tab content."""
        # Clear existing content
        for widget in parent.winfo_children():
            widget.destroy()
        
        if tab_name == "appearance":
            self.create_appearance_settings(parent)
        elif tab_name == "processing":
            self.create_processing_settings(parent)
        elif tab_name == "advanced":
            self.create_advanced_settings(parent)
    
    def create_appearance_settings(self, parent):
        """Create appearance settings."""
        ctk.CTkLabel(parent, text="Appearance Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Theme selection
        theme_frame = ctk.CTkFrame(parent)
        theme_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(theme_frame, text="Theme:").pack(anchor="w", padx=5)
        theme_var = tk.StringVar(value=self.config_manager.get("appearance.theme", "dark"))
        theme_menu = ctk.CTkOptionMenu(theme_frame, variable=theme_var, values=["dark", "light"])
        theme_menu.pack(fill="x", padx=5, pady=2)
        
        # Color theme
        color_frame = ctk.CTkFrame(parent)
        color_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(color_frame, text="Color Theme:").pack(anchor="w", padx=5)
        color_var = tk.StringVar(value=self.config_manager.get("appearance.color_theme", "blue"))
        color_menu = ctk.CTkOptionMenu(color_frame, variable=color_var, values=["blue", "green", "dark-blue"])
        color_menu.pack(fill="x", padx=5, pady=2)
        
        # Store references for saving
        self.theme_var = theme_var
        self.color_var = color_var
    
    def create_processing_settings(self, parent):
        """Create processing settings."""
        ctk.CTkLabel(parent, text="Processing Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Concurrent jobs
        jobs_frame = ctk.CTkFrame(parent)
        jobs_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(jobs_frame, text="Concurrent Jobs:").pack(anchor="w", padx=5)
        jobs_var = tk.StringVar(value=str(self.config_manager.get("processing.concurrent_jobs", 2)))
        jobs_entry = ctk.CTkEntry(jobs_frame, textvariable=jobs_var)
        jobs_entry.pack(fill="x", padx=5, pady=2)
        
        # Hardware acceleration
        hw_frame = ctk.CTkFrame(parent)
        hw_frame.pack(fill="x", padx=10, pady=5)
        
        hw_var = tk.BooleanVar(value=self.config_manager.get("processing.hardware_acceleration", True))
        ctk.CTkCheckBox(hw_frame, text="Enable Hardware Acceleration", variable=hw_var).pack(anchor="w", padx=5, pady=5)
        
        # Store references
        self.jobs_var = jobs_var
        self.hw_var = hw_var
    
    def create_advanced_settings(self, parent):
        """Create advanced settings."""
        ctk.CTkLabel(parent, text="Advanced Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Verbose logging
        log_frame = ctk.CTkFrame(parent)
        log_frame.pack(fill="x", padx=10, pady=5)
        
        log_var = tk.BooleanVar(value=self.config_manager.get("advanced.verbose_logging", False))
        ctk.CTkCheckBox(log_frame, text="Enable Verbose Logging", variable=log_var).pack(anchor="w", padx=5, pady=5)
        
        # Auto updates
        update_frame = ctk.CTkFrame(parent)
        update_frame.pack(fill="x", padx=10, pady=5)
        
        update_var = tk.BooleanVar(value=self.config_manager.get("advanced.check_updates", True))
        ctk.CTkCheckBox(update_frame, text="Check for Updates", variable=update_var).pack(anchor="w", padx=5, pady=5)
        
        # Store references
        self.log_var = log_var
        self.update_var = update_var
    
    def save_settings(self):
        """Save current settings."""
        try:
            # Save settings based on current tab and available variables
            if hasattr(self, 'theme_var'):
                old_theme = self.config_manager.get("appearance.theme", "dark")
                new_theme = self.theme_var.get()
                old_color = self.config_manager.get("appearance.color_theme", "blue")
                new_color = self.color_var.get()
                
                self.config_manager.set("appearance.theme", new_theme)
                self.config_manager.set("appearance.color_theme", new_color)
                
                # Apply theme changes immediately
                theme_changed = False
                if old_theme != new_theme:
                    ctk.set_appearance_mode(new_theme)
                    theme_changed = True
                if old_color != new_color:
                    ctk.set_default_color_theme(new_color)
                    theme_changed = True
                    
                if theme_changed:
                    messagebox.showinfo("Settings", "Settings saved! Please restart the application for color theme changes to take full effect.")
                else:
                    messagebox.showinfo("Settings", "Settings saved successfully!")
            
            if hasattr(self, 'jobs_var'):
                self.config_manager.set("processing.concurrent_jobs", int(self.jobs_var.get()))
                self.config_manager.set("processing.hardware_acceleration", self.hw_var.get())
            
            if hasattr(self, 'log_var'):
                self.config_manager.set("advanced.verbose_logging", self.log_var.get())
                self.config_manager.set("advanced.check_updates", self.update_var.get())
            
            # Save config to disk
            self.config_manager.save_config()
            
            if not hasattr(self, 'theme_var'):
                messagebox.showinfo("Settings", "Settings saved successfully!")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid values for all settings.")
    
    def reset_settings(self):
        """Reset settings to defaults."""
        if messagebox.askyesno("Confirm Reset", "Reset all settings to defaults?"):
            self.config_manager.reset_to_defaults()
            messagebox.showinfo("Settings", "Settings reset to defaults.")
    
    def save_preset(self):
        """Save current settings as preset."""
        name = tk.simpledialog.askstring("Save Preset", "Enter preset name:")
        if name:
            preset = {
                'duration': self.duration_var.get(),
                'direction': self.direction_var.get(),
                'quality': self.quality_var.get(),
                'engine': self.engine_var.get()
            }
            self.config_manager.save_preset(name, preset)
            messagebox.showinfo("Preset", f"Preset '{name}' saved successfully!")
    
    def load_preset(self):
        """Load settings from preset."""
        # Get saved presets
        saved_presets = self.config_manager.get_presets()
        
        # Define built-in presets
        builtin_presets = {
            "Remove First 10s": {
                'duration': '10',
                'direction': 'start',
                'quality': 'original',
                'engine': 'ffmpeg'
            },
            "Remove Last 10s": {
                'duration': '10', 
                'direction': 'end',
                'quality': 'original',
                'engine': 'ffmpeg'
            },
            "Remove First 30s": {
                'duration': '30',
                'direction': 'start', 
                'quality': 'original',
                'engine': 'ffmpeg'
            },
            "Remove Last 30s": {
                'duration': '30',
                'direction': 'end',
                'quality': 'original', 
                'engine': 'ffmpeg'
            },
            "Quick Trim (5s start)": {
                'duration': '5',
                'direction': 'start',
                'quality': 'original',
                'engine': 'ffmpeg'
            },
            "Quick Trim (5s end)": {
                'duration': '5',
                'direction': 'end',
                'quality': 'original',
                'engine': 'ffmpeg'
            }
        }
        
        # Combine built-in and saved presets
        all_presets = {**builtin_presets, **saved_presets}
        
        if not all_presets:
            messagebox.showinfo("Presets", "No presets found.")
            return
        
        # Create preset selection dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Load Preset")
        dialog.geometry("350x300")
        
        ctk.CTkLabel(dialog, text="Select Preset:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        # Preset list with categories
        listbox_frame = ctk.CTkFrame(dialog)
        listbox_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        preset_listbox = tk.Listbox(listbox_frame, height=10)
        preset_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add built-in presets first (with separator)
        if builtin_presets:
            preset_listbox.insert(tk.END, "--- Built-in Presets ---")
            for name in builtin_presets.keys():
                preset_listbox.insert(tk.END, name)
        
        # Add saved presets
        if saved_presets:
            if builtin_presets:  # Add separator if we have both types
                preset_listbox.insert(tk.END, "")
                preset_listbox.insert(tk.END, "--- Saved Presets ---")
            for name in saved_presets.keys():
                preset_listbox.insert(tk.END, name)
        
        def load_selected():
            selection = preset_listbox.curselection()
            if not selection:
                return
                
            selected_text = preset_listbox.get(selection[0])
            
            # Skip separator lines
            if selected_text.startswith("---") or selected_text == "":
                return
                
            if selected_text in all_presets:
                preset = all_presets[selected_text]
                self.duration_var.set(preset.get('duration', '10'))
                self.direction_var.set(preset.get('direction', 'start'))
                self.quality_var.set(preset.get('quality', 'original'))
                self.engine_var.set(preset.get('engine', 'ffmpeg'))
                dialog.destroy()
                messagebox.showinfo("Preset", f"Preset '{selected_text}' loaded!")
        
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(button_frame, text="Load", command=load_selected).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=5)
    
    def load_theme_settings(self):
        """Load and apply theme settings before UI creation."""
        theme = self.config_manager.get("appearance.theme", "dark")
        color_theme = self.config_manager.get("appearance.color_theme", "blue")
        
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme(color_theme)
    
    def load_settings(self):
        """Load remaining application settings."""
        # Apply window geometry (themes already loaded in load_theme_settings)
        geometry = self.config_manager.get("appearance.window_geometry", "1200x900")
        self.geometry(geometry)
    
    def on_job_completed(self, job: ProcessingJob):
        """Handle job completion."""
        self.after(0, lambda: self.status_var.set(f"Completed: {os.path.basename(job.output_path)}"))
    
    def on_job_failed(self, job: ProcessingJob, error: str):
        """Handle job failure."""
        self.after(0, lambda: self.status_var.set(f"Failed: {error[:50]}..."))
        self.after(0, lambda: messagebox.showerror("Processing Error", f"Job failed: {error}"))
    
    def on_job_progress(self, job: ProcessingJob, progress: float):
        """Handle job progress update."""
        self.after(0, lambda: self.progress_bar.set(progress / 100))
        self.after(0, lambda: self.status_var.set(f"Processing: {progress:.1f}%"))
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in seconds to readable format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:06.2f}"
        else:
            return f"{minutes:02d}:{secs:06.2f}"
    
    def on_closing(self):
        """Handle application closing."""
        # Save window state
        if self.config_manager.get("appearance.remember_window_state", True):
            self.config_manager.set("appearance.window_geometry", self.geometry())
        
        # Stop queue processing
        self.queue_manager.stop_processing()
        
        # Cleanup
        self.video_preview.cleanup()
        
        logger.info("Application closing")
        self.destroy()


def main():
    """Main function to run the enhanced video trimmer."""
    try:
        # Initialize logging
        logger.info("Starting Enhanced Video Trimmer")
        
        # Create and run application
        app = AdvancedVideoTrimmer()
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()
        
    except Exception as e:
        logger.exception("Fatal error in main application")
        messagebox.showerror("Fatal Error", f"Application error: {str(e)}")


if __name__ == "__main__":
    main()
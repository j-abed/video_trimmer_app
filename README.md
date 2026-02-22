# Advanced Video Trimmer Pro

A comprehensive Python application for professional video trimming with advanced features. Includes both a modern GUI with enhanced capabilities and a powerful command-line interface for batch processing.

## 🚀 Key Features

### **Modern User Interface**

- **Interactive Timeline**: Visual timeline with thumbnails and draggable trim markers for precision editing
- **Real-time Preview**: Live video preview that updates as you interact with the timeline
- **Dark/Light Themes**: Customizable appearance with multiple color schemes (blue, green, dark-blue)
- **Drag & Drop Support**: Simply drag video files into the application
- **Responsive Design**: Modern, scalable interface using CustomTkinter with proper window resizing

### **Enhanced Timeline Editor**

- **Visual Thumbnails**: See video content at different time points
- **Draggable Markers**: Click and drag start/end trim points with precision
- **Live Preview Updates**: Preview changes instantly as you adjust trim markers
- **Smart Coordinate Mapping**: Accurate time-to-pixel conversion for frame-accurate trimming
- **hover Tooltips**: Real-time time display as you move your mouse

### **Built-in Preset System**

- **Quick Presets**: Remove First/Last 10s, Remove First/Last 30s, Quick Trim 5s options
- **Custom Presets**: Save your own frequently used trimming configurations
- **Easy Access**: Load presets with a simple dialog showing built-in and saved options
- **Professional Workflows**: Streamline repetitive video editing tasks

### **Advanced Processing**

- **Multiple Processing Engines**: FFmpeg (fast) and MoviePy (compatible)
- **Hardware Acceleration**: GPU acceleration support for faster processing
- **Quality Presets**: Original, High, Medium, and Low quality options
- **Concurrent Processing**: Process multiple videos simultaneously with smart queue management
- **Thread-Safe Operations**: Robust video handling with proper synchronization

### **Professional Features**

- **Batch Processing**: Process hundreds of videos with consistent settings
- **Visual Queue Management**: Monitor processing jobs with detailed progress tracking
- **Multiple Trim Segments**: Trim multiple parts from a single video
- **Frame-Accurate Trimming**: Select exact frames for precision work
- **Error Recovery**: Robust error handling with helpful messages and automatic retries

### **Format Support**

- **Input Formats**: MP4, TS, AVI, MOV, MKV, WMV, FLV, WebM, and more
- **Output Formats**: MP4, AVI, MOV with customizable codecs
- **Streaming Support**: Efficient processing with stream copy when possible
- **Subtitle Preservation**: Maintain subtitle tracks during trimming

## 🛠 Installation

### **Quick Install (Recommended)**

1. **Clone or download** this repository:

   ```bash
   git clone <repository-url>
   cd video_trimmer_app
   ```

2. **Install as a package**:

   ```bash
   pip install -e .
   ```

3. **Run from anywhere**:

   ```bash
   video-trimmer          # Launch GUI with auto dependency check
   video-trimmer-cli      # Command-line interface
   video-trimmer-basic    # Basic GUI version
   ```

### **Development Installation**

1. **Install Python dependencies**:

   ```bash
   # Required dependencies
   pip install customtkinter tkinterdnd2 moviepy numpy loguru psutil
   
   # Optional dependencies (for enhanced features)
   pip install opencv-python Pillow pyyaml ffmpeg-python tqdm librosa soundfile
   
   # Or install all at once
   pip install -r requirements.txt
   ```

2. **Install FFmpeg** (strongly recommended):

   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt install ffmpeg`
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html)

   **Note**: FFmpeg provides:
   - 10-100x faster processing with stream copy
   - Hardware acceleration support
   - Advanced filtering capabilities
   - Better format compatibility

### **System Requirements**

- **Python**: 3.8 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 100MB for application + space for processed videos
- **OS**: Windows 10+, macOS 10.14+, or Linux
- **Optional**: GPU with hardware acceleration support

## 📖 Usage

### **Quick Start**

1. **Launch the application**:

   ```bash
   # GUI with automatic dependency checking
   video-trimmer
   
   # Command-line interface  
   video-trimmer-cli --help
   
   # Basic GUI version
   video-trimmer-basic
   
   # Alternative: Direct GUI launch
   video-trimmer-gui
   ```

2. **Load a video**:

   - Click "Open" or drag & drop a video file
   - Or select from "Recent" files

3. **Set trim parameters**:

   - Enter duration to trim (in seconds)
   - Choose trim from start or end
   - Select quality preset

4. **Process**:

   - Click "Add to Queue" for single videos
   - Use "Batch" for multiple videos
   - Monitor progress in real-time

### **Enhanced GUI Features**

#### **Interactive Timeline Editor**

- **Visual Timeline**: See video thumbnails across the entire duration
- **Draggable Trim Markers**: Click and drag green (start) and red (end) markers
- **Live Preview Updates**: Video preview updates instantly as you move markers
- **Precise Control**: 15-pixel detection radius for easy marker grabbing
- **Time Tooltips**: Hover over timeline to see exact time positions
- **Frame Boundaries**: Automatic prevention of seeking beyond video limits

#### **Built-in Presets**

Choose from professionally crafted presets:

- **Remove First 10s / Last 10s**: Common intro/outro trimming
- **Remove First 30s / Last 30s**: Extended intro/outro removal  
- **Quick Trim 5s (start/end)**: Fast trimming for social media content

Or create and save your own custom presets for repeated workflows.

#### **Theme Customization**

- **Appearance Modes**: Dark and Light themes
- **Color Schemes**: Blue, Green, and Dark Blue color themes
- **Instant Application**: Theme changes apply immediately (may require restart for full color theme effect)
- **Persistent Settings**: Your theme preferences are saved between sessions

#### **Main Interface**

- **Resizable Layout**: Proper window resizing with scrollable controls panel
- **File Management**: Drag & drop, recent files, smart output naming
- **Quality Control**: Original, High, Medium, Low presets with real-time quality feedback
- **Engine Selection**: FFmpeg (fast, hardware-accelerated) or MoviePy (compatible, pure Python)
- **Progress Monitoring**: Real-time processing updates with time estimates

### **Command Line Interface (CLI)**

For automation and batch processing:

```bash
video-trimmer-cli [options] input_files...
```

**CLI Options:**

```text
-d, --duration SECONDS    Duration to trim (required)
-s, --start              Trim from start (default)
-e, --end                Trim from end
-o, --output DIR         Output directory (default: same as input)
-f, --format FORMAT      Output format (mp4, avi, mov)
-q, --quality QUALITY    Quality preset (original/high/medium/low)
-j, --jobs JOBS          Parallel processing jobs (default: 2)
-v, --verbose            Detailed output
--engine ENGINE          Processing engine (ffmpeg/moviepy)
--hw-accel               Enable hardware acceleration
--prefix PREFIX          Output filename prefix
--suffix SUFFIX          Output filename suffix
--filters FILTERS        Apply video filters
--preset NAME            Use saved preset
```

**Advanced Examples:**

```bash
# Basic trimming
video-trimmer-cli -d 10 -s video.mp4

# Batch processing with quality control
video-trimmer-cli -d 5 -e -q high -j 4 *.mp4

# Hardware-accelerated processing
video-trimmer-cli -d 15 --hw-accel --engine ffmpeg video.mp4

# Apply filters while trimming
video-trimmer-cli -d 10 --filters "scale=1280:720,fps=30" input.mp4

# Use saved preset
video-trimmer-cli --preset "youtube_shorts" video.mp4

# Custom output naming
video-trimmer-cli -d 10 --prefix "short_" --suffix "_v2" *.mp4
```

## 🎯 Key Features in Detail

### **Advanced Video Processing**

#### **Trimming Capabilities**

- **Precision Trimming**: Frame-accurate selection
- **Multiple Segments**: Trim several parts from one video
- **Visual Feedback**: Timeline with thumbnails
- **Smart Detection**: Automatic scene detection
- **Batch Consistency**: Same settings across multiple files

#### **Quality Management**

- **Original Quality**: Stream copy (no re-encoding)
- **High Quality**: 8Mbps video, 192kbps audio
- **Medium Quality**: 4Mbps video, 128kbps audio
- **Low Quality**: 1.5Mbps video, 96kbps audio
- **Custom Settings**: Fine-tune codecs and bitrates

#### **Processing Engines**

1. **FFmpeg Engine (Recommended)**:

   - Hardware acceleration (CUDA, VideoToolbox, VAAPI)
   - Stream copy for instant processing
   - Advanced filtering capabilities
   - Professional codec support
   - Subtitle preservation

2. **MoviePy Engine (Fallback)**:

   - Pure Python implementation
   - Cross-platform compatibility
   - Built-in effects and transitions
   - Good for complex editing

### **User Interface Excellence**

#### **Modern Design**

- **CustomTkinter Framework**: Native-like appearance
- **Responsive Layout**: Adapts to window resizing
- **Dark/Light Themes**: Comfortable viewing
- **Intuitive Controls**: Minimal learning curve
- **Keyboard Shortcuts**: Power user efficiency

#### **Workflow Optimization**

- **Drag & Drop**: Instant file loading
- **Recent Files**: Quick access to previous work
- **Preset System**: Save common configurations
- **Auto-save**: Never lose your settings
- **Progress Tracking**: Real-time feedback

### **Professional Tools**

#### **Queue Management**

- **Add, Remove, Prioritize**: Full job control
- **Concurrent Processing**: Multiple videos simultaneously
- **Progress Monitoring**: Individual and overall progress
- **Error Recovery**: Automatic retry and reporting
- **Resource Management**: CPU and memory optimization

#### **Advanced Processing Features**

- **Audio Extraction**: Separate audio tracks
- **Thumbnail Generation**: Create preview grids
- **Filter Application**: Color correction and effects
- **Format Conversion**: Change containers and codecs
- **Metadata Preservation**: Keep original file information

### **Cloud Storage Integration**

- **Dropbox Upload**: Automatic cloud backup
- **Google Drive**: Seamless integration
- **Progress Tracking**: Upload progress monitoring
- **Auto-Organization**: Smart folder management

### **Comprehensive Format Support**

#### **Input Formats**

- **Video**: MP4, AVI, MOV, MKV, WMV, FLV, WebM, TS, M4V
- **Audio**: MP3, WAV, AAC, FLAC, OGG
- **Containers**: Most common video containers
- **Codecs**: H.264, H.265, VP9, AV1, and more

#### **Output Options**

- **Containers**: MP4, AVI, MOV, MKV
- **Video Codecs**: H.264, H.265, VP9
- **Audio Codecs**: AAC, MP3, AC3
- **Quality Levels**: Lossless to highly compressed

## 🔧 Troubleshooting

### **Installation Issues**

#### **Dependency Problems**

```bash
# Check Python version
python --version  # Should be 3.8+

# Install missing packages
pip install -r requirements.txt

# For development
pip install -e .
```

#### **FFmpeg Issues**

```bash
# Check FFmpeg installation
ffmpeg -version

# Install FFmpeg
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: Download from ffmpeg.org
```

### **Common Problems & Solutions**

#### **Performance Issues**

- **Slow Processing**: Enable hardware acceleration in settings
- **High Memory Usage**: Reduce concurrent jobs in processing settings
- **UI Lag**: Close other applications, use lower preview quality

#### **File Format Issues**

```bash
# Check supported formats using Python
python -c "from video_trimmer_app.ffmpeg_processor import AdvancedFFmpegTrimmer; print(AdvancedFFmpegTrimmer().get_supported_formats())"

# Convert unsupported format first
ffmpeg -i input.format -c copy output.mp4
```

#### **Processing Errors**

- **Permission Denied**: Check write permissions on output directory
- **Disk Space**: Ensure sufficient space (2x input file size)
- **Corrupted Files**: Try different input file or repair with FFmpeg
- **Codec Issues**: Use MoviePy engine as fallback

### **Getting Help**

#### **Debug Information**

1. **Enable Verbose Logging**: Settings → Advanced → Verbose Logging
2. **Check Log Files**: Look in `logs/video_trimmer.log`
3. **System Information**: Note OS, Python version, RAM
4. **Hardware Details**: GPU type, available storage

#### **Error Reporting**

When reporting issues, include:

- Operating system and version
- Python version (`python --version`)
- FFmpeg version (`ffmpeg -version`)
- Input file format and size
- Complete error message
- Steps to reproduce

### **Performance Optimization**

#### **Hardware Acceleration**

- **NVIDIA GPUs**: Ensure CUDA drivers installed
- **AMD GPUs**: Check VAAPI support on Linux
- **Intel GPUs**: Verify Quick Sync support
- **Apple Silicon**: VideoToolbox automatically available

#### **Memory Management**

- **Large Files**: Process one at a time
- **4K Videos**: Use original quality (stream copy)
- **Low RAM**: Reduce concurrent processing jobs
- **SSD Storage**: Use for temporary files

#### **CPU Optimization**

- **Multi-core**: Increase concurrent jobs setting
- **Single-core**: Use basic quality preset
- **Background Processing**: Enable in queue settings

## 🧪 Testing & Development

### **Running Tests**

```bash
# Create test video and run basic tests
python video_trimmer_app/test_video_trimmer.py

# Test processing efficiency (FFmpeg vs MoviePy)
python video_trimmer_app/test_efficiency.py test_video.mp4

# Test enhanced features
python video_trimmer_app/test_features.py

# Use Make commands for easier development
make test
make run
make help
```

### **Development Setup**

```bash
# Clone repository
git clone <repository-url>
cd video_trimmer_app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Run in development mode
video-trimmer              # GUI version
video-trimmer-cli --help   # CLI version
```

### **Available CLI Commands**

After installation with `pip install -e .`, these commands are available system-wide:

```bash
video-trimmer          # Main GUI launcher with dependency checking
video-trimmer-gui      # Direct GUI access
video-trimmer-cli      # Command-line interface
video-trimmer-basic    # Basic GUI version
```

### **Configuration & Customization**

#### **Settings Location**

- **Configuration**: `~/.video_trimmer/config.json`
- **Presets**: `~/.video_trimmer/presets.json`
- **Recent Files**: `~/.video_trimmer/recent_files.json`
- **Logs**: `logs/video_trimmer.log`

#### **Custom Presets**

```json
{
  "youtube_shorts": {
    "duration": "10",
    "direction": "start",
    "quality": "high",
    "engine": "ffmpeg",
    "filters": ["scale=1080:1920"]
  }
}
```

### **Development Tools**

#### **Make Commands**

```bash
make help      # Show all available commands
make install   # Install package in development mode
make run       # Launch the GUI application
make test      # Run all tests
make clean     # Clean up build artifacts
```

### **Changelog & Recent Improvements**

#### **Latest Updates (2.0.3)**

- **Fixed Timeline Interaction**: Draggable trim markers now work correctly with proper coordinate mapping
- **Real-time Preview**: Video preview updates instantly when interacting with timeline
- **Theme System**: Fixed theme loading to apply color changes properly on startup
- **Built-in Presets**: Added 6 professional presets for common trimming tasks
- **Thread Safety**: Implemented proper video access synchronization to prevent crashes
- **UI Layout**: Fixed window resizing issues and improved responsive design
- **User Experience**: Enhanced timeline with better visual markers and tooltips
- **Bug Fixes**: Resolved coordinate conversion issues and boundary checking

#### **Known Issues & Solutions**

- **Timeline Showing Blue Bar**: This has been fixed in the latest version with proper thumbnail generation
- **Preview Not Updating**: Now resolved with real-time preview system
- **Theme Changes Not Applying**: Fixed by loading themes before UI creation
- **FFmpeg Threading Crashes**: Resolved with video access locks and proper error handling

## 🛠 Latest Installation & Setup

### **Quick Install (Recommended)**

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd video_trimmer_app
   ```

2. **Install as package**:

   ```bash
   pip install -e .
   ```

3. **Launch**:

   ```bash
   video-trimmer          # GUI with dependency checking
   video-trimmer-cli      # Command-line interface  
   ```

### **Dependencies**

**Required:**

```bash
pip install customtkinter tkinterdnd2 moviepy numpy loguru psutil
```

**Optional (for enhanced features):**

```bash
pip install opencv-python Pillow pyyaml ffmpeg-python
```

**FFmpeg (Strongly Recommended):**

- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt install ffmpeg`  
- **Windows**: Download from [FFmpeg website](https://ffmpeg.org)

## � System Requirements

### **Minimum Requirements**

- **OS**: Windows 10, macOS 10.14, Ubuntu 18.04
- **Python**: 3.8 or higher
- **RAM**: 4GB
- **Storage**: 100MB + video storage  
- **CPU**: Dual-core processor

### **Recommended Specifications**

- **OS**: Latest versions
- **Python**: 3.10 or higher
- **RAM**: 8GB or more
- **Storage**: SSD with ample free space
- **CPU**: Quad-core or better
- **GPU**: Modern GPU with hardware acceleration

## 🧪 Quick Testing

After installation, test the application:

```bash
# Generate a test video and run basic functionality test
python -c "import video_trimmer_app; print('Installation successful!')"

# Launch GUI
video-trimmer

# Test CLI
video-trimmer-cli --help
```

## 📄 License

This project is released under the MIT License. See LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please:

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Follow code style**: Use PEP 8, type hints
4. **Add tests**: Include tests for new features
5. **Update docs**: Keep README current
6. **Submit PR**: Describe changes clearly

## 🙏 Acknowledgments

- **FFmpeg Team**: For the powerful multimedia framework
- **MoviePy**: For Python video editing capabilities  
- **CustomTkinter**: For the modern GUI framework
- **OpenCV**: For computer vision features

---

Made with ❤️ for video creators and developers. @j-abed

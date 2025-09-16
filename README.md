# Video Trimmer Application

A Python application for trimming video files (.mp4, .ts, etc.) from either the start or end. Features both a graphical user interface (GUI) and command-line interface (CLI) for batch processing.

## Features

- **GUI Application**: User-friendly interface for single video trimming
- **CLI Application**: Command-line tool for batch processing multiple videos
- **Multiple Format Support**: Works with MP4, TS, AVI, MOV, MKV, WMV, FLV, and WebM files
- **Flexible Trimming**: Trim from start or end of videos
- **Preview Functionality**: Preview trim settings before processing
- **Batch Processing**: Process multiple videos at once
- **Progress Tracking**: Visual progress indicators and status updates
- **Fast Trimming**: Uses FFmpeg with stream copy for lossless, high-speed trimming (when available)
- **Fallback Support**: Automatically falls back to MoviePy if FFmpeg is not available

## Installation

1. **Clone or download** this repository to your local machine

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Recommended**: Install FFmpeg for fast, lossless trimming:
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt install ffmpeg`
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html)
   
   **Note**: FFmpeg enables stream copy trimming which is 10-100x faster than re-encoding. The application will work without FFmpeg but will be slower.

## Usage

### GUI Application

Launch the graphical interface:

```bash
python video_trimmer.py
```

**GUI Features:**
- **Input Selection**: Browse and select your input video file
- **Output Selection**: Choose where to save the trimmed video
- **Duration Setting**: Specify how many seconds to trim
- **Direction Selection**: Choose to trim from start or end
- **Engine Selection**: Choose between FFmpeg (faster) or MoviePy (more compatible)
- **Preview**: See trim details before processing
- **Progress Bar**: Visual feedback during processing

**GUI Workflow:**
1. Click "Browse" to select your input video
2. The output filename will be auto-generated (you can change it)
3. Set the duration to trim (in seconds)
4. Choose whether to trim from start or end
5. Click "Update Preview" to see the trim details
6. Click "Trim Video" to process the video

### Performance Comparison

The application now supports two trimming engines:

- **FFmpeg (Recommended)**: Uses stream copy for lossless, ultra-fast trimming
- **MoviePy**: Re-encodes the entire video (slower but more compatible)

**Speed Comparison Example:**
- FFmpeg: ~2 seconds for a 1-hour video
- MoviePy: ~5-10 minutes for the same video

To test the performance difference on your system:
```bash
python test_efficiency.py your_video.mp4
```

### CLI Application

For command-line usage and batch processing:

```bash
python video_trimmer_cli.py --help
```

#### Single File Processing

```bash
# Trim 10 seconds from the start (uses FFmpeg if available)
python video_trimmer_cli.py input.mp4 output.mp4 --duration 10 --from-start

# Trim 30 seconds from the end
python video_trimmer_cli.py input.mp4 output.mp4 --duration 30 --from-end

# Force use of MoviePy instead of FFmpeg
python video_trimmer_cli.py input.mp4 output.mp4 --duration 10 --from-start --no-ffmpeg
```

#### Batch Processing

```bash
# Process all videos in a directory
python video_trimmer_cli.py --batch input_directory/ output_directory/ --duration 15 --from-start

# Process with pattern matching
python video_trimmer_cli.py --batch input_directory/ output_directory/ --duration 20 --from-end --pattern "episode"
```

#### CLI Options

- `--duration, -d`: Duration to trim in seconds (required)
- `--from-start`: Trim from start of video (default)
- `--from-end`: Trim from end of video
- `--batch INPUT_DIR OUTPUT_DIR`: Batch process all videos in INPUT_DIR
- `--pattern, -p`: Pattern to match in filenames (for batch mode)
- `--verbose, -v`: Verbose output with detailed information
- `--no-ffmpeg`: Force use of MoviePy instead of FFmpeg

## Examples

### Example 1: Remove Intro from Video
```bash
# Remove first 30 seconds from a video
python video_trimmer_cli.py movie.mp4 movie_no_intro.mp4 --duration 30 --from-start
```

### Example 2: Remove Credits from Video
```bash
# Remove last 2 minutes from a video
python video_trimmer_cli.py movie.mp4 movie_no_credits.mp4 --duration 120 --from-end
```

### Example 3: Batch Process TV Episodes
```bash
# Remove 15 seconds from start of all episodes
python video_trimmer_cli.py --batch episodes/ trimmed_episodes/ --duration 15 --from-start --pattern "episode"
```

### Example 4: GUI Usage
1. Open `video_trimmer.py`
2. Select your video file
3. Set duration to 45 seconds
4. Choose "Trim from Start"
5. Click "Update Preview" to verify settings
6. Click "Trim Video" to process

## Supported Formats

**Input Formats:**
- MP4 (.mp4)
- TS (.ts)
- AVI (.avi)
- MOV (.mov)
- MKV (.mkv)
- WMV (.wmv)
- FLV (.flv)
- WebM (.webm)

**Output Format:**
- MP4 (.mp4) with H.264 video and AAC audio codecs

## Technical Details

- **Video Processing**: Uses FFmpeg with stream copy for fast trimming (when available), falls back to MoviePy
- **Codec**: FFmpeg preserves original codec, MoviePy outputs H.264 video codec and AAC audio codec
- **Performance**: FFmpeg stream copy is 10-100x faster than re-encoding
- **Threading**: GUI uses threading to prevent UI freezing during processing
- **Error Handling**: Comprehensive error checking and user feedback
- **File Safety**: Validates input files and creates output directories as needed

## Troubleshooting

### Common Issues

1. **"No module named 'moviepy'"**
   - Install dependencies: `pip install -r requirements.txt`

2. **"FFmpeg not found"**
   - Install FFmpeg for your operating system (see Installation section)

3. **"Cannot trim X seconds"**
   - The video is shorter than the requested trim duration
   - Reduce the trim duration or check the video length

4. **"Permission denied"**
   - Ensure you have write permissions to the output directory
   - Check if the output file is not open in another application

### Performance Tips

- **Install FFmpeg** for 10-100x faster trimming using stream copy
- For large videos without FFmpeg, processing may take several minutes
- Use SSD storage for faster read/write operations
- Close other applications to free up system resources
- For batch processing, consider processing smaller batches
- Test trimming efficiency: `python test_efficiency.py your_video.mp4`

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this application.

## Requirements

- Python 3.6 or higher
- MoviePy 1.0.3 or higher
- FFmpeg (recommended for better codec support)
- Sufficient disk space for output videos

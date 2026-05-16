import sys
import shutil

def check_dependencies():
    """Ensure that native dependencies are accessible."""
    if not shutil.which("ffmpeg") and not shutil.which("ffprobe"):
        print("Warning: ffmpeg/ffprobe not found in PATH. yt-dlp might fail to extract some formats.", file=sys.stderr)

def main():
    check_dependencies()
    from sc_tui.ui.app import ScTuiApp

    app = ScTuiApp()
    app.run()

if __name__ == "__main__":
    main()

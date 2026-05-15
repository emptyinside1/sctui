import sys
import os

def check_dependencies():
    """Ensure that native dependencies are accessible."""
    import shutil

    missing = []
    if not shutil.which("mpv"):
        # In Nix, this might be available if we're in the devShell or via LD_LIBRARY_PATH
        # But for python-mpv, the library is what actually matters (libmpv.so)
        pass

    if not shutil.which("ffmpeg") and not shutil.which("ffprobe"):
        print("Warning: ffmpeg/ffprobe not found in PATH. yt-dlp might fail to extract some formats.", file=sys.stderr)

def main():
    check_dependencies()

    # Import app here so we don't load everything if dependencies check fails critically in the future
    from sc_tui.ui import ScTuiApp

    app = ScTuiApp()
    app.run()

if __name__ == "__main__":
    main()

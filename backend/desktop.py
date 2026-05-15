import os
import sys
import threading
import time
import pathlib
import multiprocessing

# 1. PREVENT SPAWN LOOPS & HANDLE SUBPROCESSES
if __name__ == '__main__':
    multiprocessing.freeze_support()
    
    # 1. SETUP PROFESSIONAL LOGGING (Fast & Persistent)
    if getattr(sys, 'frozen', False):
        app_data_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'ATS_Pro_AI')
        log_dir = os.path.join(app_data_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, "app_debug.log")
        # 'a' means APPEND - it won't delete old logs
        sys.stdout = open(log_file, "a", buffering=1)
        sys.stderr = sys.stdout
        print(f"\n--- SESSION START: {time.ctime()} ---")

    if len(sys.argv) > 1 and sys.argv[1] == '-m':
        import runpy
        module_to_run = sys.argv[2]
        sys.argv = sys.argv[2:] 
        try:
            runpy.run_module(module_to_run, run_name='__main__', alter_sys=True)
        except Exception: pass
        sys.exit(0) 

# 2. GLOBAL SILENCER (for subprocesses)
if getattr(sys, 'frozen', False) and sys.platform == 'win32':
    import subprocess
    _original_init = subprocess.Popen.__init__
    def _patched_init(self, *args, **kwargs):
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = 0x08000000 # CREATE_NO_WINDOW
        _original_init(self, *args, **kwargs)
    subprocess.Popen.__init__ = _patched_init

import webview # Keep webview at top for fast window creation

def start_backend():
    """Heavy imports are done here in a background thread."""
    print("Loading heavy modules in background...")
    import uvicorn
    # Import the app here to delay its loading
    sys.path.append(os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), 'backend'))
    from main import app
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error", timeout_keep_alive=60)

def monitor_and_switch(splash_window):
    """Wait for the backend, then swap windows."""
    import requests
    start_time = time.time()
    for _ in range(120):
        try:
            if requests.get('http://127.0.0.1:8001/health', timeout=1).status_code == 200:
                elapsed = time.time() - start_time
                if elapsed < 3.0: time.sleep(3.0 - elapsed)
                
                print("Backend ready. Swapping to Main Window...")
                
                # 1. Create the REAL Main Window (centered)
                screen = webview.screens[0]
                main_x = (screen.width - 1200) // 2
                main_y = (screen.height - 800) // 2
                
                webview.create_window(
                    'ATS Pro AI', 
                    url='http://127.0.0.1:8001',
                    width=1200,
                    height=800,
                    x=main_x,
                    y=main_y,
                    min_size=(800, 600)
                )
                
                # 2. Close the splash
                splash_window.destroy()
                return
        except: pass
        time.sleep(0.5)

if __name__ == '__main__':
    # Get loading screen path immediately
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        loading_path = os.path.join(base_path, 'backend', 'loading.html')
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        loading_path = os.path.join(base_path, 'backend', 'loading.html')
    
    loading_uri = pathlib.Path(loading_path).as_uri()

    # 0. CALCULATE CENTER POSITION
    # We use the primary monitor's dimensions
    try:
        # Some versions of webview use a different screen API
        # but this is the most common standard
        screen = webview.screens[0]
        splash_x = (screen.width - 640) // 2
        splash_y = (screen.height - 360) // 2
    except:
        # Fallback if screen detection fails
        splash_x = None
        splash_y = None

    # 1. Create the SPLASH (Centered, Frameless)
    splash = webview.create_window(
        'Starting ATS', 
        url=loading_uri,
        width=640,
        height=360,
        x=splash_x,
        y=splash_y,
        frameless=True,
        background_color='#0f172a',
        easy_drag=True
    )

    # Start backend and monitor
    threading.Thread(target=start_backend, daemon=True).start()
    threading.Thread(target=monitor_and_switch, args=(splash,), daemon=True).start()

    # Show the splash
    webview.start()

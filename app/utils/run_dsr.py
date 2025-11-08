# save this as e.g. scheduler_dsreqs.py in the same folder as dsreqs.py
from pathlib import Path
import subprocess, sys, time, datetime

SCRIPT_NAME = "dsreqs.py"
TWO_DAYS_SEC = 2 * 24 * 60 * 60  # 172800 seconds

def run_dsreqs_once() -> int:
    """Run dsreqs.py from the same directory as this file."""
    script_dir = Path(__file__).resolve().parent
    script_path = script_dir / SCRIPT_NAME
    if not script_path.exists():
        raise FileNotFoundError(f"Cannot find {SCRIPT_NAME} at {script_path}")

    # Run with the same Python interpreter; set cwd to script_dir so relative paths work.
    proc = subprocess.run(
        [sys.executable, "-u", str(script_path)],
        cwd=str(script_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    print(f"[{timestamp}] dsreqs.py exited with code {proc.returncode}")
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="")
    return proc.returncode

def run_every_two_days(start_immediately: bool = True) -> None:
    """
    Run dsreqs.py every two days in an infinite loop.
    Press Ctrl+C to stop.
    """
    try:
        next_run = time.time()
        if start_immediately:
            print('Starting dsreqs.py :', datetime.datetime.now().isoformat(timespec="seconds"))
            run_dsreqs_once()
            print('finished dsreqs.py :', datetime.datetime.now().isoformat(timespec="seconds"))
            next_run = time.time() + TWO_DAYS_SEC

        while True:
            # Sleep until the next run (accounts for execution time drift).
            sleep_for = max(0, next_run - time.time())
            time.sleep(sleep_for)
            print('Starting dsreqs.py :', datetime.datetime.now().isoformat(timespec="seconds"))
            run_dsreqs_once()
            print('finished dsreqs.py :', datetime.datetime.now().isoformat(timespec="seconds"))
            next_run += TWO_DAYS_SEC
    except KeyboardInterrupt:
        print("Stopped scheduler.")

if __name__ == "__main__":
    run_every_two_days(start_immediately=True)

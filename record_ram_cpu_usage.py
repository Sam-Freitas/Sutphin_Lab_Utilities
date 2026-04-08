import os, sys, argparse, time, shutil
from csv import writer
import psutil
from io import StringIO
# from pynput import keyboard

# default inputs
allowable_time_sec = 5
measurement_interval = 0.5
output_file = "system_metrics.csv"
buffer_flush_interval = 10

# set up input arguments
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
parser.add_argument("-t", "--timer", help="how long to run the recorder", action="store", default=allowable_time_sec)
parser.add_argument("-li", "--loop_interval", help="loop measurement interval (seconds)", action="store", default=measurement_interval)
parser.add_argument("-o", "--output", help="output CSV file path", action="store", default=output_file)
parser.add_argument("-b", "--buffer", help="rows to buffer before flushing to disk", action="store", default=buffer_flush_interval)

args = parser.parse_args()

verbose_flag = args.verbose
if verbose_flag:
    print("Verbosity turned on")

allowable_time_sec = float(args.timer)
measurement_interval = float(args.loop_interval)
buffer_flush_interval = int(args.buffer)
output_file = args.output
temp_file = output_file + ".tmp"

print(f"Timer: {allowable_time_sec}s | Interval: {measurement_interval}s | Output: {output_file}")
print("Press ESC at any time to stop early and save.")

# --- ESC key listener (runs in background thread) ---
esc_pressed = False

# def on_press(key):
#     global esc_pressed
#     if key == keyboard.Key.esc:
#         esc_pressed = True
#         return False  # stops the listener thread

# listener = keyboard.Listener(on_press=on_press)
# listener.start()

# --- CSV setup ---
header = ["timestamp", "elapsed_sec", 
        "cpu_percent",
        "swap_total","swap_used","swap_free","swap_percent",
        "ram_total", "ram_used", "ram_available", "ram_percent"]

for path in (output_file, temp_file):
    with open(path, "w", newline="") as f:
        writer(f).writerow(header)

def flush_buffer(buffer: StringIO, filepath: str):
    """Append buffer to temp file, then try to copy temp -> final. Never loses data."""
    temp_path = filepath + ".tmp"

    with open(temp_path, "a", newline="") as f:
        f.write(buffer.getvalue())

    try:
        shutil.copy2(temp_path, filepath)
    except PermissionError:
        if verbose_flag:
            print("Final file locked (Excel open?) — data safe in .tmp, will retry next flush")

    buffer.truncate(0)
    buffer.seek(0)

buffer = StringIO()
csv_writer = writer(buffer)
row_count = 0

start_time = time.time()
while True:
    loop_start = time.time()

    # Measurements
    ram = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=None)
    swap_mem = psutil.swap_memory()
    elapsed = time.time() - start_time

    row = [
        loop_start, round(elapsed, 3),
        cpu,
        swap_mem.total, swap_mem.used,swap_mem.free,swap_mem.percent,
        ram.total,ram.used,ram.available,ram.percent,
    ]

    csv_writer.writerow(row)
    row_count += 1

    if verbose_flag:
        print(row)

    # Flush buffer to disk every N rows
    if row_count >= buffer_flush_interval:
        flush_buffer(buffer, output_file)
        row_count = 0

    # Precise sleep to maintain interval
    elapsed_loop = time.time() - loop_start
    time_to_wait = measurement_interval - elapsed_loop
    if time_to_wait > 0:
        time.sleep(time_to_wait)

    # --- Exit conditions ---
    if esc_pressed:
        print("\nESC pressed — stopping early.")
        break

    if time.time() - start_time >= allowable_time_sec:
        print("\nTimer elapsed — stopping.")
        break

# --- Cleanup and final save ---
# listener.stop()  # ensure listener thread is cleaned up if timer expired first

if row_count > 0:
    flush_buffer(buffer, output_file)

if not os.path.exists(output_file) or os.path.getsize(temp_file) > os.path.getsize(output_file):
    try:
        shutil.copy2(temp_file, output_file)
    except PermissionError:
        print(f"Warning: final file still locked. Your complete data is in {temp_file}")

print(f"Done. Data written to {output_file} (temp: {temp_file})")
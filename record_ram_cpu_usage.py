import os, sys, argparse, time
from csv import writer
import psutil
from io import StringIO

# default inputs
allowable_time_sec = 5
measurement_interval = 0.5
output_file = "system_metrics.csv"
buffer_flush_interval = 10  # flush buffer to disk every N rows

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

print(f"Timer: {allowable_time_sec}s | Interval: {measurement_interval}s | Output: {output_file}")

# --- CSV setup ---
# Write header to the file once on start
with open(output_file, "w", newline="") as f:
    csv_writer = writer(f)
    csv_writer.writerow(["timestamp", "elapsed_sec", "cpu_percent",
                         "ram_total", "ram_used", "ram_available", "ram_percent"])

def flush_buffer(buffer: StringIO, filepath: str):
    """Append the in-memory buffer to the CSV file on disk, then reset it."""
    with open(filepath, "a", newline="") as f:
        f.write(buffer.getvalue())
    buffer.truncate(0)
    buffer.seek(0)

buffer = StringIO()
csv_writer = writer(buffer)
row_count = 0

start_time = time.time()
while True:
    loop_start = time.time()

    # --- Measurements ---
    ram = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=None)  # non-blocking; measurement_interval controls timing
    elapsed = time.time() - start_time

    row = [
        time.strftime("%Y-%m-%dT%H:%M:%S"),
        round(elapsed, 3),
        cpu,
        ram.total,
        ram.used,
        ram.available,
        ram.percent,
    ]

    csv_writer.writerow(row)
    row_count += 1

    if verbose_flag:
        print(row)

    # --- Flush buffer to disk every N rows ---
    if row_count >= buffer_flush_interval:
        flush_buffer(buffer, output_file)
        row_count = 0

    # --- Precise sleep to maintain interval ---
    elapsed_loop = time.time() - loop_start
    time_to_wait = measurement_interval - elapsed_loop
    if time_to_wait > 0:
        time.sleep(time_to_wait)

    if time.time() - start_time >= allowable_time_sec:
        break

# Flush any remaining rows in the buffer
if row_count > 0:
    flush_buffer(buffer, output_file)

print(f"Done. Data written to {output_file}")
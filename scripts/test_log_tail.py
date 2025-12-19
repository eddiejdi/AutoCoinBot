from pathlib import Path
import time

LOG_DIR = Path(__file__).resolve().parent.parent / "bot_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG = LOG_DIR / "test_bot.log"

MAX_BYTES = 2000


def read_from_offset(path, offset, max_bytes):
    try:
        with open(path, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            if offset is None:
                to_read = min(size, max_bytes)
                fh.seek(max(0, size - to_read))
                data = fh.read().decode(errors="ignore")
                return data, size

            # rotation detected
            if size < offset:
                fh.seek(0)
                data = fh.read().decode(errors="ignore")
                return data, size

            fh.seek(offset)
            data = fh.read(max_bytes).decode(errors="ignore")
            return data, fh.tell()
    except Exception as e:
        print("read error:", e)
        return None, offset


# write initial content
with open(LOG, "w", encoding="utf-8") as f:
    for i in range(1, 101):
        f.write(f"initial line {i}\n")

print("Initial file size:", LOG.stat().st_size)

# initial read (offset None)
data, offset = read_from_offset(LOG, None, MAX_BYTES)
print("Initial read lines:", len(data.splitlines()), "offset:", offset)
print(data.splitlines()[:3])

# append a few lines
with open(LOG, "a", encoding="utf-8") as f:
    for i in range(101, 111):
        f.write(f"appended line {i}\n")

# read new data
new_data, offset = read_from_offset(LOG, offset, MAX_BYTES)
print("After append read lines (new chunk):", len(new_data.splitlines()))
print(new_data.splitlines()[:3])

# simulate rotation/truncation
with open(LOG, "w", encoding="utf-8") as f:
    for i in range(1, 6):
        f.write(f"rotated line {i}\n")

rot_data, new_offset = read_from_offset(LOG, offset, MAX_BYTES)
print("After rotation read lines:", len(rot_data.splitlines()), "new_offset:", new_offset)
print(rot_data.splitlines()[:5])

print("Test completed.")

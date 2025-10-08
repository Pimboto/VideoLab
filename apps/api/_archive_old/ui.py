
from collections import Counter, defaultdict
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import threading
import re
import math
import batch_core as core  # processing core

VIDEO_EXT = getattr(core, "VIDEO_EXT", {".mp4", ".mov", ".m4v", ".avi", ".mkv"})
AUDIO_EXT = getattr(core, "AUDIO_EXT", {".mp3", ".wav", ".m4a"})

def list_videos(folder):
    return core.list_files(Path(folder), VIDEO_EXT) if folder and Path(folder).exists() else []

def list_audios(folder):
    return core.list_files(Path(folder), AUDIO_EXT) if folder and Path(folder).exists() else []

def list_rows(csvfile):
    return core.load_text_segments_csv(Path(csvfile)) if csvfile and Path(csvfile).exists() else []

def first_words(s, n=20):
    return re.sub(r"[^\w\s]", "", s).strip()[:n] if s else "text"

def build_all_jobs(vids, auds, rows_used):
    """Cartesian jobs (fallback when unique is OFF)."""
    jobs = []
    for vpath in vids:
        for idx, segments in enumerate(rows_used):
            if auds:
                for apath in auds:
                    jobs.append((vpath, apath, segments, idx))
            else:
                jobs.append((vpath, None, segments, idx))
    return jobs

def build_deterministic_unique_jobs(vids, auds, rows_used, want):
    """
    Deterministic per-video staggered selection:
      - Cycle through raw videos round-robin so each video gets picks evenly.
      - For each video `b`, start caption index at (b % C) and audio at (b % A).
      - For the k-th pick of that same video, advance both indices by +k (wrapping).
      - Guarantees no repeated (video, caption_idx, audio_idx) within the planned list.
    """
    V = len(vids)
    C = max(1, len(rows_used))
    A = len(auds) if auds else 1
    if V == 0:
        return []
    total_possible = V * C * A
    N = min(want, total_possible)

    # Track how many we have already assigned to each video
    picks_per_video = [0] * V
    jobs = []

    # Precompute simple index-able audio list even if None
    for t in range(N):
        b = t % V  # which base/video this turn
        k = picks_per_video[b]  # this video's local pick index
        picks_per_video[b] += 1

        start_c = b % C
        cap_idx = (start_c + k) % C

        if auds:
            start_a = b % A
            aud_idx = (start_a + k) % A
            apath = auds[aud_idx]
        else:
            apath = None

        vpath = vids[b]
        segments = rows_used[cap_idx] if C > 0 else []
        jobs.append((vpath, apath, segments, cap_idx))

    return jobs

class App:
    def __init__(self, root):
        self.root = root
        root.title("Batch Video Processor (Tkinter GUI)")

        self.videos_var = tk.StringVar()
        self.audios_var = tk.StringVar()
        self.csv_var = tk.StringVar()
        self.out_var = tk.StringVar()

        self.unique_var = tk.IntVar()
        self.unique_amount = tk.StringVar(value="100")  # user target when unique ON

        tk.Label(root, text="Videos folder").grid(row=0, column=0, sticky="w")
        tk.Entry(root, textvariable=self.videos_var, width=50).grid(row=0, column=1)
        tk.Button(root, text="Browse", command=self.pick_videos).grid(row=0, column=2)

        tk.Label(root, text="Audios folder (optional)").grid(row=1, column=0, sticky="w")
        tk.Entry(root, textvariable=self.audios_var, width=50).grid(row=1, column=1)
        tk.Button(root, text="Browse", command=self.pick_audios).grid(row=1, column=2)

        tk.Label(root, text="Texts CSV (optional)").grid(row=2, column=0, sticky="w")
        tk.Entry(root, textvariable=self.csv_var, width=50).grid(row=2, column=1)
        tk.Button(root, text="Browse", command=self.pick_csv).grid(row=2, column=2)

        tk.Label(root, text="Output folder").grid(row=3, column=0, sticky="w")
        tk.Entry(root, textvariable=self.out_var, width=50).grid(row=3, column=1)
        tk.Button(root, text="Browse", command=self.pick_out).grid(row=3, column=2)

        tk.Checkbutton(
            root,
            text="Pick most-unique BEFORE rendering (staggered per video)",
            variable=self.unique_var,
            command=self.toggle_unique,
        ).grid(row=4, column=0, columnspan=2, sticky="w")
        tk.Entry(root, textvariable=self.unique_amount, width=8, state="disabled").grid(row=4, column=2)

        self.count_label = tk.Label(root, text="Videos:0 | Captions:0 | Audios:0 | Total:0")
        self.count_label.grid(row=5, column=0, columnspan=3, sticky="w")

        self.log = tk.Text(root, height=12, width=80)
        self.log.grid(row=6, column=0, columnspan=3)

        tk.Button(root, text="Render", bg="#0E7A0D", fg="white", command=self.start_render).grid(row=7, column=0)
        tk.Button(root, text="Quit", command=root.destroy).grid(row=7, column=2)

        self.update_counts()

    def toggle_unique(self):
        st = "normal" if self.unique_var.get() else "disabled"
        self.root.grid_slaves(row=4, column=2)[0]["state"] = st

    def pick_videos(self):
        folder = filedialog.askdirectory()
        if folder:
            self.videos_var.set(folder)
            self.update_counts()

    def pick_audios(self):
        folder = filedialog.askdirectory()
        if folder:
            self.audios_var.set(folder)
            self.update_counts()

    def pick_csv(self):
        file = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if file:
            self.csv_var.set(file)
            self.update_counts()

    def pick_out(self):
        folder = filedialog.askdirectory()
        if folder:
            self.out_var.set(folder)

    def update_counts(self):
        vids = list_videos(self.videos_var.get())
        auds = list_audios(self.audios_var.get())
        rows = list_rows(self.csv_var.get())
        v = len(vids)
        r = len(rows)
        a = len(auds) if auds else 0
        total = v * (r if r > 0 else 1) * (a if a > 0 else 1)
        self.count_label.config(text=f"Videos:{v} | Captions:{r} | Audios:{a} | Total:{total}")
        return vids, auds, rows, total

    def logmsg(self, msg):
        self.log.insert("end", msg + "\n")
        self.log.see("end")

    def start_render(self):
        vids, auds, rows, total = self.update_counts()

        # At least one video + output folder
        if not vids:
            messagebox.showerror("Error", "Need at least one video.")
            return
        outd = Path(self.out_var.get()) if self.out_var.get() else None
        if not outd:
            messagebox.showerror("Error", "Select output folder.")
            return
        outd.mkdir(parents=True, exist_ok=True)

        # Use a dummy empty-segment row when there is no CSV
        rows_used = rows if rows else [[]]

        # Build jobs
        if self.unique_var.get():
            try:
                want = int(self.unique_amount.get())
            except ValueError:
                messagebox.showerror("Error", "Enter a valid number for 'most-unique' amount.")
                return
            jobs = build_deterministic_unique_jobs(vids, auds, rows_used, want)
            self.logmsg(f"Preselected {len(jobs)} jobs (staggered per video).")
        else:
            jobs = build_all_jobs(vids, auds, rows_used)

        if not jobs:
            messagebox.showerror("Error", "Nothing to render (0 jobs).")
            return

        self.log.delete("1.0", "end")
        self.logmsg(f"Rendering {len(jobs)} files...")
        threading.Thread(target=self.do_render, args=(jobs, outd), daemon=True).start()

    def do_render(self, jobs, outd):
        cfg = core.default_cfg()
        for i, (vpath, apath, segments, idx) in enumerate(jobs, 1):
            video_folder = outd / Path(vpath).stem
            video_folder.mkdir(parents=True, exist_ok=True)

            abase = apath.stem if apath else "noaudio"
            cap_key = first_words(segments[0] if segments else "text")
            safe_tbase = re.sub(r"[^\w\-_]", "_", f"combo{idx+1}_{cap_key}")[:50]
            out_path = video_folder / f"{abase}__{safe_tbase}.mp4"

            self.logmsg(f"[{i}/{len(jobs)}] {Path(vpath).name} -> {out_path.name}")
            try:
                ok = core.run_one(vpath, apath, segments, out_path, cfg)
                self.logmsg("  ✓ Done" if ok else "  ✗ Failed")
            except Exception as e:
                self.logmsg(f"  ✗ ERROR {e}")
        messagebox.showinfo("Done", "Rendering complete!")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

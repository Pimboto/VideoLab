"""
Batch Video Processor - core (portrait-safe, strict sizing)
- Always produces exact canvas size (default 1080x1920)
- Landscape inputs are center crop/zoomed to 9:16 ("cover") by default
- Final size guard before write (avoids OpenCV writer mismatches)
- Even output dimensions enforced (codec-friendly)
- Public API kept stable for ui.py:
    - VIDEO_EXT, AUDIO_EXT
    - list_files, load_text_segments_csv
    - default_cfg, run_one
    - select_jobs_diverse, job_tokens
    - process_video_with_segments(...)
"""
import csv, json, os, re, shutil, subprocess, sys, warnings
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import List, Tuple, Dict, Optional
warnings.filterwarnings("ignore")

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip

# -------------------- constants --------------------
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}
AUDIO_EXT = {".mp3", ".wav", ".m4a"}

EMOJI_FONTS = {
    "windows":  ["C:/Windows/Fonts/seguiemj.ttf", "C:/Windows/Fonts/SegoeUIEmoji.ttf"],
    "mac": ["/System/Library/Fonts/Apple Color Emoji.ttc"],
    "linux": ["/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"]
}

EMOJI_PATTERN = re.compile(
    "[\U0001F600-\U0001F64F]|"
    "[\U0001F300-\U0001F5FF]|"
    "[\U0001F680-\U0001F6FF]|"
    "[\U0001F700-\U0001F77F]|"
    "[\U0001F780-\U0001F7FF]|"
    "[\U0001F800-\U0001F8FF]|"
    "[\U00002600-\U000027BF]|"
    "[\U0001F900-\U0001F9FF]|"
    "[\U0001FA00-\U0001FA6F]|"
    "[\U0001FA70-\U0001FAFF]|"
    "[\U00002300-\U000023FF]|"
    "[\U00002B00-\U00002BFF]|"
    "[\U00010000-\U0001FFFF]|"
    "[\U0000FE0F]"
)

def find_emoji_font():
    import platform
    sysname = platform.system().lower()
    if sysname == "windows":
        fonts = EMOJI_FONTS["windows"]
    elif sysname == "darwin":
        fonts = EMOJI_FONTS["mac"]
    else:
        fonts = EMOJI_FONTS["linux"]
    for f in fonts:
        if Path(f).exists():
            return f
    for lst in EMOJI_FONTS.values():
        for f in lst:
            if Path(f).exists():
                return f
    raise FileNotFoundError("No emoji font found. Install Segoe UI Emoji (Win) or Noto Color Emoji (Linux).")

def which_or_exit():
    ffprobe = shutil.which("ffprobe") or shutil.which("ffprobe.exe")
    if not ffprobe:
        sys.exit("ERROR: Install FFmpeg and ensure 'ffprobe' is on PATH.")
    return ffprobe

FFPROBE = which_or_exit()

def run(cmd: List[str]) -> str:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n\nSTDERR:\n{p.stderr[:400]}")
    return p.stdout

def probe_video(path: Path) -> Tuple[int, int, float, float]:
    meta = run([FFPROBE, "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height,r_frame_rate",
                "-of", "json", str(path)])
    d = json.loads(meta)
    if not d.get("streams"):
        raise ValueError(f"Cannot read video: {path}")
    w = int(d["streams"][0]["width"])
    h = int(d["streams"][0]["height"])
    fps_str = d["streams"][0].get("r_frame_rate", "30/1")
    if "/" in fps_str:
        num, den = fps_str.split("/")
        den = float(den) if float(den) != 0 else 1.0
        fps = float(num) / den
    else:
        fps = float(fps_str)
    fps = min(fps, 60.0)
    dur_s = run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=nokey=1:noprint_wrappers=1", str(path)]).strip()
    dur = float(dur_s) if dur_s and dur_s != "N/A" else 0.0
    return w, h, dur, fps

def probe_audio_duration(path: Optional[Path]) -> float:
    if not path or not Path(path).exists():
        return 0.0
    try:
        dur_s = run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=nokey=1:noprint_wrappers=1", str(path)]).strip()
        return float(dur_s) if dur_s and dur_s != "N/A" else 0.0
    except Exception:
        return 0.0

def list_files(folder: Path, exts: set) -> List[Path]:
    if not folder.exists():
        return []
    return sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts])

def load_text_segments_csv(csv_path: Path) -> List[List[str]]:
    combos = []
    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader, 1):
                if not row:
                    continue
                segs = [c.strip() for c in row if c and c.strip()]
                if segs:
                    combos.append(segs)
                    print(f"  Combination {i}: {len(segs)} text segments")
    except Exception as e:
        print(f"Error reading CSV: {e}")
    return combos

def is_emoji(ch: str) -> bool:
    return bool(EMOJI_PATTERN.match(ch))

class EmojiTextRenderer:
    def __init__(self, text_font_path=None, emoji_font_path=None, font_size=48,
                 text_color=(255,255,255), outline_color=(0,0,0), outline_width=2, preset=None):
        if preset:
            self._apply_preset(preset)
        else:
            self.text_color = text_color
            self.outline_color = outline_color
            self.outline_width = outline_width
        self.font_size = font_size

        if text_font_path and Path(text_font_path).exists():
            self.text_font_path = text_font_path
        else:
            candidates = [
                "C:/USERS/JUAN ESTEBAN/APPDATA/LOCAL/MICROSOFT/WINDOWS/FONTS/FONNTS.COM-PROXIMA_NOVA_SEMIBOLD.OTF",
                "C:/Windows/Fonts/inter.ttf",
                "C:/Windows/Fonts/Inter-VariableFont_slnt,wght.ttf",
                "C:/Windows/Fonts/Arial.ttf"
            ]
            self.text_font_path = None
            for p in candidates:
                if Path(p).exists():
                    self.text_font_path = p
                    break
            if not self.text_font_path:
                print("  WARNING: No Inter/Arial found, using emoji font as fallback for text")
                self.text_font_path = find_emoji_font()

        self.emoji_font_path = emoji_font_path or find_emoji_font()
        print(f"  Text font: {Path(self.text_font_path).name}")
        print(f"  Emoji font: {Path(self.emoji_font_path).name}")

        try:
            self.text_font = ImageFont.truetype(self.text_font_path, self.font_size)
            self.emoji_font = ImageFont.truetype(self.emoji_font_path, self.font_size)
        except Exception as e:
            print(f"Error loading fonts: {e}")
            self.text_font = ImageFont.load_default()
            self.emoji_font = self.text_font

        self._render_cache: Dict[str, np.ndarray] = {}

    def _apply_preset(self, preset: str):
        presets = {
            "clean":  {"text_color":(255,255,255),"outline_color":(0,0,0),"outline_width":0},
            "bold":   {"text_color":(255,255,255),"outline_color":(0,0,0),"outline_width":3},
            "subtle": {"text_color":(255,255,255),"outline_color":(128,128,128),"outline_width":1},
            "yellow": {"text_color":(255,255,0),"outline_color":(0,0,0),"outline_width":2},
            "shadow": {"text_color":(255,255,255),"outline_color":(50,50,50),"outline_width":2},
        }
        s = presets.get(preset)
        if s:
            self.text_color = s["text_color"]; self.outline_color = s["outline_color"]; self.outline_width = s["outline_width"]
            print(f"  Applying preset: {preset}")
        else:
            print(f"  WARNING: Preset '{preset}' not found, using default config")
            self.text_color=(255,255,255); self.outline_color=(0,0,0); self.outline_width=2

    def _split_text_and_emojis(self, text: str):
        if not text: return []
        segs = []
        cur = ""
        cur_is_emoji = False
        i=0
        while i<len(text):
            ch=text[i]
            is_em = is_emoji(ch)
            if is_em:
                emoji_end=i+1
                while emoji_end<len(text) and (text[emoji_end] in '\u200d\ufe0f' or is_emoji(text[emoji_end])):
                    emoji_end+=1
                if cur and not cur_is_emoji:
                    segs.append((cur, False))
                    cur=""
                segs.append((text[i:emoji_end], True))
                i=emoji_end
            else:
                if cur_is_emoji and cur:
                    segs.append((cur, True)); cur=""
                cur+=ch; cur_is_emoji=False; i+=1
        if cur: segs.append((cur, False))
        return segs

    def _calc_line_size(self, line: str):
        segs = self._split_text_and_emojis(line)
        w=h=0
        for t,is_e in segs:
            if not t: continue
            font = self.emoji_font if is_e else self.text_font
            bbox = font.getbbox(t)
            w += (bbox[2]-bbox[0])
            h = max(h, (bbox[3]-bbox[1]))
        return w,h

    def _hard_wrap_dual_font(self, text: str, max_width: int) -> str:
        lines=[]; cur=""
        for word in text.split():
            test=(cur+" "+word).strip()
            w,_=self._calc_line_size(test)
            if w<=max_width: cur=test
            else:
                if cur: lines.append(cur)
                cur=word
        if cur: lines.append(cur)
        return "\n".join(lines)

    def render_text(self, text: str, max_width: Optional[int]=None) -> np.ndarray:
        key=f"{text}_{max_width}"
        if key in self._render_cache:
            return self._render_cache[key].copy()
        if max_width:
            text=self._hard_wrap_dual_font(text, max_width)

        lines=text.split("\n")
        line_infos=[]; max_line_w=0; total_h=0
        for line in lines:
            segs=self._split_text_and_emojis(line)
            lw=0; lh=0; seg_info=[]
            for s,is_e in segs:
                if not s: continue
                font=self.emoji_font if is_e else self.text_font
                bbox=font.getbbox(s)
                sw,sh= bbox[2]-bbox[0], bbox[3]-bbox[1]
                y_adj=int(self.font_size*0.1) if is_e else 0
                seg_info.append({"text":s,"is_emoji":is_e,"width":sw,"height":sh,"bbox":bbox,"y_adjust":y_adj})
                lw+=sw; lh=max(lh,sh)
            line_infos.append({"segments":seg_info,"width":lw,"height":lh})
            max_line_w=max(max_line_w,lw); total_h+=lh+5

        padding=self.outline_width*2+10
        W=max_line_w+padding*2; H=total_h+padding*2
        img=Image.new("RGBA",(W,H),(0,0,0,0)); draw=ImageDraw.Draw(img)
        y=padding
        for li in line_infos:
            x=padding+(max_line_w-li["width"])//2
            baseline=y+li["height"]
            for seg in li["segments"]:
                font=self.emoji_font if seg["is_emoji"] else self.text_font
                sy=baseline-seg["bbox"][3]+seg["y_adjust"]
                if seg["is_emoji"]:
                    draw.text((x,sy), seg["text"], font=font, fill=self.text_color+(255,), embedded_color=True)
                else:
                    if self.outline_width>0:
                        for dx in range(-self.outline_width, self.outline_width+1):
                            for dy in range(-self.outline_width, self.outline_width+1):
                                if dx!=0 or dy!=0:
                                    draw.text((x+dx,sy+dy), seg["text"], font=font, fill=self.outline_color+(255,), embedded_color=False)
                    draw.text((x,sy), seg["text"], font=font, fill=self.text_color+(255,), embedded_color=False)
                x+=seg["width"]
            y+=li["height"]+5

        arr=np.array(img)
        bgra=arr.copy()
        bgra[:,:,0]=arr[:,:,2]
        bgra[:,:,2]=arr[:,:,0]
        if bgra.nbytes < 50*1024*1024:
            self._render_cache[key]=bgra.copy()
        return bgra

# -------------- helpers --------------
def _even(v:int)->int: return int(v) & ~1

def _resize_cover(frame: np.ndarray, out_w:int, out_h:int) -> np.ndarray:
    h, w = frame.shape[:2]
    if w==0 or h==0: 
        return np.zeros((out_h,out_w,3), dtype=np.uint8)
    scale = max(out_w/float(w), out_h/float(h))
    new_w = max(1, int(round(w*scale)))
    new_h = max(1, int(round(h*scale)))
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    y0 = max(0, (new_h - out_h)//2); x0 = max(0, (new_w - out_w)//2)
    y1 = y0 + out_h; x1 = x0 + out_w
    cropped = resized[y0:y1, x0:x1]
    if cropped.shape[0]!=out_h or cropped.shape[1]!=out_w:
        cropped = cv2.resize(cropped, (out_w, out_h), interpolation=cv2.INTER_LINEAR)
    return cropped

def _resize_contain(frame: np.ndarray, out_w:int, out_h:int) -> np.ndarray:
    h, w = frame.shape[:2]
    if w==0 or h==0:
        return np.zeros((out_h,out_w,3), dtype=np.uint8)
    scale = min(out_w/float(w), out_h/float(h))
    new_w = max(1, int(round(w*scale)))
    new_h = max(1, int(round(h*scale)))
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    top = (out_h - new_h)//2; left = (out_w - new_w)//2
    canvas = np.zeros((out_h, out_w, 3), dtype=resized.dtype)
    canvas[top:top+new_h, left:left+new_w] = resized
    return canvas

def overlay_text_on_frame(frame: np.ndarray, text_img: np.ndarray, position: str="center", margin_pct: float=0.16)->np.ndarray:
    if text_img is None or text_img.size==0: return frame
    fh, fw = frame.shape[:2]
    th, tw = text_img.shape[:2]
    if th>fh or tw>fw:
        scale = min(fh/float(th), fw/float(tw)) * 0.9
        text_img = cv2.resize(text_img, (max(1,int(tw*scale)), max(1,int(th*scale))), interpolation=cv2.INTER_LINEAR)
        th, tw = text_img.shape[:2]
    mx = int(fw*margin_pct); my=int(fh*margin_pct)
    if position=="center":
        x=(fw-tw)//2; y=(fh-th)//2
    elif position=="bottom":
        x=(fw-tw)//2; y=fh-th-my
    elif position=="top":
        x=(fw-tw)//2; y=my
    else: x,y = position
    x=max(0, min(x, fw-tw)); y=max(0, min(y, fh-th))

    if frame.shape[2]==3 and text_img.shape[2]==4:
        roi = frame[y:y+th, x:x+tw]
        alpha = text_img[:, :, 3:4] / 255.0
        for c in range(3):
            roi[:, :, c] = roi[:, :, c]*(1-alpha[:,:,0]) + text_img[:, :, c]*alpha[:,:,0]
        frame[y:y+th, x:x+tw] = roi
    else:
        if text_img.shape[2]==4:
            alpha = text_img[:, :, 3:4] / 255.0
            text_bgr = text_img[:, :, :3] * alpha
            roi = frame[y:y+th, x:x+tw]
            frame[y:y+th, x:x+tw] = (roi*(1-alpha[:,:,0]) + text_bgr).astype(np.uint8)
        else:
            frame[y:y+th, x:x+tw] = text_img
    return frame

# -------------- main processor --------------
def process_video_with_segments(video_path: Path, output_path: Path,
                                text_segments: List[str],
                                audio_path: Optional[Path]=None,
                                renderer: Optional[EmojiTextRenderer]=None,
                                position: str="center",
                                margin_pct: float=0.16,
                                duration_policy: str="shortest",
                                fixed_seconds: Optional[float]=None,
                                canvas_size: Optional[Tuple[int,int]]=(1080,1920),
                                fit_mode: str="cover",
                                music_gain_db: int=-8,
                                mix_audio: bool=False):
    print(f"Processing: {output_path.name}")
    print(f"  Text segments: {len(text_segments)}")

    try:
        src_w, src_h, video_dur, fps = probe_video(video_path)

        if canvas_size:
            out_w, out_h = canvas_size
        else:
            out_w, out_h = src_w, src_h
        out_w, out_h = _even(out_w), _even(out_h)

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        temp_video = output_path.with_suffix(".temp.mp4")
        temp_video.parent.mkdir(parents=True, exist_ok=True)
        out = cv2.VideoWriter(str(temp_video), fourcc, fps, (out_w, out_h))
        if not out.isOpened():
            for codec in ["XVID","MJPG","MP42"]:
                fourcc = cv2.VideoWriter_fourcc(*codec)
                out = cv2.VideoWriter(str(temp_video), fourcc, fps, (out_w, out_h))
                if out.isOpened():
                    print(f"  Using codec: {codec}")
                    break
            if not out.isOpened():
                raise ValueError("Could not initialize video writer with any codec")

        if renderer is None:
            fontsize = max(18, int(out_h * 0.036))
            renderer = EmojiTextRenderer(font_size=fontsize)

        max_w = int(out_w * (1 - 2*margin_pct))
        rendered = []
        for seg in text_segments:
            try:
                rendered.append(renderer.render_text(seg, max_w))
            except Exception as e:
                print(f" Error rendering segment '{seg[:20]}...': {e}")
                rendered.append(np.zeros((100,100,4), dtype=np.uint8))

        audio_dur = probe_audio_duration(audio_path) if audio_path else 0.0
        if duration_policy == "fixed" and fixed_seconds:
            target = float(fixed_seconds)
        elif duration_policy == "audio" and audio_dur > 0:
            target = audio_dur
        elif duration_policy == "video":
            target = video_dur
        else:
            target = min(video_dur, audio_dur) if audio_dur>0 else video_dur

        seg_dur = target/len(text_segments) if text_segments else target
        print(f"  Duration per segment: {seg_dur:.2f}s")

        max_frames = int(round(target * fps))
        frame_idx = 0
        while frame_idx < max_frames:
            ok, frame = cap.read();
            if not ok:
                break

            if fit_mode in ("cover","zoom"):
                frame = _resize_cover(frame, out_w, out_h)
            elif fit_mode == "contain":
                frame = _resize_contain(frame, out_w, out_h)
            else:
                frame = cv2.resize(frame, (out_w, out_h), interpolation=cv2.INTER_LINEAR)

            if rendered:
                t = frame_idx / fps
                seg_i = min(int(t / seg_dur), len(rendered)-1) if seg_dur>0 else 0
                frame = overlay_text_on_frame(frame, rendered[seg_i], position, margin_pct)

            fh, fw = frame.shape[:2]
            if (fw != out_w) or (fh != out_h):
                interp = cv2.INTER_AREA if (fw>out_w or fh>out_h) else cv2.INTER_LINEAR
                frame = cv2.resize(frame, (out_w, out_h), interpolation=interp)

            out.write(frame)
            frame_idx += 1

        cap.release(); out.release()

        if audio_path and Path(audio_path).exists():
            print(f"  Adding audio: {Path(audio_path).name}")
            try:
                video_clip = VideoFileClip(str(temp_video))
                audio_clip = AudioFileClip(str(audio_path))
                if music_gain_db != 0:
                    volume_factor = 10**(music_gain_db/20)
                    audio_clip = audio_clip.with_volume_scaled(volume_factor)

                final_audio = CompositeAudioClip([video_clip.audio, audio_clip]) if (mix_audio and video_clip.audio) else audio_clip

                if video_clip.duration and video_clip.duration > target:
                    video_clip = video_clip.subclipped(0, target)
                if final_audio.duration and final_audio.duration > target:
                    final_audio = final_audio.subclipped(0, target)

                final_clip = video_clip.with_audio(final_audio)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                final_clip.write_videofile(str(output_path), codec="libx264", audio_codec="aac",
                                           temp_audiofile=str(output_path.parent / "temp-audio.m4a"),
                                           remove_temp=True, logger=None)
                video_clip.close(); audio_clip.close()
                if hasattr(final_clip, "close"): final_clip.close()
                if temp_video.exists():
                    try: temp_video.unlink()
                    except: pass
            except Exception as e:
                print(f"WARNING: Error with audio: {e}")
                if temp_video.exists():
                    shutil.move(str(temp_video), str(output_path))
        else:
            if temp_video.exists():
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(temp_video), str(output_path))

        print(f"  SUCCESS: Completed {output_path.name}")
        return True

    except Exception as e:
        print(f"  ERROR: Failed processing video: {e}")
        import traceback; traceback.print_exc()
        return False

# ---------------- selection utilities ----------------
def job_tokens(job):
    if isinstance(job, tuple):
        vpath, apath, segments, _ = job
    else:
        vpath = job["video"]; apath = job.get("audio"); segments = job["text_segments"]
    base = Path(vpath).stem.lower().strip()
    audio = (Path(apath).stem if apath else "noaudio").lower().strip()
    caption = re.sub(r"[^\w\s-]", "", (segments[0] if segments else "text")).lower().strip()
    return base, audio, caption

def _ratio_penalty(total, counts, key, value, target_ratio, strength):
    if total<=0: return 0.0
    cur = counts[key][value]/float(total)
    over = max(0.0, cur - target_ratio)
    return strength * over

def select_jobs_diverse(
    jobs,
    target_n,
    target_mix=None,
    ratio_strength=12.0,
    window_penalty=2.0,
    recent_window=4,
    weights=None
):
    if not jobs: return []
    if target_mix is None: target_mix={"base":0.70,"caption":0.20,"audio":0.10}
    if weights is None:
        weights = {"base":6,"audio":4,"caption":3,"combo":1,"repeat_bonus":8}

    rnd=list(jobs)
    import random; random.shuffle(rnd)

    selected=[]; used=set()
    counts={k:Counter() for k in ("base","audio","caption","combo")}
    last_bases=deque(maxlen=2); last_audios=deque(maxlen=recent_window); last_captions=deque(maxlen=recent_window)

    def score(job):
        if isinstance(job, tuple):
            vpath, apath, segs, combo_idx = job
        else:
            vpath = job["video"]; apath=job.get("audio"); segs=job["text_segments"]; combo_idx=job.get("text_combo_idx",0)
        base, audio, caption = job_tokens(job)
        s=0.0
        s += counts["base"][base]*weights["base"]
        s += counts["audio"][audio]*weights["audio"]
        s += counts["caption"][caption]*weights["caption"]
        s += counts["combo"][combo_idx]*weights["combo"]
        if base in last_bases: s += weights["repeat_bonus"]
        if audio in last_audios: s += window_penalty
        if caption in last_captions: s += window_penalty
        total=len(selected)
        s += _ratio_penalty(total, counts, "audio", audio, target_mix.get("audio",0.10), ratio_strength)
        s += _ratio_penalty(total, counts, "caption", caption, target_mix.get("caption",0.20), ratio_strength)
        s += _ratio_penalty(total, counts, "base", base, target_mix.get("base",0.70), ratio_strength*0.6)
        return s

    for _ in range(min(target_n, len(rnd))):
        avail=[j for j in rnd if id(j) not in used]
        if not avail: break
        best=min(avail, key=score)
        used.add(id(best)); selected.append(best)

        if isinstance(best, tuple):
            vpath, apath, segs, combo_idx = best
        else:
            vpath = best["video"]; apath=best.get("audio"); segs=best["text_segments"]; combo_idx=best.get("text_combo_idx",0)
        base, audio, caption = job_tokens(best)
        counts["base"][base]+=1; counts["audio"][audio]+=1; counts["caption"][caption]+=1; counts["combo"][combo_idx]+=1
        last_bases.append(base); last_audios.append(audio); last_captions.append(caption)

    return selected

# ---------------- user-facing cfg/run ----------------
def default_cfg():
    return {
        "position":"center",
        "margin_pct":0.16,
        "duration_policy":"shortest",
        "fixed_seconds":None,
        "canvas_size":(1080,1920),
        "fit_mode":"cover",
        "music_gain_db":-8,
        "mix_audio":False,
        "preset":None,
        "outline_px":2,
        "fontsize_ratio":0.036,
        "font":None,
        "emoji_font":None,
    }

def run_one(video_path, audio_path, text_segments, output_path, cfg):
    return process_video_with_segments(
        video_path=Path(video_path),
        output_path=Path(output_path),
        text_segments=text_segments,
        audio_path=Path(audio_path) if audio_path else None,
        renderer=None,
        position=cfg.get("position","center"),
        margin_pct=cfg.get("margin_pct",0.16),
        duration_policy=cfg.get("duration_policy","shortest"),
        fixed_seconds=cfg.get("fixed_seconds"),
        canvas_size=cfg.get("canvas_size",(1080,1920)),
        fit_mode=cfg.get("fit_mode","cover"),
        music_gain_db=cfg.get("music_gain_db",-8),
        mix_audio=cfg.get("mix_audio",False),
    )

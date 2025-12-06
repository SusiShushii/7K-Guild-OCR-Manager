from pathlib import Path
import re
from typing import List, Dict
import easyocr
import pandas as pd
from rapidfuzz import fuzz
import json

from .pre_image import preprocess_image_for_ocr

# ---------- CONFIG : ชื่อกิลด์ / คีย์เวิร์ดที่ไม่ใช่ชื่อคน ----------
CONFIG_PATH = Path("config.json")
if not CONFIG_PATH.exists():
    default_cfg = {
        "GUILD_NAME": "YOUR_GUILD_NAME_HERE",
        "NON_NAME_KEYWORDS": ["ท้าทาย", "ครั้ง, ","ครัง","ครั่ง","Play(s)"],
        "GUILD_EXTRA_KEYWORDS": [],
        "TIME_WORDS": ["ครั้ง","Play(s)"]
    }
    
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(default_cfg, f, indent=4, ensure_ascii=False)

    print("⚠️ สร้างไฟล์ config.json ให้ใหม่แล้ว โปรดแก้ชื่อกิลด์ก่อนรันอีกครั้ง!")
    exit(1)

with CONFIG_PATH.open("r", encoding="utf-8") as f:
    cfg = json.load(f)

GUILD_NAME: str = cfg.get("GUILD_NAME", "").strip()

BASE_NON_NAME_KEYWORDS: list[str] = cfg.get("NON_NAME_KEYWORDS", [])
GUILD_EXTRA_KEYWORDS: list[str] = cfg.get("GUILD_EXTRA_KEYWORDS", [])
TIME_WORDS: list[str] = cfg.get("TIME_WORDS", ["ครั้ง"])

# เอามารวมกันเป็นชุดเดียวที่ใช้จริง
NON_NAME_KEYWORDS: list[str] = BASE_NON_NAME_KEYWORDS + GUILD_EXTRA_KEYWORDS

# โหลด OCR ไทย/อังกฤษ ครั้งเดียวใช้ทั้งโปรเจกต์
reader = easyocr.Reader(['th', 'en'])


# ---------- Helper: normalize token ----------

def norm_token(t: str) -> str:
    # รวมทุกแบบให้กลายเป็น "ครั้ง"
    t = t.replace("ครั่ง", "ครั้ง")
    t = t.replace("ครัง", "ครั้ง")
    t = t.replace("คั้ง", "ครั้ง")
    t = re.sub(r"\s+", " ", t)          # รวม space ยาว ๆ
    t = t.strip()
    return t

def clean_number_token(t: str) -> str:
    """
    ทำความสะอาด token ที่น่าจะเป็น "เลข"
    เช่น '5,             ,726,133' -> '5,726,133'
         '4,8            889,111'  -> '4,889,111'
    """
    s = t.replace(" ", "").replace("|", "")
    # รวม comma ซ้อนกันให้เหลือตัวเดียว
    s = re.sub(r",+", ",", s)
    # ถ้าเป็นเลขล้วนกับ comma ก็คืนเลขที่สะอาด
    if re.fullmatch(r"\d{1,3}(,\d{3})*", s):
        return s
    return t

def merge_broken_numbers(tokens_raw: list[str]) -> list[str]:
    """
    รวมเลขที่แตกบรรทัด เช่น
      ['3,909', '679'] -> ['3,909,679']
    """
    tokens: list[str] = []
    i = 0
    while i < len(tokens_raw):
        tk = tokens_raw[i]

        # ถ้าเป็นรูป 1–3 หลัก + ( ,xxx )* เช่น 3,909
        if re.fullmatch(r"\d{1,3}(,\d{3})*", tk) and i + 1 < len(tokens_raw):
            nxt = tokens_raw[i + 1]
            # ตัวถัดไปเป็นเลข 3 หลัก เช่น 679
            if re.fullmatch(r"\d{3}", nxt):
                tokens.append(f"{tk},{nxt}")   # 3,909,679
                i += 2
                continue

        tokens.append(tk)
        i += 1

    return tokens

def is_guild_or_noise(t: str) -> bool:
    t = norm_token(t)
    if not t:
        return True
    if GUILD_NAME and (GUILD_NAME in t):
        return True
    for kw in NON_NAME_KEYWORDS:
        if kw in t:
            return True
    if re.fullmatch(r"[0-9,]+", t):
        return True
    return False


def is_time_like(t: str) -> bool:
    """ใช้บอกว่า token นี้น่าจะเกี่ยวกับจำนวนครั้ง/Play(s)"""
    t = norm_token(t)

    # เป็นตัวเลขล้วน เช่น "3"
    if re.fullmatch(r"\d+", t):
        return True

    # ถ้ามีคำที่กำหนดใน TIME_WORDS เช่น "ครั้ง" หรือ "Play(s)"
    for w in TIME_WORDS:
        if w.lower() in t.lower():
            return True

    return False

def find_name(tokens: List[str], i_score: int) -> str:
    """
    หา Member ย้อนหลังจากตำแหน่ง score
    ไล่ย้อนกลับ 3 ช่อง หา candidate ที่ไม่ใช่ guild / time / ตัวเลขล้วน
    """
    for j in range(i_score - 1, max(-1, i_score - 4), -1):
        if j < 0:
            break
        cand = norm_token(tokens[j])
        if not cand:
            continue
        if is_guild_or_noise(cand):
            continue
        if is_time_like(cand):
            continue
        return cand
    return "UNKNOWN"

def find_time(tokens: List[str], i_score: int) -> int:
    """
    หา Time จาก window ด้านหน้า score
    รองรับ:
    - "ท้าทาย 8 ครั้ง"
    - "8 ครั้ง"
    - "8", "ครั้ง" แยกกัน
    - "3 Play(s)"
    - "3", "Play(s)" แยกกัน
    """
    window = [norm_token(t) for t in tokens[i_score + 1:i_score + 6]]

    # 1) เคสดูเป็น [ตัวเลข, TIME_WORD]
    for k in range(len(window) - 1):
        if re.fullmatch(r"\d+", window[k]):
            for w in TIME_WORDS:
                if window[k + 1].lower().startswith(w.lower()):
                    return int(window[k])

    # 2) เคสในประโยคเดียวกัน เช่น "8 ครั้ง", "3 Play(s)"
    joined = " ".join(window)
    for w in TIME_WORDS:
        pat = rf"([0-9]+)\s*{re.escape(w)}"
        m = re.search(pat, joined, flags=re.IGNORECASE)
        if m:
            return int(m.group(1))

    # 3) ถ้าไม่มีคำ TIME_WORD เลย ก็ถือว่า 0
    return 0


def read_scores_from_image(img_path: Path, boss_name: str, mode: str):
    """
    อ่านรูป 1 ใบแล้วดึงข้อมูลคะแนนออกมา
    mode = 'boss' หรือ 'castle'
    - boss  : มี Time (จำนวนครั้งที่ท้าทาย)
    - castle: ไม่มี Time
    """
    # print(f"อ่านรูป ({mode}): {img_path}")

    # ใช้ภาพที่ preprocess แล้ว
    img_proc = preprocess_image_for_ocr(img_path)

    raw = reader.readtext(img_proc,detail=0,)

    # ทำความสะอาด token ทีเดียว
    tmp: list[str] = []
    for r in raw:
        tk = norm_token(r)
        if not tk:
            continue

        # ถ้าดูเหมือนเป็น "เลข" (มีแต่ 0-9 , space | )
        if re.fullmatch(r"[0-9,\s|]+", tk):
            tk = clean_number_token(tk)

        tmp.append(tk)
    # 2) รวมเลขที่แตกบรรทัด
    tokens = merge_broken_numbers(tmp)

    # print("OCR tokens:", tokens)  # debug

    rows: List[dict] = []

    for i, t in enumerate(tokens):
        # เจอ score เช่น "14,374,399"
        if re.fullmatch(r"[0-9,]+", t):

            name = find_name(tokens, i)

            row = {
                "Member": name,
                "Score_str": t,
                "Boss_name": boss_name,
                "Image": img_path.name,
            }

            if mode == "boss":
                row["Time"] = find_time(tokens, i)

            rows.append(row)

    return rows


# ---------- merge_similar_names (ยังต้องใช้ใน boss_guild.py) ----------

def merge_similar_names(series: pd.Series, threshold: int = 85) -> pd.Series:
    """
    รวมชื่อที่สะกดคล้ายกัน (จาก OCR) ให้ใช้ชื่อเดียวกัน
    threshold = 0-100, ยิ่งสูงยิ่งเข้มงวด
    """
    names = series.dropna().astype(str).unique().tolist()
    mapping: Dict[str, str] = {}

    for name in names:
        if name in mapping:
            continue

        canonical = name
        mapping[name] = canonical

        for other in names:
            if other == name or other in mapping:
                continue

            score = fuzz.ratio(name.lower(), other.lower())
            if score >= threshold:
                mapping[other] = canonical

    return series.map(lambda x: mapping.get(x, x))

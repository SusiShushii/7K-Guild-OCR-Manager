from pathlib import Path
import cv2
import numpy as np

def preprocess_image_for_ocr(img_path: Path):
    """
    ทำ pre-processing ภาพให้ตัวเลข/ชื่อสีขาวชัดขึ้น
    - แปลงเป็น grayscale
    - ลด noise เบา ๆ
    - เพิ่ม contrast
    - sharpen ขอบตัวหนังสือ
    - ขยายภาพเล็กน้อย
    ไม่ทำ threshold เป็นขาวดำ (คงรายละเอียดไว้)
    """
    img = cv2.imread(str(img_path))
    if img is None:
        raise ValueError(f"ไม่สามารถอ่านรูปได้: {img_path}")

    # 1) grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2) ลด noise เบา ๆ
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # 3) ดึงคอนทราสต์ให้เต็มช่วง 0-255
    gray = cv2.normalize(gray, None, alpha=0, beta=255,
                         norm_type=cv2.NORM_MINMAX)

    # 4) ใช้ CLAHE เพิ่ม local contrast (ตัวหนังสือขาวบนพื้นมืดจะเด่นขึ้น)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # # 5) unsharp mask (sharp ขอบให้คมขึ้น)
    blur = cv2.GaussianBlur(gray, (0, 0), sigmaX=1.0)
    sharp = cv2.addWeighted(gray, 1.5, blur, -0.5, 0)

    # # 6) ขยายภาพ 1.5 เท่า (ไม่ต้องเยอะ เดี๋ยวแตก)
    # sharp = cv2.resize(sharp, None, fx=1.5, fy=1.5,
    #                    interpolation=cv2.INTER_LINEAR)
    
    # ทดสอบทีละไฟล์
    # cv2.imwrite("debug_gray.png", gray)
    # cv2.imwrite("debug_sharp.png", sharp)
    return sharp

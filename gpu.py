import uvicorn
import base64, io
from collections import Counter

import numpy as np
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from PIL import Image

# Загружаем модель сразу на GPU (если CUDA доступен)
model = YOLO("best.pt")
model.to("cuda")  # <-- переносим на GPU

app = FastAPI(
    title="Car Damage Detection API",
    description="API для распознавания царапин и повреждений автомобиля",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))

@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    """Возвращает детекции, метрики (0–100), image_size и превью с боксами."""
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = image.size

    # ---- Инференс на GPU ----
    results = model(image, device="cuda:0")  # <-- здесь указываем GPU

    detections, confidences, class_list = [], [], []
    frame_area = float(w * h)

    # для sharpness
    box_areas = []

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            cls  = int(box.cls[0])
            cls_name = model.names[cls]

            detections.append({
                "bbox": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                "confidence": round(conf, 3),
                "class": cls_name
            })
            confidences.append(conf)
            class_list.append(cls_name)

            w_box = max(0.0, x2 - x1)
            h_box = max(0.0, y2 - y1)
            area  = (w_box * h_box) / frame_area if frame_area > 0 else 1.0
            box_areas.append(area)

    total = len(detections)
    avg_conf = float(np.mean(confidences)) if confidences else 0.0
    class_distribution = dict(Counter(class_list))
    unique_classes = len(class_distribution)

    quality = clamp(round(avg_conf * 100))

    if box_areas:
        avg_box_ratio = float(np.mean(box_areas))
        sharpness = clamp(round((1 - min(avg_box_ratio, 0.5) / 0.5) * 100))
    else:
        sharpness = 0

    im_small = image.resize((min(256, w), max(1, int(h * (min(256, w) / max(1, w))))), Image.BILINEAR)
    luminance = np.array(im_small.convert("L"), dtype=np.float32)
    light = clamp(round(luminance.mean() / 255 * 100))

    import math
    box_part = 70 * (math.log10(1 + max(0, total)) / math.log10(21)) if total > 0 else 0
    cls_part = min(30, unique_classes * 6)
    details = clamp(round(box_part + cls_part))

    plotted = results[0].plot()
    img_bytes = io.BytesIO()
    Image.fromarray(plotted[..., ::-1]).save(img_bytes, format="PNG")
    img_base64 = base64.b64encode(img_bytes.getvalue()).decode("utf-8")

    return JSONResponse({
        "detections": detections,
        "metrics": {
            "quality": quality,
            "sharpness": sharpness,
            "light": light,
            "details": details,
            "total_detections": total,
            "avg_confidence": round(avg_conf, 3),
            "class_distribution": class_distribution
        },
        "image_size": {"w": w, "h": h},
        "image_base64": img_base64
    })

if __name__ == "__main__":
    # запуск как обычно
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

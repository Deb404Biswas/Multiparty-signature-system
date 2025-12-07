from ultralytics import YOLO
import cv2
import numpy as np
from fastapi import HTTPException,Path
import io

class Sign_Detect_Extract:
    @staticmethod
    async def signature_detect_extract(image_bytes: bytes) -> bytes:
        model = YOLO(r"app\api\services\image_analysis\model_dependency\yolov8s.pt")
        
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail='Invalid image format')

        results = model(img)
        signature_found = False
        extracted_sign = None
        for res in results:
            boxes = res.boxes.xyxy
            scores = res.boxes.conf
            orig_img = res.orig_img
            
            if len(scores) == 0:
                continue

            idx_max = scores.argmax()
            box = boxes[idx_max]
            x1, y1, x2, y2 = map(int, box)

            crop = orig_img[y1:y2, x1:x2]
            

            success, encoded_image = cv2.imencode('.jpeg', crop)
            if success:
                extracted_sign = encoded_image.tobytes()
                signature_found = True
                print(f"Signature detected and extracted")
                break
        
        if not signature_found:
            raise HTTPException(status_code=404, detail='No signature found')
        return extracted_sign

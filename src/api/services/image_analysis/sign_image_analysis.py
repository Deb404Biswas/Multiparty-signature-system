from ultralytics import YOLO
import cv2
import os
from fastapi import HTTPException

class Sign_Detect_Extract:
    @staticmethod
    async def signature_detect_extract(img_path):
        model = YOLO(r"C:\InfinityBit\Multiparty-signature-system\src\api\services\image_analysis\model_dependency\yolov8s.pt")
        results = model(img_path)

        signature_found = False
        for res in results:
            boxes = res.boxes.xyxy
            scores = res.boxes.conf
            orig_img = res.orig_img

            if len(scores) == 0:
                continue
            else:
                idx_max=scores.argmax()
                box=boxes[idx_max]
                x1, y1, x2, y2 = map(int, box)
                crop = orig_img[y1:y2, x1:x2]
                cv2.imwrite(img_path, crop)
                signature_found = True
                print(f"Signature detected and overwritten in:{img_path}")
                break

        if not signature_found:
            raise HTTPException(status_code=403,detail='No signature found')


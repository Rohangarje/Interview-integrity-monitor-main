import cv2
import numpy as np
import os

class FaceAnalyzer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FaceAnalyzer, cls).__new__(cls)
            # Load Haar Cascade from local directory
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Check monitor/ml_models and root/ml_models
            param_paths = [
                os.path.join(base_dir, 'ml_models', 'haarcascade_frontalface_default.xml'),
                os.path.join(base_dir, '..', 'ml_models', 'haarcascade_frontalface_default.xml'),
            ]
            
            model_path = None
            for p in param_paths:
                if os.path.exists(p):
                    model_path = p
                    break
            
            if not model_path:
                 # Fallback to system path if local missing (sanity check)
                 print(f"Warning: Local model not found checked {param_paths}, using system default.")
                 model_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            
            cls._instance.face_cascade = cv2.CascadeClassifier(model_path)
        return cls._instance

    def process_frame(self, image_np):
        """
        Process a numpy image (BGR) and return face data.
        """
        gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        face_count = len(faces)
        faces_data = []
        
        for (x, y, w, h) in faces:
            faces_data.append({
                'bbox': (int(x), int(y), int(w), int(h)),
                'score': 1.0 # Haar doesn't provide probability score easily
            })

        status = 'ok'
        if face_count == 0:
            status = 'no_face'
        elif face_count > 1:
            status = 'multiple_faces'
            
        return {
            'face_count': face_count,
            'faces': faces_data,
            'status': status
        }

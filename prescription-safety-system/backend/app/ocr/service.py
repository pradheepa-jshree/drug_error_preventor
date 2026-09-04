from .preprocessing import preprocess_image
from .trocr_model import TrOCRModel
from .confidence import calculate_confidence


class OCRService:

    def __init__(self):
        self.model = TrOCRModel()

    def process(self, image_bytes: bytes):
        # Preprocess image
        image = preprocess_image(image_bytes)

        # Run TrOCR
        text = self.model.predict(image)

        # Calculate confidence
        confidence = calculate_confidence(text)

        return {
            "text": text,
            "ocr_confidence": confidence
        }
from transformers import TrOCRProcessor, VisionEncoderDecoderModel


MODEL_NAME = "microsoft/trocr-base-handwritten"


class TrOCRModel:

    def __init__(self):
        print("Loading TrOCR model...")

        self.processor = TrOCRProcessor.from_pretrained(MODEL_NAME)

        self.model = VisionEncoderDecoderModel.from_pretrained(
            MODEL_NAME
        )

        print("TrOCR model loaded.")

    def predict(self, image):
        """
        Convert handwritten prescription image into text.
        """

        pixel_values = self.processor(
            images=image,
            return_tensors="pt"
        ).pixel_values

        generated_ids = self.model.generate(
            pixel_values
        )

        text = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )[0]

        return text.strip()
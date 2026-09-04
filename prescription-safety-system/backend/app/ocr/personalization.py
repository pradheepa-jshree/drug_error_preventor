class PersonalizationStore:

    def __init__(self):
        self.corrections = {}

    def add_correction(
        self,
        doctor_id: int,
        original_text: str,
        corrected_text: str
    ):
        """
        Store a doctor's OCR correction.

        This acts as the personalization scaffold
        for future model improvement.
        """

        if doctor_id not in self.corrections:
            self.corrections[doctor_id] = []

        self.corrections[doctor_id].append({
            "original": original_text,
            "corrected": corrected_text
        })

    def get_corrections(self, doctor_id: int):
        """
        Retrieve previously stored corrections
        for a doctor.
        """

        return self.corrections.get(doctor_id, [])
import re

from app.models import (
    DrugInteraction,
    PurchaseHistory,
    LASAPair
)


# ==========================================================
# DEMO DOSAGE REFERENCE
# ==========================================================
# These are ONLY prototype/demo reference values.
# They are not intended for real clinical decision-making.

DOSAGE_RANGES = {
    "Warfarin": {
        "min_mg": 1,
        "max_mg": 10
    },
    "Spironolactone": {
        "min_mg": 25,
        "max_mg": 400
    }
}


class SafetyEngine:

    def __init__(self, db):
        self.db = db

    # ======================================================
    # 1. DRUG-DRUG INTERACTION CHECK
    # ======================================================

    def check_interactions(self, drug_ids):
        """
        Checks all combinations of prescribed drugs
        against the drug_interactions table.
        """

        alerts = []

        # Compare every drug with every other drug
        for i in range(len(drug_ids)):
            for j in range(i + 1, len(drug_ids)):

                drug_a = drug_ids[i]
                drug_b = drug_ids[j]

                interaction = (
                    self.db.query(DrugInteraction)
                    .filter(
                        (
                            (DrugInteraction.drug_a_id == drug_a) &
                            (DrugInteraction.drug_b_id == drug_b)
                        )
                        |
                        (
                            (DrugInteraction.drug_a_id == drug_b) &
                            (DrugInteraction.drug_b_id == drug_a)
                        )
                    )
                    .first()
                )

                if interaction:
                    alerts.append({
                        "drug_a_id": drug_a,
                        "drug_b_id": drug_b,
                        "severity": interaction.severity,
                        "reason": interaction.reason
                    })

        return alerts

    # ======================================================
    # 2. DOSAGE SANITY CHECK
    # ======================================================

    def check_dosage(self, drug_name, prescribed_dose):
        """
        Compares the prescribed dose with the prototype
        dosage reference.
        """

        if drug_name not in DOSAGE_RANGES:
            return {
                "status": "UNKNOWN",
                "message": "No dosage reference available for this drug."
            }

        # Extract numerical value from something like "5mg"
        match = re.search(r"\d+(\.\d+)?", str(prescribed_dose))

        if not match:
            return {
                "status": "UNKNOWN",
                "message": "Could not determine the prescribed dose."
            }

        dose = float(match.group())

        limits = DOSAGE_RANGES[drug_name]

        if limits["min_mg"] <= dose <= limits["max_mg"]:
            return {
                "status": "REFERENCE_OK",
                "message": "Dose is within the configured prototype reference range.",
                "dose_mg": dose
            }

        return {
            "status": "WARNING",
            "message": "Dose is outside the configured prototype reference range.",
            "dose_mg": dose,
            "min_mg": limits["min_mg"],
            "max_mg": limits["max_mg"]
        }
        # ======================================================
    # 3. DRUG DETAILS VALIDATION
    # ======================================================

    def validate_drug_details(
        self,
        drug,
        ocr_name,
        ocr_dosage=None
    ):
        """
        Compares OCR-extracted drug information with
        the database drug record.
        """

        results = {
            "name_match": False,
            "strength_match": False,
            "dosage_form_match": True,
            "status": "REVIEW"
        }

        # --------------------------------------------------
        # Drug name comparison
        # --------------------------------------------------

        if drug.generic_name.lower().strip() == ocr_name.lower().strip():
            results["name_match"] = True

        # --------------------------------------------------
        # Strength comparison
        # --------------------------------------------------

        if ocr_dosage and drug.strength:
            if ocr_dosage.lower().strip() == drug.strength.lower().strip():
                results["strength_match"] = True

        # --------------------------------------------------
        # Overall validation
        # --------------------------------------------------

        if results["name_match"] and results["strength_match"]:
            results["status"] = "VERIFIED"
        elif results["name_match"]:
            results["status"] = "REVIEW"

        return results

    # ======================================================
    # 3. PATIENT HISTORY CHECK
    # ======================================================

    def check_patient_history(self, patient_id, drug_ids):
        """
        Checks whether the patient has previously received
        any of the prescribed medications.
        """

        history_alerts = []

        for drug_id in drug_ids:

            previous_use = (
                self.db.query(PurchaseHistory)
                .filter(
                    PurchaseHistory.patient_id == patient_id,
                    PurchaseHistory.drug_id == drug_id
                )
                .first()
            )

            if previous_use:
                history_alerts.append({
                    "drug_id": drug_id,
                    "status": "PREVIOUSLY_USED",
                    "message": "Patient has previously received this medication."
                })

        return history_alerts

    # ======================================================
    # 4. CONTEXT-AWARE DISAMBIGUATION
    # ======================================================

    def calculate_disambiguation_score(
        self,
        spelling_score,
        phonetic_score,
        context_score=0
    ):
        """
        Combines spelling, phonetic and contextual evidence.

        Weight:
        - Spelling  : 40%
        - Phonetic  : 40%
        - Context   : 20%
        """

        final_score = (
            spelling_score * 0.4 +
            phonetic_score * 0.4 +
            context_score * 0.2
        )

        return round(final_score, 2)

    # ======================================================
    # 5. LASA / CONTEXT CHECK
    # ======================================================

    def check_lasa_candidates(
        self,
        candidate_ids,
        context_score=0
    ):
        """
        Finds LASA (Look-Alike Sound-Alike) relationships
        between candidate drugs and calculates a confidence
        score using spelling, phonetic and contextual evidence.
        """

        results = []

        for i in range(len(candidate_ids)):
            for j in range(i + 1, len(candidate_ids)):

                drug_a = candidate_ids[i]
                drug_b = candidate_ids[j]

                pair = (
                    self.db.query(LASAPair)
                    .filter(
                        (
                            (LASAPair.drug_a_id == drug_a) &
                            (LASAPair.drug_b_id == drug_b)
                        )
                        |
                        (
                            (LASAPair.drug_a_id == drug_b) &
                            (LASAPair.drug_b_id == drug_a)
                        )
                    )
                    .first()
                )

                if pair:

                    score = self.calculate_disambiguation_score(
                        pair.spelling_score,
                        pair.phonetic_score,
                        context_score
                    )

                    results.append({
                        "drug_a_id": drug_a,
                        "drug_b_id": drug_b,
                        "spelling_score": pair.spelling_score,
                        "phonetic_score": pair.phonetic_score,
                        "context_score": context_score,
                        "final_score": score,
                        "reason": pair.reason
                    })

        return results
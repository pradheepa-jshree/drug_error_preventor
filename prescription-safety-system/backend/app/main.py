from fastapi import FastAPI, UploadFile, File, Depends, Form
from sqlalchemy.orm import Session

from .database import get_db
from .safety.engine import SafetyEngine
from .models import (
    Drug,
    LASAPair,
    DrugInteraction,
    Patient,
    PurchaseHistory,
    OCRCorrection,
)
from .schemas import (
    OCRResult,
    BarcodeResponse,
    VerifyRequest,
    VerifyResponse,
    DisambiguateRequest,
    DisambiguateResponse,
    HistoryResponse,
    SafetyCheckRequest,
    SafetyCheckResponse,
    FeedbackRequest,
    FeedbackResponse,
)


app = FastAPI(
    title="LASA Guardian API",
    description="Prescription safety and drug error prevention backend",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "LASA Guardian API is running",
        "status": "ok"
    }


# ---------------------------------------------------------
# OCR
# ---------------------------------------------------------

@app.post("/ocr", response_model=list[OCRResult])
async def ocr_endpoint(file: UploadFile = File(...)):
    # Temporary response.
    # Member 1's OCR service will be connected here later.
    return [
        {
            "text": "Amlodipine",
            "dosage": "5mg",
            "frequency": "once daily",
            "ocr_confidence": 0.95
        }
    ]


# ---------------------------------------------------------
# BARCODE
# ---------------------------------------------------------

@app.post("/barcode", response_model=BarcodeResponse)
async def barcode_endpoint(
    file: UploadFile = File(...),
    gtin: str | None = Form(None),
    db: Session = Depends(get_db)
):
    # The actual barcode image decoder will be connected later.
    # For now, a GTIN can be supplied to test the DB lookup.

    if not gtin:
        return {
            "gtin": None,
            "drug_id": None,
            "generic_name": None,
            "brand_name": None,
            "found": False
        }

    drug = (
        db.query(Drug)
        .filter(Drug.barcode_gtin == gtin)
        .first()
    )

    if not drug:
        return {
            "gtin": gtin,
            "drug_id": None,
            "generic_name": None,
            "brand_name": None,
            "found": False
        }

    return {
        "gtin": drug.barcode_gtin,
        "drug_id": drug.drug_id,
        "generic_name": drug.generic_name,
        "brand_name": drug.brand_name,
        "found": True
    }


# ---------------------------------------------------------
# VERIFY OCR vs BARCODE
# ---------------------------------------------------------

@app.post("/verify", response_model=VerifyResponse)
def verify_endpoint(
    request: VerifyRequest,
    db: Session = Depends(get_db)
):
    ocr_drug = (
        db.query(Drug)
        .filter(Drug.drug_id == request.ocr_drug_id)
        .first()
    )

    barcode_drug = (
        db.query(Drug)
        .filter(Drug.drug_id == request.barcode_drug_id)
        .first()
    )

    if not ocr_drug or not barcode_drug:
        return {
            "match": False,
            "message": "One or both drug IDs were not found"
        }

    if ocr_drug.drug_id == barcode_drug.drug_id:
        return {
            "match": True,
            "message": "OCR drug and barcode drug match"
        }

    return {
        "match": False,
        "message": (
            f"OCR identified {ocr_drug.generic_name}, "
            f"but barcode identifies {barcode_drug.generic_name}"
        )
    }


# ---------------------------------------------------------
# DISAMBIGUATE LASA DRUGS
# ---------------------------------------------------------

@app.post(
    "/disambiguate",
    response_model=DisambiguateResponse
)
def disambiguate_endpoint(
    request: DisambiguateRequest,
    db: Session = Depends(get_db)
):
    engine = SafetyEngine(db)

    # No candidates
    if not request.candidates:
        return {
            "resolved": False,
            "drug": None,
            "candidates": []
        }

    # Only one candidate
    if len(request.candidates) == 1:
        return {
            "resolved": True,
            "drug": request.candidates[0],
            "candidates": request.candidates
        }

    # -----------------------------------------------------
    # CONTEXT SCORE
    # -----------------------------------------------------
    # For now, give a basic context score when context
    # information is provided.
    context_score = 50 if request.context else 0

    # -----------------------------------------------------
    # LASA SCORING
    # -----------------------------------------------------

    lasa_results = engine.check_lasa_candidates(
        request.candidates,
        context_score
    )

    # No LASA pairs found
    if not lasa_results:
        return {
            "resolved": False,
            "drug": None,
            "candidates": request.candidates
        }

    # -----------------------------------------------------
    # FIND THE STRONGEST LASA RELATIONSHIP
    # -----------------------------------------------------

    best_result = max(
        lasa_results,
        key=lambda x: x["final_score"]
    )

    # -----------------------------------------------------
    # DON'T GUESS A DRUG
    # -----------------------------------------------------

    # A high score means the candidates are very similar.
    # We should flag the ambiguity instead of randomly
    # selecting one of them.

    return {
        "resolved": False,
        "drug": None,
        "candidates": request.candidates
    }


# ---------------------------------------------------------
# PATIENT HISTORY
# ---------------------------------------------------------

@app.get(
    "/patient/{phone}/history",
    response_model=HistoryResponse
)
def patient_history(
    phone: str,
    db: Session = Depends(get_db)
):
    patient = (
        db.query(Patient)
        .filter(Patient.phone == phone)
        .first()
    )

    if not patient:
        return {
            "patient_found": False,
            "history": []
        }

    records = (
        db.query(PurchaseHistory)
        .filter(
            PurchaseHistory.patient_id == patient.patient_id
        )
        .order_by(PurchaseHistory.date_dispensed.desc())
        .all()
    )

    return {
        "patient_found": True,
        "history": [
            {
                "drug_id": record.drug_id,
                "date": str(record.date_dispensed)
            }
            for record in records
        ]
    }


# ---------------------------------------------------------
# SAFETY CHECK
# ---------------------------------------------------------

@app.post(
    "/safety-check",
    response_model=SafetyCheckResponse
)
def safety_check(
    request: SafetyCheckRequest,
    db: Session = Depends(get_db)
):
    engine = SafetyEngine(db)

    alerts = []

    # Remove duplicate drug IDs
    drug_ids = list(set(request.today_drug_ids))

    # -----------------------------------------------------
    # 1. DRUG-DRUG INTERACTION CHECK
    # -----------------------------------------------------

    interactions = engine.check_interactions(drug_ids)

    for interaction in interactions:
        alerts.append(
            f"{interaction['severity'].upper()}: "
            f"{interaction['reason']}"
        )

    # -----------------------------------------------------
    # 2. PATIENT HISTORY CHECK
    # -----------------------------------------------------

    patient = (
        db.query(Patient)
        .filter(Patient.phone == request.patient_phone)
        .first()
    )

    if patient:
        history_alerts = engine.check_patient_history(
            patient.patient_id,
            drug_ids
        )

        for history in history_alerts:
            alerts.append(
                f"PATIENT HISTORY: "
                f"{history['message']} "
                f"(Drug ID: {history['drug_id']})"
            )

    else:
        alerts.append(
            "Patient not found. Patient history could not be checked."
        )

    # -----------------------------------------------------
    # 3. DOSAGE SANITY CHECK
    # -----------------------------------------------------

    if request.dosages:

        for drug_id, prescribed_dose in request.dosages.items():

            drug = (
                db.query(Drug)
                .filter(Drug.drug_id == drug_id)
                .first()
            )

            if not drug:
                alerts.append(
                    f"Drug ID {drug_id} was not found."
                )
                continue

            dosage_result = engine.check_dosage(
                drug.generic_name,
                prescribed_dose
            )

            if dosage_result["status"] == "WARNING":
                alerts.append(
                    f"DOSAGE WARNING - "
                    f"{drug.generic_name}: "
                    f"{dosage_result['message']}"
                )

            elif dosage_result["status"] == "UNKNOWN":
                alerts.append(
                    f"DOSAGE CHECK - "
                    f"{drug.generic_name}: "
                    f"{dosage_result['message']}"
                )

    return {
        "alerts": alerts
    }


# ---------------------------------------------------------
# FEEDBACK / OCR CORRECTIONS
# ---------------------------------------------------------

@app.post(
    "/feedback",
    response_model=FeedbackResponse
)
def feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    correction = OCRCorrection(
        doctor_id=request.doctor_id,
        original_ocr_text=request.original_ocr_text,
        corrected_text=request.corrected_text,
        prescription_ref=request.prescription_ref,
    )

    db.add(correction)
    db.commit()
    db.refresh(correction)

    return {
        "stored": True
    }

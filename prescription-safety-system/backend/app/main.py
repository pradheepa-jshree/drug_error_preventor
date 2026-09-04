from fastapi import FastAPI, UploadFile, File, Depends, Form
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from .database import get_db
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    if not request.candidates:
        return {
            "resolved": False,
            "drug": None,
            "candidates": []
        }

    if len(request.candidates) == 1:
        return {
            "resolved": True,
            "drug": request.candidates[0],
            "candidates": request.candidates
        }

    # Check whether candidate pairs exist in LASA table.
    lasa_pairs = []

    for i in range(len(request.candidates)):
        for j in range(i + 1, len(request.candidates)):
            pair = (
                db.query(LASAPair)
                .filter(
                    (
                        (LASAPair.drug_a_id == request.candidates[i])
                        & (LASAPair.drug_b_id == request.candidates[j])
                    )
                    |
                    (
                        (LASAPair.drug_a_id == request.candidates[j])
                        & (LASAPair.drug_b_id == request.candidates[i])
                    )
                )
                .first()
            )

            if pair:
                lasa_pairs.append(pair)

    # If multiple candidates remain, don't guess.
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
    alerts = []

    # Check today's drugs against each other.
    drug_ids = list(set(request.today_drug_ids))

    for i in range(len(drug_ids)):
        for j in range(i + 1, len(drug_ids)):

            interaction = (
                db.query(DrugInteraction)
                .filter(
                    (
                        (DrugInteraction.drug_a_id == drug_ids[i])
                        & (DrugInteraction.drug_b_id == drug_ids[j])
                    )
                    |
                    (
                        (DrugInteraction.drug_a_id == drug_ids[j])
                        & (DrugInteraction.drug_b_id == drug_ids[i])
                    )
                )
                .first()
            )

            if interaction:
                alerts.append(
                    f"{interaction.severity.upper()}: "
                    f"{interaction.reason}"
                )

    # Check patient's previous medications.
    patient = (
        db.query(Patient)
        .filter(Patient.phone == request.patient_phone)
        .first()
    )

    if patient:
        previous_records = (
            db.query(PurchaseHistory)
            .filter(
                PurchaseHistory.patient_id == patient.patient_id
            )
            .all()
        )

        previous_drug_ids = {
            record.drug_id
            for record in previous_records
        }

        for today_drug_id in drug_ids:
            for previous_drug_id in previous_drug_ids:

                if today_drug_id == previous_drug_id:
                    continue

                interaction = (
                    db.query(DrugInteraction)
                    .filter(
                        (
                            (
                                DrugInteraction.drug_a_id
                                == today_drug_id
                            )
                            &
                            (
                                DrugInteraction.drug_b_id
                                == previous_drug_id
                            )
                        )
                        |
                        (
                            (
                                DrugInteraction.drug_a_id
                                == previous_drug_id
                            )
                            &
                            (
                                DrugInteraction.drug_b_id
                                == today_drug_id
                            )
                        )
                    )
                    .first()
                )

                if interaction:
                    alerts.append(
                        f"PATIENT HISTORY - "
                        f"{interaction.severity.upper()}: "
                        f"{interaction.reason}"
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

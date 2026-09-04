from fastapi import FastAPI, UploadFile, File

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


@app.post("/ocr", response_model=list[OCRResult])
async def ocr_endpoint(file: UploadFile = File(...)):
    return [
        {
            "text": "Amlodipine",
            "dosage": "5mg",
            "frequency": "once daily",
            "ocr_confidence": 0.95
        }
    ]


@app.post("/barcode", response_model=BarcodeResponse)
async def barcode_endpoint(file: UploadFile = File(...)):
    return {
        "gtin": "8901234500017",
        "drug_id": 1,
        "generic_name": "Amlodipine",
        "brand_name": "Amlopin",
        "found": True
    }


@app.post("/verify", response_model=VerifyResponse)
def verify_endpoint(request: VerifyRequest):
    if request.ocr_drug_id == request.barcode_drug_id:
        return {
            "match": True,
            "message": "OCR drug and barcode drug match"
        }

    return {
        "match": False,
        "message": "OCR drug and barcode drug do not match"
    }


@app.post("/disambiguate", response_model=DisambiguateResponse)
def disambiguate_endpoint(request: DisambiguateRequest):
    if len(request.candidates) == 1:
        return {
            "resolved": True,
            "drug": request.candidates[0],
            "candidates": request.candidates
        }

    return {
        "resolved": False,
        "drug": None,
        "candidates": request.candidates
    }


@app.get("/patient/{phone}/history", response_model=HistoryResponse)
def patient_history(phone: str):
    return {
        "patient_found": True,
        "history": [
            {
                "drug_id": 1,
                "date": "2026-08-01"
            },
            {
                "drug_id": 5,
                "date": "2026-08-15"
            }
        ]
    }


@app.post("/safety-check", response_model=SafetyCheckResponse)
def safety_check(request: SafetyCheckRequest):
    return {
        "alerts": []
    }


@app.post("/feedback", response_model=FeedbackResponse)
def feedback(request: FeedbackRequest):
    return {
        "stored": True
    }

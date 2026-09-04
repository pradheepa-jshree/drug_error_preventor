from pydantic import BaseModel
from typing import List, Optional


class OCRResult(BaseModel):
    text: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    ocr_confidence: float


class BarcodeResponse(BaseModel):
    gtin: Optional[str] = None
    drug_id: Optional[int] = None
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    found: bool


class VerifyRequest(BaseModel):
    ocr_drug_id: int
    barcode_drug_id: int


class VerifyResponse(BaseModel):
    match: bool
    message: str


class DisambiguateRequest(BaseModel):
    candidates: List[int]
    context: Optional[str] = None


class DisambiguateResponse(BaseModel):
    resolved: bool
    drug: Optional[int] = None
    candidates: Optional[List[int]] = None


class HistoryItem(BaseModel):
    drug_id: int
    date: str


class HistoryResponse(BaseModel):
    patient_found: bool
    history: List[HistoryItem]


class SafetyCheckRequest(BaseModel):
    today_drug_ids: List[int]
    patient_phone: str
    dosages: Optional[dict[int, str]] = None


class SafetyCheckResponse(BaseModel):
    alerts: List[str]


class FeedbackRequest(BaseModel):
    doctor_id: int
    original_ocr_text: str
    corrected_text: str
    prescription_ref: str


class FeedbackResponse(BaseModel):
    stored: bool

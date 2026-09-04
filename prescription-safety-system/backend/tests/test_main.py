import pytest
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import (
    Drug,
    LASAPair,
    DrugInteraction,
    Patient,
    PurchaseHistory,
    Doctor,
    OCRCorrection,
)


# ============================================================
# TEST DATABASE
# ============================================================

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# DATABASE OVERRIDE
# ============================================================

def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# ============================================================
# DATABASE SETUP
# ============================================================

@pytest.fixture(autouse=True)
def setup_database():

    # Start every test with a completely clean database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    # --------------------------------------------------------
    # DRUGS
    # --------------------------------------------------------

    drug1 = Drug(
        drug_id=1,
        generic_name="Amlodipine",
        brand_name="Norvasc",
        strength="5mg",
        dosage_form="Tablet",
        drug_class="Calcium Channel Blocker",
        barcode_gtin="8901234567890",
    )

    drug2 = Drug(
        drug_id=2,
        generic_name="Amoxicillin",
        brand_name="Amoxil",
        strength="500mg",
        dosage_form="Capsule",
        drug_class="Antibiotic",
        barcode_gtin="8909876543210",
    )

    drug3 = Drug(
        drug_id=3,
        generic_name="Warfarin",
        brand_name="Coumadin",
        strength="5mg",
        dosage_form="Tablet",
        drug_class="Anticoagulant",
        barcode_gtin="8905555555555",
    )

    # --------------------------------------------------------
    # PATIENT
    # --------------------------------------------------------

    patient = Patient(
        patient_id=1,
        phone="9876543210",
        name="Test Patient",
    )

    # --------------------------------------------------------
    # DOCTOR
    # --------------------------------------------------------

    doctor = Doctor(
        doctor_id=1,
        name="Dr. Test",
        clinic_name="Test Clinic",
    )

    # --------------------------------------------------------
    # DRUG INTERACTION
    # --------------------------------------------------------

    interaction = DrugInteraction(
        drug_a_id=2,
        drug_b_id=3,
        severity="high",
        reason="May increase bleeding risk",
    )

    # --------------------------------------------------------
    # PURCHASE HISTORY
    # --------------------------------------------------------

    history = PurchaseHistory(
        patient_id=1,
        drug_id=3,
        date_dispensed=date(2026, 9, 1),
    )

    # Add all test data
    db.add_all([
        drug1,
        drug2,
        drug3,
        patient,
        doctor,
        interaction,
        history,
    ])

    db.commit()
    db.close()

    yield

    # Clean database after each test
    Base.metadata.drop_all(bind=engine)


# ============================================================
# ROOT ENDPOINT
# ============================================================

def test_root():

    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "LASA Guardian API is running"
    assert data["status"] == "ok"


# ============================================================
# OCR ENDPOINT
# ============================================================

def test_ocr_endpoint():

    response = client.post(
        "/ocr",
        files={
            "file": (
                "prescription.jpg",
                b"fake image data",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1

    assert data[0]["text"] == "Amlodipine"
    assert data[0]["dosage"] == "5mg"
    assert data[0]["frequency"] == "once daily"
    assert data[0]["ocr_confidence"] == 0.95


# ============================================================
# BARCODE - WITHOUT GTIN
# ============================================================

def test_barcode_without_gtin():

    response = client.post(
        "/barcode",
        files={
            "file": (
                "barcode.jpg",
                b"fake barcode image",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["gtin"] is None
    assert data["drug_id"] is None
    assert data["generic_name"] is None
    assert data["brand_name"] is None
    assert data["found"] is False


# ============================================================
# BARCODE - KNOWN DRUG
# ============================================================

def test_barcode_known_drug():

    response = client.post(
        "/barcode",
        data={
            "gtin": "8901234567890"
        },
        files={
            "file": (
                "barcode.jpg",
                b"fake barcode image",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["gtin"] == "8901234567890"
    assert data["drug_id"] == 1
    assert data["generic_name"] == "Amlodipine"
    assert data["brand_name"] == "Norvasc"
    assert data["found"] is True


# ============================================================
# BARCODE - UNKNOWN DRUG
# ============================================================

def test_barcode_unknown_drug():

    response = client.post(
        "/barcode",
        data={
            "gtin": "9999999999999"
        },
        files={
            "file": (
                "barcode.jpg",
                b"fake barcode image",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["gtin"] == "9999999999999"
    assert data["drug_id"] is None
    assert data["generic_name"] is None
    assert data["brand_name"] is None
    assert data["found"] is False


# ============================================================
# VERIFY - MATCHING DRUGS
# ============================================================

def test_verify_matching_drugs():

    response = client.post(
        "/verify",
        json={
            "ocr_drug_id": 1,
            "barcode_drug_id": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["match"] is True
    assert data["message"] == "OCR drug and barcode drug match"


# ============================================================
# VERIFY - MISMATCHED DRUGS
# ============================================================

def test_verify_mismatched_drugs():

    response = client.post(
        "/verify",
        json={
            "ocr_drug_id": 1,
            "barcode_drug_id": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["match"] is False
    assert "Amlodipine" in data["message"]
    assert "Amoxicillin" in data["message"]


# ============================================================
# VERIFY - MISSING DRUG
# ============================================================

def test_verify_missing_drug():

    response = client.post(
        "/verify",
        json={
            "ocr_drug_id": 999,
            "barcode_drug_id": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["match"] is False
    assert data["message"] == "One or both drug IDs were not found"


# ============================================================
# DISAMBIGUATE - EMPTY CANDIDATES
# ============================================================

def test_disambiguate_empty_candidates():

    response = client.post(
        "/disambiguate",
        json={
            "candidates": []
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["resolved"] is False
    assert data["drug"] is None
    assert data["candidates"] == []


# ============================================================
# DISAMBIGUATE - SINGLE CANDIDATE
# ============================================================

def test_disambiguate_single_candidate():

    response = client.post(
        "/disambiguate",
        json={
            "candidates": [1]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["resolved"] is True
    assert data["drug"] == 1
    assert data["candidates"] == [1]


# ============================================================
# DISAMBIGUATE - MULTIPLE CANDIDATES
# ============================================================

def test_disambiguate_multiple_candidates():

    response = client.post(
        "/disambiguate",
        json={
            "candidates": [1, 2]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["resolved"] is False
    assert data["drug"] is None
    assert data["candidates"] == [1, 2]


# ============================================================
# PATIENT HISTORY - NOT FOUND
# ============================================================

def test_patient_history_not_found():

    response = client.get(
        "/patient/9999999999/history"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["patient_found"] is False
    assert data["history"] == []


# ============================================================
# PATIENT HISTORY - FOUND
# ============================================================

def test_patient_history_found():

    response = client.get(
        "/patient/9876543210/history"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["patient_found"] is True
    assert len(data["history"]) == 1

    assert data["history"][0]["drug_id"] == 3
    assert data["history"][0]["date"] == "2026-09-01"


# ============================================================
# SAFETY CHECK - NO INTERACTION
# ============================================================

def test_safety_check_no_interaction():

    response = client.post(
        "/safety-check",
        json={
            "today_drug_ids": [1, 2],
            "patient_phone": "9999999999",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["alerts"] == []


# ============================================================
# SAFETY CHECK - DRUG INTERACTION
# ============================================================

def test_safety_check_drug_interaction():

    response = client.post(
        "/safety-check",
        json={
            "today_drug_ids": [2, 3],
            "patient_phone": "9999999999",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["alerts"]) == 1

    assert (
        "HIGH: May increase bleeding risk"
        in data["alerts"][0]
    )


# ============================================================
# SAFETY CHECK - PATIENT HISTORY
# ============================================================

def test_safety_check_patient_history():

    response = client.post(
        "/safety-check",
        json={
            "today_drug_ids": [2],
            "patient_phone": "9876543210",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["alerts"]) == 1

    assert (
        "PATIENT HISTORY - HIGH: May increase bleeding risk"
        in data["alerts"][0]
    )


# ============================================================
# FEEDBACK
# ============================================================

def test_feedback():

    response = client.post(
        "/feedback",
        json={
            "doctor_id": 1,
            "original_ocr_text": "Amoxcillin",
            "corrected_text": "Amoxicillin",
            "prescription_ref": "RX-001",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["stored"] is True

    # Verify the correction was actually stored
    db = TestingSessionLocal()

    correction = (
        db.query(OCRCorrection)
        .filter(
            OCRCorrection.prescription_ref == "RX-001"
        )
        .first()
    )

    assert correction is not None
    assert correction.doctor_id == 1
    assert correction.original_ocr_text == "Amoxcillin"
    assert correction.corrected_text == "Amoxicillin"

    db.close()

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    Date,
    TIMESTAMP,
    ForeignKey,
)
from sqlalchemy.sql import func
from .database import Base


class Drug(Base):
    __tablename__ = "drugs"

    drug_id = Column(Integer, primary_key=True, index=True)
    generic_name = Column(String(120), nullable=False)
    brand_name = Column(String(120))
    strength = Column(String(40))
    dosage_form = Column(String(40))
    drug_class = Column(String(80))
    barcode_gtin = Column(String(20), unique=True)


class LASAPair(Base):
    __tablename__ = "lasa_pairs"

    id = Column(Integer, primary_key=True, index=True)
    drug_a_id = Column(Integer, ForeignKey("drugs.drug_id"))
    drug_b_id = Column(Integer, ForeignKey("drugs.drug_id"))
    spelling_score = Column(Float)
    phonetic_score = Column(Float)
    reason = Column(String(20))


class DrugInteraction(Base):
    __tablename__ = "drug_interactions"

    id = Column(Integer, primary_key=True, index=True)
    drug_a_id = Column(Integer, ForeignKey("drugs.drug_id"))
    drug_b_id = Column(Integer, ForeignKey("drugs.drug_id"))
    severity = Column(String(20))
    reason = Column(Text)


class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(15), unique=True, nullable=False)
    name = Column(String(120))


class PurchaseHistory(Base):
    __tablename__ = "purchase_history"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"))
    drug_id = Column(Integer, ForeignKey("drugs.drug_id"))
    date_dispensed = Column(Date, nullable=False)


class Doctor(Base):
    __tablename__ = "doctors"

    doctor_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120))
    clinic_name = Column(String(120))


class OCRCorrection(Base):
    __tablename__ = "ocr_corrections"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.doctor_id"))
    original_ocr_text = Column(Text)
    corrected_text = Column(Text)
    prescription_ref = Column(String(120))
    created_at = Column(TIMESTAMP, server_default=func.now())
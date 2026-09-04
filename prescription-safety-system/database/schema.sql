CREATE TABLE drugs (
    drug_id SERIAL PRIMARY KEY,
    generic_name VARCHAR(120) NOT NULL,
    brand_name VARCHAR(120),
    strength VARCHAR(40),
    dosage_form VARCHAR(40),
    drug_class VARCHAR(80),
    barcode_gtin VARCHAR(20) UNIQUE
);

CREATE TABLE lasa_pairs (
    id SERIAL PRIMARY KEY,
    drug_a_id INTEGER REFERENCES drugs(drug_id),
    drug_b_id INTEGER REFERENCES drugs(drug_id),
    spelling_score FLOAT,
    phonetic_score FLOAT,
    reason VARCHAR(20)
);

CREATE TABLE drug_interactions (
    id SERIAL PRIMARY KEY,
    drug_a_id INTEGER REFERENCES drugs(drug_id),
    drug_b_id INTEGER REFERENCES drugs(drug_id),
    severity VARCHAR(20),
    reason TEXT
);

CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    phone VARCHAR(15) UNIQUE NOT NULL,
    name VARCHAR(120)
);

CREATE TABLE purchase_history (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id),
    drug_id INTEGER REFERENCES drugs(drug_id),
    date_dispensed DATE NOT NULL
);

CREATE TABLE doctors (
    doctor_id SERIAL PRIMARY KEY,
    name VARCHAR(120),
    clinic_name VARCHAR(120)
);

CREATE TABLE ocr_corrections (
    id SERIAL PRIMARY KEY,
    doctor_id INTEGER REFERENCES doctors(doctor_id),
    original_ocr_text TEXT,
    corrected_text TEXT,
    prescription_ref VARCHAR(120),
    created_at TIMESTAMP DEFAULT now()
);

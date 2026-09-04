INSERT INTO lasa_pairs (drug_a_id, drug_b_id, spelling_score, phonetic_score, reason) VALUES
(1, 2, 85.0, 92.0, 'both'),
(1, 3, 82.0, 88.0, 'both'),
(2, 3, 78.0, 84.0, 'both'),
(3, 4, 45.0, 72.0, 'sound'),
(5, 6, 40.0, 68.0, 'sound');

INSERT INTO doctors (name, clinic_name) VALUES
('Dr. Sharma', 'City Care Clinic'),
('Dr. Priya', 'Apollo Demo Clinic');

INSERT INTO patients (phone, name) VALUES
('9876500001', 'Demo Patient One'),
('9876500002', 'Demo Patient Two');

INSERT INTO purchase_history (patient_id, drug_id, date_dispensed) VALUES
(1, 1, CURRENT_DATE - 30),
(1, 5, CURRENT_DATE - 15),
(1, 6, CURRENT_DATE - 7),
(2, 3, CURRENT_DATE - 20),
(2, 4, CURRENT_DATE - 5);

INSERT INTO drugs
(generic_name, brand_name, strength, dosage_form, drug_class, barcode_gtin)
VALUES
('Warfarin', 'Warfarin', '5mg', 'tablet', 'anticoagulant', '8901234500027'),
('Spironolactone', 'Aldactone', '25mg', 'tablet', 'potassium-sparing diuretic', '8901234500028');

INSERT INTO drug_interactions (drug_a_id, drug_b_id, severity, reason) VALUES
(10, 11, 'high', 'Aspirin and warfarin can increase bleeding risk when taken together.'),
(8, 12, 'high', 'ACE inhibitors such as lisinopril combined with spironolactone can increase potassium levels and require monitoring.');

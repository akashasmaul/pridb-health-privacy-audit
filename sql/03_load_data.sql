\set ON_ERROR_STOP on

TRUNCATE TABLE audit_log, admissions, prescriptions, diagnoses, patients, doctors RESTART IDENTITY CASCADE;

\copy doctors (doctor_id, first_name, last_name, specialty, license_number, department, is_active) FROM 'data/raw/doctors.csv' WITH (FORMAT csv, HEADER true, NULL '');
\copy patients (patient_id, first_name, last_name, dob, age, gender, blood_type, zip_code, city, marital_status, ethnicity, ssn_hash) FROM 'data/raw/patients.csv' WITH (FORMAT csv, HEADER true, NULL '');
\copy diagnoses (diagnosis_id, patient_id, icd10_code, diagnosis_name, severity, diagnosed_date, diagnosing_doctor_id, is_chronic) FROM 'data/raw/diagnoses.csv' WITH (FORMAT csv, HEADER true, NULL '');
\copy prescriptions (prescription_id, patient_id, doctor_id, drug_name, dosage, frequency, start_date, end_date, is_active) FROM 'data/raw/prescriptions.csv' WITH (FORMAT csv, HEADER true, NULL '');

SELECT setval(pg_get_serial_sequence('doctors', 'doctor_id'), COALESCE(MAX(doctor_id), 1), MAX(doctor_id) IS NOT NULL) FROM doctors;
SELECT setval(pg_get_serial_sequence('patients', 'patient_id'), COALESCE(MAX(patient_id), 1), MAX(patient_id) IS NOT NULL) FROM patients;
SELECT setval(pg_get_serial_sequence('diagnoses', 'diagnosis_id'), COALESCE(MAX(diagnosis_id), 1), MAX(diagnosis_id) IS NOT NULL) FROM diagnoses;
SELECT setval(pg_get_serial_sequence('prescriptions', 'prescription_id'), COALESCE(MAX(prescription_id), 1), MAX(prescription_id) IS NOT NULL) FROM prescriptions;


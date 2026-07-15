\set ON_ERROR_STOP on
SET client_encoding = 'UTF8';

CREATE TABLE IF NOT EXISTS patients (
    patient_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    gender VARCHAR(10) NOT NULL CHECK (gender IN ('Male', 'Female', 'Other')),
    blood_type VARCHAR(5),
    zip_code VARCHAR(10) NOT NULL,
    city VARCHAR(100) NOT NULL,
    marital_status VARCHAR(20) CHECK (marital_status IN ('Single', 'Married', 'Divorced', 'Widowed')),
    ethnicity VARCHAR(50),
    ssn_hash VARCHAR(64) CHECK (ssn_hash IS NULL OR length(ssn_hash) = 64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS doctors (
    doctor_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    license_number VARCHAR(50) UNIQUE NOT NULL,
    department VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS diagnoses (
    diagnosis_id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    icd10_code VARCHAR(10) NOT NULL,
    diagnosis_name VARCHAR(200) NOT NULL,
    severity VARCHAR(20) CHECK (severity IN ('Mild', 'Moderate', 'Severe', 'Critical')),
    diagnosed_date DATE NOT NULL,
    diagnosing_doctor_id INTEGER REFERENCES doctors(doctor_id),
    is_chronic BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS prescriptions (
    prescription_id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id INTEGER NOT NULL REFERENCES doctors(doctor_id),
    drug_name VARCHAR(200) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    frequency VARCHAR(100),
    start_date DATE NOT NULL,
    end_date DATE CHECK (end_date IS NULL OR end_date >= start_date),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS admissions (
    admission_id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id INTEGER NOT NULL REFERENCES doctors(doctor_id),
    ward VARCHAR(100) NOT NULL,
    room_number VARCHAR(20),
    admitted_date DATE NOT NULL,
    discharge_date DATE CHECK (discharge_date IS NULL OR discharge_date >= admitted_date),
    reason TEXT,
    outcome VARCHAR(50) CHECK (outcome IN ('Recovered', 'Transferred', 'Deceased', 'Ongoing'))
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE', 'SELECT')),
    row_id INTEGER,
    performed_by VARCHAR(100) NOT NULL DEFAULT current_user,
    performed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    old_values JSONB,
    new_values JSONB
);

CREATE INDEX IF NOT EXISTS idx_patients_zip ON patients(zip_code);
CREATE INDEX IF NOT EXISTS idx_patients_age ON patients(age);
CREATE INDEX IF NOT EXISTS idx_patients_gender ON patients(gender);
CREATE INDEX IF NOT EXISTS idx_diagnoses_pid ON diagnoses(patient_id);
CREATE INDEX IF NOT EXISTS idx_diagnoses_icd ON diagnoses(icd10_code);
CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_log(table_name, performed_at);

CREATE OR REPLACE FUNCTION update_updated_at() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_patients_updated_at ON patients;
CREATE TRIGGER trg_patients_updated_at BEFORE UPDATE ON patients
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

COMMENT ON TABLE patients IS 'Core patient demographics. QIs: age, gender, zip_code, marital_status, ethnicity.';
COMMENT ON TABLE diagnoses IS 'Diagnosis name is the sensitive attribute for privacy analysis.';
COMMENT ON TABLE audit_log IS 'Database audit trail; non-admin application roles are insert-only.';


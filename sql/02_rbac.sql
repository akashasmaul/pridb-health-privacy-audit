\set ON_ERROR_STOP on

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'role_admin') THEN CREATE ROLE role_admin NOLOGIN; END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'role_doctor') THEN CREATE ROLE role_doctor NOLOGIN; END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'role_nurse') THEN CREATE ROLE role_nurse NOLOGIN; END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'role_researcher') THEN CREATE ROLE role_researcher NOLOGIN; END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'role_patient_portal') THEN CREATE ROLE role_patient_portal NOLOGIN; END IF;
END $$;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO role_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO role_admin;

REVOKE SELECT, INSERT, UPDATE ON patients FROM role_doctor;
GRANT SELECT (patient_id, first_name, last_name, dob, age, gender, blood_type, zip_code, city, marital_status, ethnicity, created_at, updated_at) ON patients TO role_doctor;
GRANT INSERT (first_name, last_name, dob, age, gender, blood_type, zip_code, city, marital_status, ethnicity) ON patients TO role_doctor;
GRANT UPDATE (first_name, last_name, dob, age, gender, blood_type, zip_code, city, marital_status, ethnicity) ON patients TO role_doctor;
GRANT SELECT, INSERT, UPDATE ON diagnoses, prescriptions TO role_doctor;
GRANT SELECT ON doctors, admissions TO role_doctor;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO role_doctor;
REVOKE SELECT ON admissions, prescriptions, diagnoses FROM role_nurse;
REVOKE SELECT ON patients, diagnoses, prescriptions FROM role_patient_portal;
GRANT SELECT (patient_id, first_name, last_name, dob, age, gender) ON patients TO role_patient_portal;
GRANT SELECT (patient_id, diagnosis_name, severity, diagnosed_date) ON diagnoses TO role_patient_portal;
GRANT SELECT (patient_id, drug_name, dosage, frequency) ON prescriptions TO role_patient_portal;
GRANT INSERT ON audit_log TO role_doctor, role_nurse, role_researcher, role_patient_portal;

ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagnoses ENABLE ROW LEVEL SECURITY;
ALTER TABLE prescriptions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS admin_all_patients ON patients;
DROP POLICY IF EXISTS admin_all_diagnoses ON diagnoses;
DROP POLICY IF EXISTS admin_all_prescriptions ON prescriptions;
CREATE POLICY admin_all_patients ON patients FOR ALL TO role_admin USING (true) WITH CHECK (true);
CREATE POLICY admin_all_diagnoses ON diagnoses FOR ALL TO role_admin USING (true) WITH CHECK (true);
CREATE POLICY admin_all_prescriptions ON prescriptions FOR ALL TO role_admin USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS doctor_all_patients ON patients;
DROP POLICY IF EXISTS doctor_all_diagnoses ON diagnoses;
DROP POLICY IF EXISTS doctor_all_prescriptions ON prescriptions;
CREATE POLICY doctor_all_patients ON patients FOR ALL TO role_doctor USING (true) WITH CHECK (true);
CREATE POLICY doctor_all_diagnoses ON diagnoses FOR ALL TO role_doctor USING (true) WITH CHECK (true);
CREATE POLICY doctor_all_prescriptions ON prescriptions FOR ALL TO role_doctor USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS patient_own_record ON patients;
DROP POLICY IF EXISTS patient_own_diagnoses ON diagnoses;
DROP POLICY IF EXISTS patient_own_prescriptions ON prescriptions;
CREATE POLICY patient_own_record ON patients FOR SELECT TO role_patient_portal
USING (patient_id = NULLIF(current_setting('app.current_patient_id', true), '')::INTEGER);
CREATE POLICY patient_own_diagnoses ON diagnoses FOR SELECT TO role_patient_portal
USING (patient_id = NULLIF(current_setting('app.current_patient_id', true), '')::INTEGER);
CREATE POLICY patient_own_prescriptions ON prescriptions FOR SELECT TO role_patient_portal
USING (patient_id = NULLIF(current_setting('app.current_patient_id', true), '')::INTEGER);

REVOKE SELECT, UPDATE, DELETE, TRUNCATE ON audit_log FROM role_doctor, role_nurse, role_researcher, role_patient_portal;

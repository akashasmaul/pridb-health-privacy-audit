\set ON_ERROR_STOP on

CREATE OR REPLACE VIEW doctor_patient_view WITH (security_barrier = true) AS
SELECT p.patient_id, p.first_name, p.last_name, p.dob, p.age, p.gender,
       p.blood_type, p.zip_code, p.city, p.marital_status,
       d.diagnosis_id, d.icd10_code, d.diagnosis_name, d.severity,
       d.diagnosed_date, d.is_chronic
FROM patients p LEFT JOIN diagnoses d ON p.patient_id = d.patient_id;
GRANT SELECT ON doctor_patient_view TO role_doctor;

CREATE OR REPLACE VIEW nurse_ward_view WITH (security_barrier = true) AS
SELECT p.age, p.gender, p.blood_type, a.ward, a.room_number,
       a.admitted_date, a.outcome, pr.drug_name, pr.dosage,
       pr.frequency, pr.is_active AS prescription_active
FROM patients p
JOIN admissions a ON p.patient_id = a.patient_id
LEFT JOIN prescriptions pr ON p.patient_id = pr.patient_id AND pr.is_active;
GRANT SELECT ON nurse_ward_view TO role_nurse;

CREATE OR REPLACE VIEW researcher_anon_view WITH (security_barrier = true) AS
SELECT CASE
           WHEN age BETWEEN 0 AND 17 THEN '0-17'
           WHEN age BETWEEN 18 AND 30 THEN '18-30'
           WHEN age BETWEEN 31 AND 45 THEN '31-45'
           WHEN age BETWEEN 46 AND 60 THEN '46-60'
           WHEN age BETWEEN 61 AND 75 THEN '61-75'
           ELSE '76+'
       END AS age_group,
       gender,
       LEFT(zip_code, 3) || 'XX' AS zip_prefix,
       d.diagnosis_name AS sensitive_attribute,
       d.severity,
       d.is_chronic
FROM patients p JOIN diagnoses d ON p.patient_id = d.patient_id;
GRANT SELECT ON researcher_anon_view TO role_researcher;

-- SECURITY INVOKER is essential: the portal view must preserve base-table RLS.
CREATE OR REPLACE VIEW patient_self_view WITH (security_invoker = true, security_barrier = true) AS
SELECT p.patient_id, p.first_name, p.last_name, p.dob, p.age, p.gender,
       d.diagnosis_name, d.severity, d.diagnosed_date,
       pr.drug_name, pr.dosage, pr.frequency
FROM patients p
LEFT JOIN diagnoses d ON p.patient_id = d.patient_id
LEFT JOIN prescriptions pr ON p.patient_id = pr.patient_id;
GRANT SELECT ON patient_self_view TO role_patient_portal;


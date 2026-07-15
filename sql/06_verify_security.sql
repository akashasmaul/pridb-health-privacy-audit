\set ON_ERROR_STOP on

DO $$
BEGIN
    IF (SELECT count(*) FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('patients','doctors','diagnoses','prescriptions','admissions','audit_log')) <> 6 THEN
        RAISE EXCEPTION 'Expected six PriDB-Health tables';
    END IF;
    IF (SELECT count(*) FROM pg_policies WHERE schemaname = 'public') < 9 THEN
        RAISE EXCEPTION 'Expected at least nine RLS policies';
    END IF;
    IF has_column_privilege('role_doctor', 'patients', 'ssn_hash', 'SELECT') THEN
        RAISE EXCEPTION 'Least-privilege failure: doctor can read SSN hash';
    END IF;
    IF has_table_privilege('role_nurse', 'diagnoses', 'SELECT') THEN
        RAISE EXCEPTION 'Least-privilege failure: nurse can read diagnoses base table';
    END IF;
    IF NOT has_table_privilege('role_nurse', 'nurse_ward_view', 'SELECT') THEN
        RAISE EXCEPTION 'Nurse cannot read approved ward view';
    END IF;
    IF has_table_privilege('role_researcher', 'patients', 'SELECT') THEN
        RAISE EXCEPTION 'Least-privilege failure: researcher can read patients';
    END IF;
    IF has_column_privilege('role_patient_portal', 'patients', 'ssn_hash', 'SELECT') THEN
        RAISE EXCEPTION 'Least-privilege failure: portal can read SSN hash';
    END IF;
    IF has_table_privilege('role_doctor', 'audit_log', 'DELETE') THEN
        RAISE EXCEPTION 'Audit immutability failure: doctor can delete audit events';
    END IF;
END $$;

SET ROLE role_patient_portal;
SET app.current_patient_id = '1';
DO $$
BEGIN
    IF (SELECT count(DISTINCT patient_id) FROM patient_self_view) > 1 THEN
        RAISE EXCEPTION 'RLS leak: patient portal returned another patient';
    END IF;
END $$;
RESET ROLE;

SET ROLE role_researcher;
SELECT count(*) AS researcher_rows FROM researcher_anon_view;
RESET ROLE;

SELECT 'SECURITY_VERIFIED' AS result;

\set ON_ERROR_STOP on

CREATE OR REPLACE FUNCTION fn_audit_row() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public AS $$
DECLARE
    changed_id INTEGER;
BEGIN
    changed_id := CASE WHEN TG_OP = 'DELETE'
        THEN (to_jsonb(OLD) ->> TG_ARGV[0])::INTEGER
        ELSE (to_jsonb(NEW) ->> TG_ARGV[0])::INTEGER END;
    INSERT INTO public.audit_log(table_name, operation, row_id, performed_by, old_values, new_values)
    VALUES (
        TG_TABLE_NAME,
        TG_OP,
        changed_id,
        session_user,
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN to_jsonb(OLD) END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW) END
    );
    RETURN COALESCE(NEW, OLD);
END;
$$;

DROP TRIGGER IF EXISTS trg_audit_patients ON patients;
CREATE TRIGGER trg_audit_patients AFTER INSERT OR UPDATE OR DELETE ON patients
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('patient_id');

DROP TRIGGER IF EXISTS trg_audit_diagnoses ON diagnoses;
CREATE TRIGGER trg_audit_diagnoses AFTER INSERT OR UPDATE OR DELETE ON diagnoses
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('diagnosis_id');

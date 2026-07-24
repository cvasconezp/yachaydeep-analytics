-- ============================================================================
-- Vista de solo lectura para que Yachay Deep Analytics consuma Core SIN PII.
-- ============================================================================
--
-- POR QUÉ: el motor de analytics recibe ANALYTICS_DB_URL y ejecuta SELECTs. Si esa URL
-- apunta a las tablas reales de Core, una métrica mal definida podría devolver una cédula
-- o un correo. Estas vistas exponen SOLO las columnas que las 8 métricas necesitan —
-- ninguna PII — y un usuario de BD de solo lectura garantiza que el motor no pueda escribir.
--
-- Las 8 métricas de apps/core.py leen de: students, enrollments, grades, course_configs.
-- Se crean vistas con el MISMO nombre de tabla que esperan las métricas, en un esquema
-- aparte (analytics_ro), y se apunta ANALYTICS_DB_URL a ese esquema.
-- ----------------------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS analytics_ro;

-- students → solo id, carrera, periodo (NADA de cédula, nombre, correo, teléfono, etnia…)
CREATE OR REPLACE VIEW analytics_ro.students AS
SELECT id, carrera, periodo
FROM public.students
WHERE retirado IS NOT TRUE;          -- los retirados no cuentan (coherente con Core)

-- enrollments → docente/asignatura/carrera/periodo (docente es dato académico, no PII de alumno)
CREATE OR REPLACE VIEW analytics_ro.enrollments AS
SELECT student_id, docente, asignatura, carrera, periodo
FROM public.enrollments;

-- grades → asignatura/docente/carrera/nota/periodo
CREATE OR REPLACE VIEW analytics_ro.grades AS
SELECT student_id, asignatura, docente, carrera, nota_final, periodo
FROM public.grades;

-- course_configs → código de aula y carrera
CREATE OR REPLACE VIEW analytics_ro.course_configs AS
SELECT codigo_avac, carrera
FROM public.course_configs;

-- ----------------------------------------------------------------------------
-- Usuario de SOLO LECTURA para el motor. Cambia 'CLAVE_FUERTE_AQUI'.
-- ANALYTICS_DB_URL usará este usuario y el search_path a analytics_ro.
-- ----------------------------------------------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'analytics_reader') THEN
    CREATE ROLE analytics_reader LOGIN PASSWORD 'CLAVE_FUERTE_AQUI';
  END IF;
END $$;

GRANT USAGE ON SCHEMA analytics_ro TO analytics_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics_ro TO analytics_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics_ro GRANT SELECT ON TABLES TO analytics_reader;
-- Que este usuario resuelva las vistas por nombre simple (students, grades…)
ALTER ROLE analytics_reader SET search_path = analytics_ro;

-- Blindaje: NO dar acceso a public (donde vive la PII)
REVOKE ALL ON SCHEMA public FROM analytics_reader;

-- ----------------------------------------------------------------------------
-- La cadena para ANALYTICS_DB_URL (Railway del backend de analytics):
--   postgresql://analytics_reader:CLAVE_FUERTE_AQUI@HOST:PUERTO/BASE
-- Verifica que el motor solo ve las vistas:
--   SET ROLE analytics_reader;  SELECT * FROM students LIMIT 1;   -- debe funcionar
--   SELECT cedula FROM public.students LIMIT 1;                    -- debe FALLAR (permiso)
-- ----------------------------------------------------------------------------

-- Direct SQL queries to test the database
-- Run these in your PostgreSQL client (pgAdmin, DBeaver, psql, etc.)

-- 1. Check if USUARIOS table exists (try both cases)
SELECT 
    table_name, 
    table_schema 
FROM information_schema.tables 
WHERE table_name IN ('USUARIOS', 'usuarios')
ORDER BY table_name;

-- 2. Check table structure
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'USUARIOS' OR table_name = 'usuarios'
ORDER BY ordinal_position;

-- 3. Count records in USUARIOS
SELECT COUNT(*) as total_usuarios FROM USUARIOS;
-- If above fails, try:
-- SELECT COUNT(*) as total_usuarios FROM usuarios;

-- 4. Sample records from USUARIOS
SELECT 
    cod_usuario, 
    nom_usuario, 
    flg_ativo 
FROM USUARIOS 
LIMIT 10;
-- If above fails, try:
-- SELECT cod_usuario, nom_usuario, flg_ativo FROM usuarios LIMIT 10;

-- 5. Test the exact query used by the backend
SELECT 
    u.cod_usuario as cod_vendedor,
    u.nom_usuario as nom_vendedor,
    CASE 
        WHEN u.flg_ativo = 'S' THEN true 
        ELSE false 
    END as ativo
FROM USUARIOS u
WHERE u.cod_usuario IS NOT NULL
ORDER BY u.nom_usuario
LIMIT 10;

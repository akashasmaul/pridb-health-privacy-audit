param(
    [string]$PostgresRoot = 'D:\App_Installation_Folder\PostgreSQL\18',
    [string]$SuperuserPassword = $env:PGSUPER_PASSWORD
)

$ErrorActionPreference = 'Stop'
$Psql = Join-Path $PostgresRoot 'bin\psql.exe'
if (-not (Test-Path -LiteralPath $Psql)) { throw "psql.exe not found at $Psql" }
if ([string]::IsNullOrWhiteSpace($SuperuserPassword)) { throw 'Provide -SuperuserPassword or set PGSUPER_PASSWORD.' }

$env:PGPASSWORD = $SuperuserPassword
& $Psql -X -v ON_ERROR_STOP=1 -U postgres -d postgres `
    -v DB_NAME=pridb_health -v DB_USER=pridb_admin -v DB_PASSWORD=pridb_secure_2024 `
    -f sql/00_bootstrap.sql
if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL bootstrap failed' }

$env:PGPASSWORD = 'pridb_secure_2024'
& $Psql -X -v ON_ERROR_STOP=1 -U pridb_admin -d pridb_health -f sql/01_schema.sql
if ($LASTEXITCODE -ne 0) { throw 'Schema creation failed' }

$env:PGPASSWORD = $SuperuserPassword
& $Psql -X -v ON_ERROR_STOP=1 -U postgres -d pridb_health -f sql/02_rbac.sql
if ($LASTEXITCODE -ne 0) { throw 'RBAC creation failed' }

$env:PGPASSWORD = 'pridb_secure_2024'
& $Psql -X -v ON_ERROR_STOP=1 -U pridb_admin -d pridb_health -f sql/04_views.sql
& $Psql -X -v ON_ERROR_STOP=1 -U pridb_admin -d pridb_health -f sql/05_audit_log.sql
& $Psql -X -v ON_ERROR_STOP=1 -U pridb_admin -d pridb_health -f sql/03_load_data.sql
if ($LASTEXITCODE -ne 0) { throw 'View, audit, or data load failed' }

$env:PGPASSWORD = $SuperuserPassword
& $Psql -X -v ON_ERROR_STOP=1 -U postgres -d pridb_health -f sql/06_verify_security.sql
if ($LASTEXITCODE -ne 0) { throw 'Security verification failed' }
Remove-Item Env:PGPASSWORD
Write-Output 'PostgreSQL setup and security verification complete.'

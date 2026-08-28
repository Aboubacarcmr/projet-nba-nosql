param(
    [string]$EnvFile = ".env",
    [string]$Out = "backups"
)

if (!(Test-Path $EnvFile)) {
    throw "Fichier .env introuvable. Copiez .env.example en .env et renseignez ATLAS_URI."
}

Get-Content $EnvFile | ForEach-Object {
    if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
    }
}

if (!$env:ATLAS_URI) {
    throw "ATLAS_URI absent dans .env"
}

$dbName = if ($env:DB_NAME) { $env:DB_NAME } else { "nba" }
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$target = Join-Path $Out $stamp

New-Item -ItemType Directory -Force $target | Out-Null
mongodump --uri "$env:ATLAS_URI" --db $dbName --out $target
Write-Host "Sauvegarde terminee dans $target"


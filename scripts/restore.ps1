param(
    [Parameter(Mandatory=$true)]
    [string]$BackupPath,
    [string]$EnvFile = ".env"
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
$source = Join-Path $BackupPath $dbName

if (!(Test-Path $source)) {
    throw "Dossier de sauvegarde introuvable: $source"
}

mongorestore --uri "$env:ATLAS_URI" --db $dbName --drop $source
Write-Host "Restauration terminee depuis $source"


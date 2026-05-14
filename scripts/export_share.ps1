<#
.SYNOPSIS
    Produces a clean, shareable copy of flow-api/ as a sibling folder.

.DESCRIPTION
    Filters out venvs, caches, the persistent Google session (user_data/profile),
    DOM inspection dumps, local generation outputs, and anything that looks like
    a secrets file. Runs a post-copy regex scan for stray secret patterns and
    aborts before you ship if it finds anything suspicious.

    The destination is a plain folder, ready to zip and hand to someone else.
    The recipient's onboarding lives in the existing README.md.

.PARAMETER Destination
    Where to write the cleaned copy. Default: ..\flow-api-share (sibling of flow-api).

.PARAMETER Force
    Overwrite the destination without prompting if it already exists.

.PARAMETER NoScan
    Skip the post-copy secret regex scan. Not recommended.

.EXAMPLE
    pwsh scripts/export_share.ps1
    pwsh scripts/export_share.ps1 -Destination ..\flow-api-v0.1.0 -Force
#>

[CmdletBinding()]
param(
    [string]$Destination,
    [switch]$Force,
    [switch]$NoScan
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$source    = Resolve-Path (Join-Path $scriptDir '..')
if (-not $Destination) {
    $Destination = Join-Path (Split-Path -Parent $source) 'flow-api-share'
}

if (Test-Path -LiteralPath $Destination) {
    if (-not $Force) {
        $reply = Read-Host "Destination '$Destination' exists. Delete and replace? [y/N]"
        if ($reply -notmatch '^[yY]') { Write-Host 'Aborted.'; exit 1 }
    }
    Remove-Item -LiteralPath $Destination -Recurse -Force
}
New-Item -ItemType Directory -Path $Destination | Out-Null

$excludeDirs = @(
    '.venv', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache',
    'dist', 'build', 'htmlcov', '.vscode', '.idea', '.git',
    'inspections', 'user_data', 'profile'
)
$excludeFiles = @(
    '*.pyc', '*.pyo', '.DS_Store', 'Thumbs.db', '.coverage', '.python-version-local',
    'out*.mp4', 'out*.png', 'out*.jpg',
    '.env', '.env.*', '*.env',
    'secrets.*', 'credentials.*', 'cookies.json', 'storage_state.json', 'auth.json',
    '*.pem', '*.key'
)

Write-Host "Copying $source -> $Destination ..."
$robocopyArgs = @(
    "$source", "$Destination",
    '/MIR', '/NFL', '/NDL', '/NJH', '/NJS', '/NP', '/R:1', '/W:1',
    '/XD'
) + $excludeDirs + @('/XF') + $excludeFiles

& robocopy @robocopyArgs | Out-Null
# robocopy exit codes 0-7 are success; 8+ are errors.
if ($LASTEXITCODE -ge 8) { throw "robocopy failed (exit $LASTEXITCODE)" }

# Glob exclusions for *.egg-info and *.profile (robocopy /XD doesn't take wildcards).
Get-ChildItem -LiteralPath $Destination -Recurse -Directory -Force `
    | Where-Object { $_.Name -like '*.egg-info' -or $_.Name -like '*.profile' } `
    | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }

if (-not $NoScan) {
    Write-Host 'Scanning for stray secrets ...'
    $patterns = @(
        'password\s*[:=]\s*["''][^"'']+["'']',
        '(?i)bearer\s+[A-Za-z0-9_\-\.=]{16,}',
        'AKIA[0-9A-Z]{16}',
        'ghp_[A-Za-z0-9]{20,}',
        'sk-[A-Za-z0-9]{20,}',
        '-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
        'munder\.elgummi@gmail\.com'
    )
    $textExts = @('.py', '.toml', '.md', '.txt', '.json', '.yaml', '.yml', '.cfg', '.ini', '.ps1', '.sh', '.env', '.html')
    $hits = @()
    Get-ChildItem -LiteralPath $Destination -Recurse -File -Force `
        | Where-Object { $textExts -contains $_.Extension.ToLower() } `
        | ForEach-Object {
            $file = $_
            $matches = Select-String -LiteralPath $file.FullName -Pattern $patterns -AllMatches -ErrorAction SilentlyContinue
            if ($matches) { $hits += $matches }
        }
    if ($hits.Count -gt 0) {
        Write-Host "`nFound $($hits.Count) suspicious match(es):" -ForegroundColor Red
        foreach ($h in $hits) {
            $rel = $h.Path.Substring($Destination.Length).TrimStart('\','/')
            Write-Host ("  {0}:{1}  -- {2}" -f $rel, $h.LineNumber, $h.Line.Trim()) -ForegroundColor Red
        }
        Write-Host "`nReview and remove the offending content, then re-run." -ForegroundColor Red
        exit 2
    }
    Write-Host '  0 suspicious matches.'
}

$fileCount = (Get-ChildItem -LiteralPath $Destination -Recurse -File -Force).Count
$totalBytes = (Get-ChildItem -LiteralPath $Destination -Recurse -File -Force | Measure-Object -Sum Length).Sum
$mb = [math]::Round($totalBytes / 1MB, 2)

Write-Host ''
Write-Host "Exported $fileCount files ($mb MB) to:" -ForegroundColor Green
Write-Host "  $Destination" -ForegroundColor Green
Write-Host ''
Write-Host 'Next step for the recipient:'
Write-Host '  cd flow-api-share'
Write-Host '  uv sync                                # or: pip install -e ".[dev]"'
Write-Host '  python -m playwright install chromium'
Write-Host '  python examples/first_run_signin.py    # one-time Google sign-in'

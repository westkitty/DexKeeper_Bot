$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$venv = Join-Path $root ".venv-win-build"
$python = Join-Path $venv "Scripts\python.exe"
$pyinstaller = Join-Path $venv "Scripts\pyinstaller.exe"

if (!(Test-Path $python)) {
  python -m venv $venv
}

& $python -m pip install --upgrade pip
& $python -m pip install -r (Join-Path $root "requirements.txt")
& $python -m pip install pyinstaller

& $python (Join-Path $PSScriptRoot "make_icon.py")

$spec = Join-Path $PSScriptRoot "pyinstaller.spec"
$dist = Join-Path $root "dist\windows"
$build = Join-Path $root "build\windows"

& $pyinstaller $spec --noconfirm --clean --distpath $dist --workpath $build

$exeCandidates = Get-ChildItem -Path $dist -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -ieq "DexKeeper.exe" -or $_.Name -ieq "DexKeeper" -or $_.Name -like "DexKeeper*.exe" }

if ($exeCandidates.Count -eq 0) {
  Write-Host "No DexKeeper binary found under $dist"
  Get-ChildItem -Path $dist -Recurse | Select-Object FullName | Write-Host
  exit 1
}

$exePath = $exeCandidates[0].FullName
$targetExe = Join-Path $dist "DexKeeper.exe"
if ($exePath -ne $targetExe) {
  Copy-Item $exePath $targetExe -Force
}

Write-Host "Build output: $dist\DexKeeper.exe"

if (Get-Command iscc.exe -ErrorAction SilentlyContinue) {
  $issPath = Join-Path $PSScriptRoot "DexKeeper.iss"
  $tempIss = Join-Path $env:TEMP "DexKeeper.generated.iss"
  $iconPath = Join-Path $root "assets\DexKeeper_Bot_icon.ico"
  $defineLine = "#define MyAppExeSource `"$exePath`"`r`n"
  $defineIcon = "#define MyAppIcon `"$iconPath`"`r`n"
  $includeLine = "#include `"$issPath`"`r`n"
  Set-Content -Path $tempIss -Value ($defineLine + $defineIcon + $includeLine) -Encoding ASCII
  & iscc.exe $tempIss
  Write-Host "Installer output: $dist\DexKeeper-Setup.exe"
} else {
  Write-Host "Inno Setup (iscc.exe) not found; skipping installer packaging."
}

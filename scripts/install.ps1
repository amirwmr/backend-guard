$ErrorActionPreference = "Stop"

$PackageSpec = if ($env:BACKEND_GUARD_PACKAGE_SPEC) { $env:BACKEND_GUARD_PACKAGE_SPEC } else { "backend-guard" }
$StateDir = Join-Path $HOME ".backend-guard"
$ManifestPath = Join-Path $StateDir "install-manifest.json"

$PythonBin = Get-Command py -ErrorAction SilentlyContinue
if (-not $PythonBin) {
    $PythonBin = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $PythonBin) {
    throw "backend-guard installer requires py or python on PATH."
}

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

$Method = $null
$UninstallCommand = $null

if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv tool install --upgrade $PackageSpec
    $Method = "uv-tool"
    $UninstallCommand = @("uv", "tool", "uninstall", "backend-guard")
}
elseif (Get-Command pipx -ErrorAction SilentlyContinue) {
    pipx install --force $PackageSpec
    $Method = "pipx"
    $UninstallCommand = @("pipx", "uninstall", "backend-guard")
}
else {
    if ($PythonBin.Name -eq "py") {
        py -m pip install --user --upgrade $PackageSpec
        $UninstallCommand = @("py", "-m", "pip", "uninstall", "-y", "backend-guard")
    }
    else {
        python -m pip install --user --upgrade $PackageSpec
        $UninstallCommand = @("python", "-m", "pip", "uninstall", "-y", "backend-guard")
    }
    $Method = "pip-user"
}

$Manifest = @{
    method = $Method
    uninstall_command = $UninstallCommand
    executable_path = $null
} | ConvertTo-Json -Depth 4

Set-Content -Path $ManifestPath -Value $Manifest -Encoding UTF8
Write-Host "backend-guard installed."
Write-Host "Run 'backend-guard --help' in a new shell if the command is not yet available."

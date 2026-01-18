param(
    [int]$Lines = 200,
    [switch]$Follow
)

# tail_uvicorn.ps1 - print last N lines of uvicorn.log (optionally follow)
Set-Location $PSScriptRoot

if (-Not (Test-Path uvicorn.log)) {
    Write-Error "uvicorn.log not found in $PSScriptRoot"
    exit 1
}

if ($Follow) {
    Get-Content uvicorn.log -Tail $Lines -Wait
} else {
    Get-Content uvicorn.log -Tail $Lines
}


$ErrorActionPreference = "Stop"
try {
    $ryzenadj = "ryzenadj\ryzenadj.exe"
    Write-Output "Using RyzenADJ at: $ryzenadj"
    
    # Test if RyzenADJ exists
    if (-not (Test-Path $ryzenadj)) {
        throw "RyzenADJ executable not found at: $ryzenadj"
    }
    
    # Build arguments array
    $ryzenadj_args = @(
        "--stapm-limit"
        "95"
        "--fast-limit"
        "95000"
        "--slow-limit"
        "95000"
        "--tctl-temp"
        "95"
        "--apu-skin-temp"
        "50"
        "--vrmmax-current"
        "180000"
    )
    Write-Output "Arguments: $($ryzenadj_args -join ' ')"
    
    # Check if running as admin
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    Write-Output "Running as admin: $isAdmin"
    
    if (-not $isAdmin) {
        Write-Output "Elevating privileges..."
        $argString = $ryzenadj_args -join ' '
        $pinfo = New-Object System.Diagnostics.ProcessStartInfo
        $pinfo.FileName = "powershell.exe"
        $pinfo.Arguments = "-NoProfile -ExecutionPolicy Bypass -Command & `"$ryzenadj`" $argString"
        $pinfo.Verb = "runas"
        $pinfo.RedirectStandardError = $true
        $pinfo.RedirectStandardOutput = $true
        $pinfo.UseShellExecute = $false
        
        $p = New-Object System.Diagnostics.Process
        $p.StartInfo = $pinfo
        $p.Start() | Out-Null
        $p.WaitForExit()
        
        $stdout = $p.StandardOutput.ReadToEnd()
        $stderr = $p.StandardError.ReadToEnd()
        
        Write-Output "Output: $stdout"
        if ($stderr) { Write-Error "Error: $stderr" }
        
        if ($p.ExitCode -ne 0) {
            throw "RyzenADJ failed with exit code: $($p.ExitCode)"
        }
    } else {
        Write-Output "Running RyzenADJ directly..."
        $output = & $ryzenadj $ryzenadj_args 2>&1
        Write-Output "Output: $output"
        if ($LASTEXITCODE -ne 0) {
            throw "RyzenADJ failed with exit code: $LASTEXITCODE`nOutput: $output"
        }
    }
    
    Write-Output "Profile applied successfully"
    exit 0
} catch {
    Write-Error $_.Exception.Message
    Write-Error $_.Exception.StackTrace
    exit 1
}

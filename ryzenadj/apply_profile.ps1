
$ErrorActionPreference = "Stop"
try {
    $ryzenadj = "ryzenadj\ryzenadj.exe"
    Write-Output "Utilisation de RyzenADJ: $ryzenadj"
    
    if (-not (Test-Path $ryzenadj)) {
        throw "ryzenadj.exe non trouvé: $ryzenadj"
    }
    
    $ryzenadj_args = @(
        "--stapm-limit"
        "120"
        "--fast-limit"
        "140000"
        "--slow-limit"
        "120000"
        "--tctl-temp"
        "100"
        "--apu-skin-temp"
        "50"
        "--vrmmax-current"
        "200000"
    )
    Write-Output "Arguments: $($ryzenadj_args -join ' ')"
    
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    Write-Output "Exécution en tant qu'admin: $isAdmin"
    
    if (-not $isAdmin) {
        Write-Output "Élévation des privilèges..."
        $argString = $ryzenadj_args -join ' '
        
        $pinfo = New-Object System.Diagnostics.ProcessStartInfo
        $pinfo.FileName = "powershell.exe"
        $pinfo.Arguments = "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -Command & `"$ryzenadj`" $argString"
        $pinfo.Verb = "runas"
        $pinfo.RedirectStandardError = $true
        $pinfo.RedirectStandardOutput = $true
        $pinfo.UseShellExecute = $false
        $pinfo.CreateNoWindow = $true
        
        $p = New-Object System.Diagnostics.Process
        $p.StartInfo = $pinfo
        $p.Start() | Out-Null
        $p.WaitForExit()
        
        $stdout = $p.StandardOutput.ReadToEnd()
        $stderr = $p.StandardError.ReadToEnd()
        
        Write-Output "Sortie: $stdout"
        if ($stderr) { Write-Error "Erreur: $stderr" }
        
        if ($p.ExitCode -ne 0) {
            throw "ryzenadj a échoué avec le code: $($p.ExitCode)"
        }
    } else {
        Write-Output "Exécution directe de ryzenadj..."
        $output = & $ryzenadj $ryzenadj_args 2>&1
        Write-Output "Sortie: $output"
        if ($LASTEXITCODE -ne 0) {
            throw "ryzenadj a échoué avec le code: $LASTEXITCODE`nSortie: $output"
        }
    }
    
    Write-Output "Profil appliqué avec succès"
    exit 0
} catch {
    Write-Error $_.Exception.Message
    Write-Error $_.Exception.StackTrace
    exit 1
}

; Framework Laptop Hub Installer Script
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"

; General
Name "Framework Laptop Hub"
OutFile "Framework_Laptop_Hub_Setup.exe"
InstallDir "$PROGRAMFILES64\Framework Laptop Hub"
RequestExecutionLevel admin

; Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "assets\logo.ico"
!define MUI_UNICON "assets\logo.ico"

; Modern UI
!define MUI_WELCOMEPAGE_TITLE "Framework Laptop Hub Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of Framework Laptop Hub.$\n$\nClick Next to continue."
!define MUI_FINISHPAGE_TITLE "Installation Complete"
!define MUI_FINISHPAGE_TEXT "Framework Laptop Hub has been installed on your computer.$\n$\nClick Finish to close Setup."
!define MUI_FINISHPAGE_RUN "$INSTDIR\Framework_Laptop_Hub.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch Framework Laptop Hub"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_LANGUAGE "German"
!insertmacro MUI_LANGUAGE "Spanish"

; Version Information
VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "Framework Laptop Hub"
VIAddVersionKey "CompanyName" "Framework"
VIAddVersionKey "LegalCopyright" "© 2024 Framework"
VIAddVersionKey "FileDescription" "Framework Laptop Hub Installer"
VIAddVersionKey "FileVersion" "1.0.0"
VIAddVersionKey "ProductVersion" "1.0.0"

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    
    ; Set output path to the installation directory
    SetOutPath "$INSTDIR"
    
    ; Add files
    File /r "dist\Framework_Laptop_Hub\*.*"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Create start menu shortcuts
    CreateDirectory "$SMPROGRAMS\Framework Laptop Hub"
    CreateShortCut "$SMPROGRAMS\Framework Laptop Hub\Framework Laptop Hub.lnk" "$INSTDIR\Framework_Laptop_Hub.exe" "" "$INSTDIR\assets\logo.ico"
    CreateShortCut "$SMPROGRAMS\Framework Laptop Hub\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    
    ; Create desktop shortcut
    CreateShortCut "$DESKTOP\Framework Laptop Hub.lnk" "$INSTDIR\Framework_Laptop_Hub.exe" "" "$INSTDIR\assets\logo.ico"
    
    ; Registry information for add/remove programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Laptop Hub" "DisplayName" "Framework Laptop Hub"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Laptop Hub" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Laptop Hub" "DisplayIcon" "$INSTDIR\assets\logo.ico"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Laptop Hub" "Publisher" "Framework"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Laptop Hub" "Version" "1.0.0"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Laptop Hub" "DisplayVersion" "1.0.0"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Laptop Hub" "URLInfoAbout" "https://frame.work"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Laptop Hub" "HelpLink" "https://frame.work/support"
    
    ; Get installation folder size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Laptop Hub" "EstimatedSize" "$0"
SectionEnd

Section "Uninstall"
    ; Remove files and directories
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$DESKTOP\Framework Laptop Hub.lnk"
    RMDir /r "$SMPROGRAMS\Framework Laptop Hub"
    
    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Laptop Hub"
    
    ; Remove any remaining files
    Delete "$INSTDIR\*.*"
    RMDir /r "$INSTDIR"
SectionEnd

; Function to check if Framework_Laptop_Hub.exe exists in dist directory
Function .onInit
    IfFileExists "dist\Framework_Laptop_Hub\Framework_Laptop_Hub.exe" continue
        MessageBox MB_ICONSTOP|MB_OK "Error: Framework_Laptop_Hub.exe not found in dist directory.$\nPlease run build.py first to create the executable.$\n$\nThe installer will now exit."
        Abort
    continue:
    
    ; Check for running instance
    FindWindow $0 "" "Framework Laptop Hub"
    StrCmp $0 0 notRunning
        MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION "Framework Laptop Hub is currently running. Please close it first to continue the installation." IDOK checkAgain IDCANCEL quit
    checkAgain:
        Goto notRunning
    quit:
        Abort
    notRunning:
FunctionEnd

; Function to check if app is running before uninstall
Function un.onInit
    FindWindow $0 "" "Framework Laptop Hub"
    StrCmp $0 0 notRunning
        MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION "Framework Laptop Hub is currently running. Please close it first to continue the uninstallation." IDOK checkAgain IDCANCEL quit
    checkAgain:
        Goto notRunning
    quit:
        Abort
    notRunning:
FunctionEnd 
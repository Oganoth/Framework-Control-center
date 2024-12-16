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

; Try to use icon if it exists, otherwise continue without it
!define MUI_ICON "assets\logo.ico"
!define MUI_UNICON "assets\logo.ico"

; Pages
!define MUI_WELCOMEPAGE_TITLE "Framework Laptop Hub Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of Framework Laptop Hub.$\n$\nClick Next to continue."

; Pre-install checks
Function .onInit
    ; Check if build directory exists
    IfFileExists "dist\Framework_Laptop_Hub\*.*" continue
        MessageBox MB_ICONSTOP|MB_OK "Error: Build directory not found. Please run build.py first.$\n$\nThe installer will now exit."
        Abort
    continue:
    
    ; Check if Framework_Laptop_Hub.exe exists
    IfFileExists "dist\Framework_Laptop_Hub\Framework_Laptop_Hub.exe" +2
        Abort "Error: Framework_Laptop_Hub.exe not found in build directory"
FunctionEnd

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Language
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "French"

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    
    ; Copy all files from dist directory
    File /r "dist\Framework_Laptop_Hub\*.*"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Create start menu shortcut
    CreateDirectory "$SMPROGRAMS\Framework Laptop Hub"
    CreateShortCut "$SMPROGRAMS\Framework Laptop Hub\Framework Laptop Hub.lnk" "$INSTDIR\Framework_Laptop_Hub.exe"
    CreateShortCut "$SMPROGRAMS\Framework Laptop Hub\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    
    ; Create desktop shortcut
    CreateShortCut "$DESKTOP\Framework Laptop Hub.lnk" "$INSTDIR\Framework_Laptop_Hub.exe"
    
    ; Registry information for add/remove programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Laptop Hub" "DisplayName" "Framework Laptop Hub"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Laptop Hub" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Laptop Hub" "DisplayIcon" "$INSTDIR\Framework_Laptop_Hub.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Laptop Hub" "Publisher" "Framework"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Laptop Hub" "Version" "1.0.0"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Laptop Hub" "DisplayVersion" "1.0.0"
    
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
SectionEnd 
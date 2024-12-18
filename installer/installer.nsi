; Framework Hub Installer Script
!include "MUI2.nsh"
!include "FileFunc.nsh"

; General
Name "Framework Hub"
OutFile "..\dist\Framework_Hub_Setup.exe"
Unicode True
RequestExecutionLevel admin
InstallDir "$PROGRAMFILES\Framework Hub"

; Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "..\assets\logo.ico"
!define MUI_UNICON "..\assets\logo.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
Page custom StartupOptionsPage StartupOptionsLeave
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Language
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "French"

; Custom page for startup options
Var Dialog
Var StartupCheckbox

Function StartupOptionsPage
    !insertmacro MUI_HEADER_TEXT "Startup Options" "Choose whether to run Framework Hub at Windows startup"
    nsDialogs::Create 1018
    Pop $Dialog
    
    ${If} $Dialog == error
        Abort
    ${EndIf}
    
    ${NSD_CreateCheckbox} 10 10 100% 12u "Run Framework Hub at Windows startup"
    Pop $StartupCheckbox
    
    nsDialogs::Show
FunctionEnd

Function StartupOptionsLeave
    ${NSD_GetState} $StartupCheckbox $0
FunctionEnd

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    
    ; Copy all files from the dist directory
    File /r "..\dist\Framework_Hub\*.*"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Create start menu shortcut
    CreateDirectory "$SMPROGRAMS\Framework Hub"
    CreateShortcut "$SMPROGRAMS\Framework Hub\Framework Hub.lnk" "$INSTDIR\mini.exe"
    CreateShortcut "$SMPROGRAMS\Framework Hub\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    
    ; Add startup option if selected
    ${NSD_GetState} $StartupCheckbox $0
    ${If} $0 == 1
        CreateShortcut "$SMSTARTUP\Framework Hub.lnk" "$INSTDIR\mini.exe"
    ${EndIf}
    
    ; Add uninstall information to Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Hub" \
                     "DisplayName" "Framework Hub"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Hub" \
                     "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Hub" \
                     "DisplayIcon" "$INSTDIR\mini.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Hub" \
                     "Publisher" "Framework"
SectionEnd

Section "Uninstall"
    ; Remove start menu shortcuts
    Delete "$SMPROGRAMS\Framework Hub\Framework Hub.lnk"
    Delete "$SMPROGRAMS\Framework Hub\Uninstall.lnk"
    RMDir "$SMPROGRAMS\Framework Hub"
    
    ; Remove startup shortcut if exists
    Delete "$SMSTARTUP\Framework Hub.lnk"
    
    ; Remove installation directory
    RMDir /r "$INSTDIR"
    
    ; Remove registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Framework Hub"
SectionEnd 
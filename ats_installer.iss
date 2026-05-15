; Inno Setup Script for ATS Pro AI
; Download Inno Setup from: https://jrsoftware.org/isdl.php

[Setup]
AppId={{C6B5F7D1-8A9E-4D2F-A1B2-C3D4E5F6A7B8}
AppName=ATS & Scraper
AppVersion=1.0
AppPublisher=Harsh Bajaj
DefaultDirName={autopf}\ATS Pro AI
DefaultGroupName=ATS Pro AI
AllowNoIcons=yes
; Output location for the Setup.exe
OutputDir=.
OutputBaseFilename=ATS_Scraper_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Add your icon here if you have one
; SetupIconFile=icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; IMPORTANT: This points to the folder created by PyInstaller in 'onedir' mode
Source: "dist\ATS_Pro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on shared system files

[Icons]
Name: "{group}\ATS Pro AI"; Filename: "{app}\ATS_Pro.exe"
Name: "{autodesktop}\ATS Pro AI"; Filename: "{app}\ATS_Pro.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\ATS_Pro.exe"; Description: "{cm:LaunchProgram,ATS Pro AI}"; Flags: nowait postinstall skipifsilent

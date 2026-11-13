; Linda Sejf — instalator Windows (Inno Setup 6). Budowanie: python installer/build.py
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#ifndef Payload
  #define Payload "..\build\payload"
#endif

[Setup]
AppId={{6B0E7C1E-5A51-4C77-9D7B-3F2A3B1E9C41}
AppName=Linda Sejf
AppVersion={#AppVersion}
AppPublisher=Linda
AppPublisherURL=https://lindasejf.denmarkeast.cloudapp.azure.com/projekt/
DefaultDirName={autopf}\Linda Sejf
DefaultGroupName=Linda Sejf
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
WizardStyle=modern
SetupIconFile=..\ui\linda.ico
UninstallDisplayIcon={app}\ui\linda.ico
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=LindaSejf-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"

[Files]
Source: "{#Payload}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Linda Sejf"; Filename: "{app}\runtime\python.exe"; Parameters: """{app}\launcher.py"""; WorkingDir: "{app}"; IconFilename: "{app}\ui\linda.ico"
Name: "{group}\Folder dokumentów Linda Sejf"; Filename: "{app}\corpus"
Name: "{group}\Odinstaluj Linda Sejf"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Linda Sejf"; Filename: "{app}\runtime\python.exe"; Parameters: """{app}\launcher.py"""; WorkingDir: "{app}"; IconFilename: "{app}\ui\linda.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Skrót na pulpicie"; GroupDescription: "Skróty:"

[Run]
Filename: "{app}\runtime\python.exe"; Parameters: """{app}\launcher.py"""; WorkingDir: "{app}"; Description: "Uruchom Linda Sejf teraz (pierwszy start pobiera modele, ok. 8,2 GB)"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\models"
Type: filesandordirs; Name: "{app}\__pycache__"
Type: filesandordirs; Name: "{app}\sejf\__pycache__"

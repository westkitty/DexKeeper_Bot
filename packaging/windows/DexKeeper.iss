#define MyAppName "DexKeeper"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "DexKeeper"
#define MyAppExeName "DexKeeper.exe"
#ifndef MyAppExeSource
  #define MyAppExeSource "..\\..\\dist\\windows\\DexKeeper.exe"
#endif
#ifndef MyAppIcon
  #define MyAppIcon "..\\..\\assets\\DexKeeper_Bot_icon.ico"
#endif

[Setup]
AppId={{4D4F6A52-9B56-49F2-AD4F-9C4A5F8120E7}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\DexKeeper
DefaultGroupName=DexKeeper
SetupIconFile={#MyAppIcon}
OutputDir=..\..\dist\windows
OutputBaseFilename=DexKeeper-Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}

[Tasks]
Name: "autostart"; Description: "Start DexKeeper on login"; Flags: unchecked

[Files]
Source: "{#MyAppExeSource}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\DexKeeper"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall DexKeeper"; Filename: "{uninstallexe}"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "DexKeeper"; ValueData: """{app}\{#MyAppExeName}"""; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch DexKeeper now"; Flags: nowait postinstall skipifsilent

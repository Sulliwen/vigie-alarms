; Per-user installer: no administrator rights needed.
#define AppName "Vigie"
; The version comes from vigie.py: build.ps1 passes it with /DAppVersion.
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define AppExe "Vigie.exe"

[Setup]
AppId={{6F0B8C2E-4D1A-4B7E-9C35-CA1E0DA7A1A2}
AppName={#AppName}
AppVersion={#AppVersion}
VersionInfoVersion={#AppVersion}
AppPublisher=Sullivan Bitho
DefaultDirName={localappdata}\Programs\Vigie
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=Vigie-Setup-{#AppVersion}
SetupIconFile=build\Vigie.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; The wizard follows the language of Windows, like the program does.
ShowLanguageDialog=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Files]
Source: "dist\Vigie\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"

[Registry]
; The program registers itself at logon; the installer only cleans that entry up.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "Vigie"; Flags: dontcreatekey uninsdeletevalue
; Entry left by the builds made under the former name, Calendar Alarm.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "CalendarAlarm"; Flags: dontcreatekey deletevalue

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Saved passwords and iCal addresses (Windows Credential Manager).
Filename: "{app}\{#AppExe}"; Parameters: "--forget"; Flags: runhidden; RunOnceId: "ForgetSecrets"

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\vigie"

[Code]
procedure StopApp();
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM {#AppExe}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  StopApp();
  Result := '';
end;

function InitializeUninstall(): Boolean;
begin
  StopApp();
  Result := True;
end;

#define MyAppName "Widget Wall"
#define MyAppVersion "0.3.0"
#define MyAppExeName "Widget_Wall.exe"

[Setup]
AppId={{C619DC93-8B8C-5E2B-8D43-0CB88AA66E18}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=ColorsOfFractals
DefaultDirName={localappdata}\Programs\Widget_Wall
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\release\installer
OutputBaseFilename=Widget_Wall_Setup
SetupIconFile=..\assets\Widget_Wall.ico
WizardImageFile=WizardImage.bmp
WizardSmallImageFile=WizardSmallImage.bmp
UninstallDisplayIcon={app}\Widget_Wall.exe
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
ArchitecturesAllowed=x64compatible
VersionInfoVersion=0.3.0.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\release\Widget_Wall\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Widget Wall"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Widget Wall"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Widget Wall"; Flags: nowait postinstall skipifsilent
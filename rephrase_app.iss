#define MyAppName "AI Text Rephraser"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Itamar Shashar"
#define MyAppExeName "AI Text Rephraser.exe"
#define MyAppId "{{E8A1C597-75A9-45CB-B9E0-14D2C3AF614A}}"
#define MyAppIcon "src\\r_icon.ico"
#define MyInstallerName "AI-Text-Rephraser-Installer"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename={#MyInstallerName}
SetupIconFile={#MyAppIcon}
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

; Use 'lowest' if you want no UAC prompt, but note that writing to {app} can be virtualized.
; If you do want to install to Program Files reliably, you typically set PrivilegesRequired=admin
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

UninstallDisplayIcon={app}\\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
WizardStyle=modern

AlwaysShowDirOnReadyPage=yes
DisableDirPage=no
DisableProgramGroupPage=yes
DisableWelcomePage=no
DisableReadyPage=no
CloseApplications=yes
CreateUninstallRegKey=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "startupicon"; Description: "Run AI Text Rephraser when Windows starts"; \
  GroupDescription: "Startup options:"; Flags: checkedonce
Name: "launchapp"; Description: "Launch AI Text Rephraser after installation"; \
  Flags: checkedonce

[Files]
; Install the main application EXE + other files into {app}
Source: "build\\exe.win-amd64-3.11\\*"; DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs
Source: "src\\r_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "src\\system_prompt.txt"; DestDir: "{app}"; Flags: ignoreversion

; Put config.json in the app directory (where the app looks for it first)
Source: "src\\config.json"; DestDir: "{app}"; Flags: ignoreversion

; Not strictly needed, but if you want an icon in the temp folder for something:
Source: "src\\r_icon.ico"; DestDir: "{tmp}"; Flags: dontcopy

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{group}\\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Registry]
Root: HKCU; Subkey: "Software\\Microsoft\\Windows\\CurrentVersion\\Run"; ValueType: string; \
  ValueName: "{#MyAppName}"; ValueData: """{app}\\{#MyAppExeName}"""; \
  Flags: uninsdeletevalue; Tasks: startupicon

[Run]
; Let user optionally launch the app after installation
Filename: "{app}\\{#MyAppExeName}"; Description: "Launch AI Text Rephraser"; \
  Flags: nowait postinstall skipifsilent; Tasks: launchapp

[UninstallDelete]
; Remove the main folder
Type: filesandordirs; Name: "{app}"

[Code]
var
  ApiKeyPage: TInputQueryWizardPage;
  ApiKeyLink: TNewStaticText;

// Terminate the running app (if any) before installing/uninstalling
procedure TerminateApp();
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{sys}\\taskkill.exe'), '/F /IM "{#MyAppExeName}"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

// Read file contents into a string
function ReadFileAsString(const FileName: String): String;
var
  FileData: AnsiString;
begin
  if LoadStringFromFile(FileName, FileData) then
    Result := FileData
  else
    Result := '';
end;

// Write string to file
function WriteStringToFile(const FileName, Contents: String): Boolean;
begin
  Result := SaveStringToFile(FileName, Contents, False);
end;

// Click handler: open the AI Studio website
procedure ApiKeyLinkClick(Sender: TObject);
var
  ErrorCode: Integer;
begin
  ShellExec('', 'https://ai.google.dev/aistudio', '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode);
end;

// Insert the user's API key into config.json
procedure UpdateConfigWithApiKey();
var
  ConfigPath: String;
  ApiKey: String;
  FileContents: String;
begin
  ApiKey := ApiKeyPage.Values[0];
  if ApiKey <> '' then
  begin
    // Update the config.json in the app directory (which is where the app looks first)
    ConfigPath := ExpandConstant('{app}\\config.json');
    if FileExists(ConfigPath) then
    begin
      // Read file contents
      FileContents := ReadFileAsString(ConfigPath);
      
      // Replace the API key placeholder with the actual key
      StringChangeEx(FileContents, '"api_key": ""', Format('"api_key": "%s"', [ApiKey]), True);
      
      // Write back to file
      if not WriteStringToFile(ConfigPath, FileContents) then
        MsgBox('Warning: Could not update the API key in config.json.', mbInformation, MB_OK);
    end else
      MsgBox('Warning: Could not find config.json in the app directory.', mbInformation, MB_OK);
  end;
end;

// Run logic before/after install
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssInstall then
  begin
    // Kill the running app before installation
    TerminateApp();
  end
  else if CurStep = ssPostInstall then
  begin
    // After files are installed, update config with user-provided API key
    UpdateConfigWithApiKey();

    // If user checked "Launch app," do so now
    if WizardIsTaskSelected('launchapp') then
    begin
      // The config is already updated before we call ShellExec
      ShellExec('open', ExpandConstant('{app}\\{#MyAppExeName}'), '', '', SW_SHOWNORMAL, ewNoWait, ResultCode);
    end;
  end;
end;

// Uninstall logic
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  mRes: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    // Terminate the app if running
    TerminateApp();
    // Ask user if they want to remove data
    mRes := MsgBox('Do you want to remove all settings and data files?', mbConfirmation, MB_YESNO or MB_DEFBUTTON2);
    if mRes = IDYES then
    begin
      DelTree(ExpandConstant('{userappdata}\\{#MyAppName}'), True, True, True);
    end;
  end;
end;

// Create wizard page for optional API key
procedure InitializeWizard;
begin
  ApiKeyPage := CreateInputQueryPage(
    wpSelectTasks,
    'Google Gemini API Key',
    'Enter your Google Gemini API Key (optional)',
    'You can get an API key from the Google AI Studio website. You can also set this later in the app settings.'
  );
  ApiKeyPage.Add('API Key:', False);

  ApiKeyLink := TNewStaticText.Create(WizardForm);
  ApiKeyLink.Caption := 'Get your API key for free in seconds from Google';
  ApiKeyLink.Cursor := crHand;
  ApiKeyLink.Font.Color := clBlue;
  ApiKeyLink.Font.Style := [fsUnderline];
  ApiKeyLink.OnClick := @ApiKeyLinkClick;
  ApiKeyLink.Parent := ApiKeyPage.Surface;
  ApiKeyLink.Top := 120;
  ApiKeyLink.Left := 5;
end;
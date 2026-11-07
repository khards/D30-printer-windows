Option Explicit

Dim fso, shell, folder, python, server, command
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
python = fso.BuildPath(folder, "venv\Scripts\pythonw.exe")
server = fso.BuildPath(folder, "tray.py")
command = """" & python & """ """ & server & """"
shell.Run command, 0, False

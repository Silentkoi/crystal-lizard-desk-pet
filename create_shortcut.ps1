$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$Home\Desktop\Crystal Lizard Pet.lnk")
$Shortcut.TargetPath = "$Home\crystal lizard desk pet\run_deskpet.bat"
$Shortcut.WorkingDirectory = "$Home\crystal lizard desk pet"
$Shortcut.Save() 
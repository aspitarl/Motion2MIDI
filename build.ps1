#Windows Build Script

Remove-Item -Recurse .\dist -ErrorAction SilentlyContinue

# Build Motion2MIDI Multi-Device (Superset of dependencies)
# Entry point: m2m/app.py
# Icon: m2m/gui/icon/icon_multi.png
pyinstaller -y --noconsole --name="Motion2MIDI" --icon=m2m/gui/icon/icon_multi.png --paths=. m2m/app.py

Copy-Item .\README.md .\dist\Motion2MIDI
Copy-Item .\LICENSE .\dist\Motion2MIDI

# Define the internal folder path
$internalPath = ".\dist\Motion2MIDI\_internal"

# Ensure destination directories exist for resources
New-Item -ItemType Directory -Force -Path "$internalPath\m2m\settings"
New-Item -ItemType Directory -Force -Path "$internalPath\m2m\gui\icon"

# Copy openvr manually
if (Test-Path ".\.venv\Lib\site-packages\openvr") {
    Copy-Item -Recurse -Force .\.venv\Lib\site-packages\openvr "$internalPath\openvr"
} else {
    Write-Warning "openvr package not found in .venv, skipping copy."
}

# Copy settings to m2m/settings structure
Copy-Item -Recurse -Force .\m2m\settings\* "$internalPath\m2m\settings"

# Copy icons to m2m/gui/icon structure
Copy-Item -Recurse -Force .\m2m\gui\icon\* "$internalPath\m2m\gui\icon"

# Compress
if (Test-Path "C:\Program Files\7-Zip\7z.exe") {
    & "C:\Program Files\7-Zip\7z.exe" a -t7z .\dist\Motion2MIDI_Win.7z .\dist\Motion2MIDI\*
    & "C:\Program Files\7-Zip\7z.exe" a -tzip .\dist\Motion2MIDI_Win.zip .\dist\Motion2MIDI\*
} else {
    Write-Host "7-Zip not found, skipping compression."
}

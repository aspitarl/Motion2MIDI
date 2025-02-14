#Windows Build Script

Remove-Item -Recurse .\dist

# Build main.py executable
pyinstaller -y --noconsole --name=Motion2MIDI --icon=src/icon/icon.png src/main.py

# Build multi_device.py executable
pyinstaller -y --noconsole --name="Motion2MIDI Multi-Device" --icon=src/icon/icon_multi.png src/multi_device.py

Copy-Item .\dist\"Motion2MIDI Multi-Device"\"Motion2MIDI Multi-Device.exe" .\dist\Motion2MIDI

Copy-Item .\README.md .\dist\Motion2MIDI
Copy-Item .\LICENSE .\dist\Motion2MIDI
# Copy the _internal folder to both executables
$internalPath = ".\dist\_internal"
Copy-Item -Recurse -Force .\.venv\Lib\site-packages\openvr $internalPath\openvr
Copy-Item -Recurse -Force .\src\settings $internalPath\settings
Copy-Item -Recurse -Force .\src\icon $internalPath\icon

Copy-Item -Recurse -Force $internalPath .\dist\Motion2MIDI

# Compress Motion2MIDI to Motion2MIDI_Win.7z
& "C:\Program Files\7-Zip\7z.exe" a -t7z .\dist\Motion2MIDI_Win.7z .\dist\Motion2MIDI\*

# Compress Motion2MIDI to Motion2MIDI_Win.zip
& "C:\Program Files\7-Zip\7z.exe" a -tzip .\dist\Motion2MIDI_Win.zip .\dist\Motion2MIDI\*

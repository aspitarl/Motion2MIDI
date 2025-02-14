#Linux build script

# Remove the dist directory
rm -rf ./dist

pyinstaller -y --noconsole --name=Motion2MIDI --icon=src/icon/icon.png src/main.py
pyinstaller -y --noconsole --name="Motion2MIDI Multi-Device" --icon=src/icon/icon.png src/multi_device.py

# Copy the _internal folder to both executables
internalPath="./dist/_internal"
mkdir -p $internalPath
cp -r ./.venv/lib/python3.12/site-packages/openvr $internalPath/openvr
cp -r ./src/settings $internalPath/settings
cp -r ./src/icon $internalPath/icon

cp -r $internalPath ./dist/Motion2MIDI
cp -r $internalPath "./dist/Motion2MIDI Multi-Device"

# Copy README.md and LICENSE to Motion2MIDI
cp ./README.md ./dist/Motion2MIDI
cp ./LICENSE ./dist/Motion2MIDI

# Prepare for GitHub release
releaseDir="./dist"
mkdir -p $releaseDir

# Create a tar.gz file for Motion2MIDI
tar -czvf $releaseDir/Motion2MIDI_Linux.tar.gz -C ./dist Motion2MIDI
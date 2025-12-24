#!/usr/bin/env python3
"""
Test script to verify the converted controller widgets work in the main window
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt5 import QtWidgets
from m2m.gui.main_window import MainWindow
from m2m.gui.theme import apply_dark_theme

def test_main_window():
    """Test the main window with embedded controller widgets"""
    app = QtWidgets.QApplication(sys.argv)
    apply_dark_theme(app)
    
    # Create main window
    main_window = MainWindow()
    main_window.resize(800, 600)  # Set a larger initial size to accommodate multiple controllers
    main_window.show()
    
    print("Main window created successfully")
    print("You can now:")
    print("1. Click 'Add New Controller' to add controller widgets")
    print("2. Test the menu options like 'Range Set Mode', 'MIDI Listener', etc.")
    print("3. Controllers will appear horizontally and can be removed individually")
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    test_main_window()
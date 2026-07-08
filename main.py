#!/usr/bin/env python3
"""
Duplicate Image Finder - Android App
Finds exact and visually similar duplicate images on your device.

Usage:
    python main.py          # Run on desktop for testing
    buildozer android debug # Build Android APK
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.utils import platform

# Material Design color palette
COLORS = {
    'primary': (0.098, 0.455, 0.824, 1),      # #1976D2 Blue
    'primary_dark': (0.059, 0.333, 0.627, 1),  # #0D47A1
    'accent': (1.0, 0.596, 0.0, 1),             # #FF9800 Orange
    'danger': (0.961, 0.263, 0.212, 1),         # #F44336 Red
    'success': (0.298, 0.686, 0.314, 1),        # #4CAF50 Green
    'background': (0.961, 0.961, 0.961, 1),     # #F5F5F5
    'surface': (1.0, 1.0, 1.0, 1),             # White
    'text_primary': (0.129, 0.129, 0.129, 1),
    'text_secondary': (0.459, 0.459, 0.459, 1),
}


def _setup_cjk_font():
    """Register a CJK-compatible font so Chinese text renders correctly."""
    import platform as pf
    system = pf.system()

    if system == 'Windows':
        windir = os.environ.get('WINDIR', 'C:\\Windows')
        for font_name in ('msyh.ttc', 'msyhbd.ttc', 'simhei.ttf', 'simsun.ttc'):
            fp = os.path.join(windir, 'Fonts', font_name)
            if os.path.exists(fp):
                LabelBase.register(name='CJK_Default', fn_regular=fp)
                return True

    # Android: use system CJK font
    if system == 'Linux':
        for path in (
            '/system/fonts/NotoSansCJK.ttc',
            '/system/fonts/DroidSansFallback.ttf',
            '/system/fonts/NotoSansSC-Regular.otf',
        ):
            if os.path.exists(path):
                LabelBase.register(name='CJK_Default', fn_regular=path)
                return True

    return False

_FONT_OK = _setup_cjk_font()
# Fallback font name — use CJK if registered, else Kivy default (Roboto)
FONT_NAME = 'CJK_Default' if _FONT_OK else None


class MainScreenManager(ScreenManager):
    """Manages navigation between the three main screens."""
    pass


class DuplicateImageFinderApp(App):
    """Kivy application entry point."""

    title = 'Duplicate Image Finder'
    icon = os.path.join(os.path.dirname(__file__), 'assets', 'icon.png')

    def build(self):
        """Build the app UI."""
        # Import screens (late import to avoid circular deps)
        from src.ui.scan_screen import ScanScreen, KV as SCAN_KV
        from src.ui.results_screen import ResultsScreen, KV as RESULTS_KV, GROUP_CARD_KV
        from src.ui.preview_screen import PreviewScreen, KV as PREVIEW_KV

        # Apply KV rules (must be before widget creation)
        from kivy.lang import Builder

        # Inject CJK font globally so Chinese text renders on Windows
        if FONT_NAME:
            Builder.load_string(f'''
<Label>:
    font_name: '{FONT_NAME}'
<Button>:
    font_name: '{FONT_NAME}'
<ToggleButton>:
    font_name: '{FONT_NAME}'
<TextInput>:
    font_name: '{FONT_NAME}'
''')

        Builder.load_string(SCAN_KV)
        Builder.load_string(RESULTS_KV)
        Builder.load_string(GROUP_CARD_KV)
        Builder.load_string(PREVIEW_KV)

        # Set window properties
        Window.clearcolor = COLORS['background']

        # Create screen manager
        sm = MainScreenManager()

        # Add screens
        sm.add_widget(ScanScreen(name='scan'))
        sm.add_widget(ResultsScreen(name='results'))
        sm.add_widget(PreviewScreen(name='preview'))

        # Start on scan screen
        sm.current = 'scan'

        # Request Android permissions at startup
        self._request_android_permissions()

        return sm

    def _request_android_permissions(self):
        """Request storage permissions on Android."""
        if platform != 'android':
            return

        # Try pyjnius first (bundled by python-for-android)
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ])
            return
        except (ImportError, Exception):
            pass

        # Fallback: try plyer (if installed separately)
        try:
            from plyer import storagepath
        except ImportError:
            pass

    def on_start(self):
        """Called after build(), when the app is fully initialized."""
        # Ensure user data directory exists
        if not os.path.exists(self.user_data_dir):
            try:
                os.makedirs(self.user_data_dir, exist_ok=True)
            except OSError:
                pass

    def on_pause(self):
        """Handle app going to background (Android)."""
        return True  # Allow the app to be paused

    def on_resume(self):
        """Handle app returning from background (Android)."""
        pass


if __name__ == '__main__':
    # On Android, the app is launched differently — this serves as a
    # desktop test entry point.
    DuplicateImageFinderApp().run()

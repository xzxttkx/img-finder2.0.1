"""Scan screen: folder selection, threshold slider, scan trigger, and progress display."""

import os
import threading

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.app import App

from ..scanner import ImageScanner
from ..db import ScanCache
from ..detector import DuplicateDetector, DuplicateReport
from ..exporter import ReportExporter

# Default scan paths by platform
DEFAULT_SCAN_PATHS = {
    'win': os.path.expanduser('~/Pictures'),
    'linux': os.path.expanduser('~/Pictures'),
    'android': '/storage/emulated/0/DCIM',
}

KV = '''
<ScanScreen>:
    orientation: 'vertical'
    padding: dp(16)
    spacing: dp(12)

    # Title
    Label:
        text: '\\U0001F50D 重复图片查找器'
        font_size: dp(24)
        size_hint_y: None
        height: dp(48)
        color: 0.1, 0.45, 0.82, 1

    # Path selection row
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(8)
        Label:
            text: '扫描目录:'
            size_hint_x: None
            width: dp(80)
            text_size: self.size
            halign: 'right'
            valign: 'middle'
        Label:
            id: path_label
            text: root.scan_path
            text_size: self.size
            halign: 'left'
            valign: 'middle'
            shorten: True
            shorten_from: 'right'
            color: 0.4, 0.4, 0.4, 1
        Button:
            text: '选择'
            size_hint_x: None
            width: dp(72)
            on_release: root.open_file_chooser()

    # Threshold slider
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(8)
        Label:
            text: '相似度阈值:'
            size_hint_x: None
            width: dp(80)
            text_size: self.size
            halign: 'right'
            valign: 'middle'
        Slider:
            id: threshold_slider
            min: 0
            max: 32
            value: root.threshold
            step: 1
            on_value: root.on_threshold_change(self.value)
        Label:
            id: threshold_label
            text: str(root.threshold)
            size_hint_x: None
            width: dp(36)
            text_size: self.size
            halign: 'center'
            valign: 'middle'

    # Scan button
    Button:
        id: scan_button
        text: '\\U0001F50D 开始扫描'
        size_hint_y: None
        height: dp(56)
        font_size: dp(18)
        background_normal: ''
        background_color: 0.1, 0.45, 0.82, 1
        color: 1, 1, 1, 1
        on_release: root.start_scan()
        disabled: root.scanning

    # Progress
    BoxLayout:
        size_hint_y: None
        height: dp(36)
        spacing: dp(8)
        ProgressBar:
            id: progress_bar
            value: root.progress
            max: 100
        Label:
            id: progress_label
            text: root.progress_text
            size_hint_x: None
            width: dp(120)
            text_size: self.size
            halign: 'left'
            valign: 'middle'

    # Status text
    Label:
        id: status_label
        text: root.status_text
        size_hint_y: None
        height: dp(20)
        font_size: dp(12)
        color: 0.5, 0.5, 0.5, 1

    # Spacer
    BoxLayout:
        size_hint_y: 1

    # Results quick summary (shown after scan)
    BoxLayout:
        id: summary_box
        size_hint_y: None
        height: dp(72)
        spacing: dp(12)
        opacity: 1 if root.has_results else 0
        disabled: not root.has_results

        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 1
            Label:
                text: '发现重复'
                font_size: dp(12)
                color: 0.5, 0.5, 0.5, 1
                size_hint_y: None
                height: dp(20)
            Label:
                id: dup_count_label
                text: str(root.dup_count) + ' 组'
                font_size: dp(20)
                bold: True
                color: 0.82, 0.15, 0.15, 1
                size_hint_y: None
                height: dp(32)

        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 1
            Label:
                text: '可释放空间'
                font_size: dp(12)
                color: 0.5, 0.5, 0.5, 1
                size_hint_y: None
                height: dp(20)
            Label:
                id: wasted_label
                text: root.wasted_text
                font_size: dp(20)
                bold: True
                color: 0.82, 0.15, 0.15, 1
                size_hint_y: None
                height: dp(32)

        Button:
            text: '查看结果 >'
            size_hint_x: None
            width: dp(120)
            background_normal: ''
            background_color: 0.1, 0.45, 0.82, 1
            color: 1, 1, 1, 1
            on_release: root.view_results()
'''


class ScanScreen(BoxLayout, Screen):
    """Main scan screen where users configure and run duplicate detection."""

    scan_path = StringProperty('')
    threshold = NumericProperty(10)
    progress = NumericProperty(0)
    progress_text = StringProperty('')
    status_text = StringProperty('')
    scanning = BooleanProperty(False)
    has_results = BooleanProperty(False)
    dup_count = NumericProperty(0)
    wasted_text = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._scanner = ImageScanner()
        self._detector: DuplicateDetector | None = None
        self._cache: ScanCache | None = None
        self._report: DuplicateReport | None = None
        self._scan_thread: threading.Thread | None = None

        # Determine default scan path based on platform
        self.scan_path = self._get_default_path()

        # Initialize cache when app data dir is available
        Clock.schedule_once(self._init_cache, 0.5)

    def _get_default_path(self) -> str:
        try:
            # android
            from android.storage import primary_external_storage_path
            path = primary_external_storage_path()
            if path:
                return os.path.join(path, 'DCIM')
        except ImportError:
            pass

        try:
            # windows/mac/linux
            import platform
            system = platform.system().lower()
            return DEFAULT_SCAN_PATHS.get(system, os.path.expanduser('~'))
        except Exception:
            return os.path.expanduser('~')

    def _init_cache(self, dt):
        app = App.get_running_app()
        if app and app.user_data_dir:
            self._cache = ScanCache(app.user_data_dir)

    def on_threshold_change(self, value):
        self.threshold = int(value)
        # Update label via ids
        if hasattr(self, 'ids') and 'threshold_label' in self.ids:
            self.ids.threshold_label.text = str(int(value))

    def open_file_chooser(self):
        """Open a popup with file chooser to select scan directory."""
        # Default to parent of current path
        start_path = self.scan_path or os.path.expanduser('~')

        chooser_layout = BoxLayout(orientation='vertical', spacing=8)
        filechooser = FileChooserListView(
            path=start_path,
            dirselect=True,
            filters=[''],
        )
        chooser_layout.add_widget(filechooser)

        btn_layout = BoxLayout(size_hint_y=None, height='48dp', spacing=8)

        def on_select(instance):
            selected = filechooser.selection
            if selected:
                self.scan_path = selected[0]
                self.ids.path_label.text = selected[0]
            popup.dismiss()

        btn_cancel = Button(text='取消', on_release=lambda x: popup.dismiss())
        btn_select = Button(
            text='选择此文件夹',
            background_normal='',
            background_color=(0.1, 0.45, 0.82, 1),
            color=(1, 1, 1, 1),
            on_release=on_select
        )
        btn_layout.add_widget(btn_cancel)
        btn_layout.add_widget(btn_select)
        chooser_layout.add_widget(btn_layout)

        popup = Popup(
            title='选择扫描目录',
            content=chooser_layout,
            size_hint=(0.9, 0.8),
        )
        popup.open()

    def start_scan(self):
        """Start the scan in a background thread."""
        if self.scanning:
            return

        if not self.scan_path or not os.path.isdir(self.scan_path):
            popup = Popup(
                title='错误',
                content=Label(text='请选择一个有效的目录'),
                size_hint=(0.6, 0.3),
            )
            popup.open()
            return

        self.scanning = True
        self.has_results = False
        self.progress = 0
        self.progress_text = '正在扫描文件...'
        self.status_text = ''

        self._scan_thread = threading.Thread(
            target=self._run_scan,
            daemon=True
        )
        self._scan_thread.start()

    def _run_scan(self):
        """Background scan worker."""
        try:
            # Phase 1: Scan files
            def on_scan_progress(count, current_path):
                Clock.schedule_once(lambda dt: self._update_scan_progress(count, current_path))

            images = self._scanner.scan(self.scan_path, on_scan_progress)

            if self._scanner._cancelled:
                Clock.schedule_once(lambda dt: self._on_scan_cancelled())
                return

            if not images:
                Clock.schedule_once(lambda dt: self._on_no_images())
                return

            # Phase 2: Detect duplicates
            if self._cache:
                self._detector = DuplicateDetector(cache=self._cache)

            def on_detect_progress(phase, current, total):
                Clock.schedule_once(lambda dt: self._update_detect_progress(phase, current, total))

            self._report = self._detector.detect(
                images,
                threshold=self.threshold,
                on_progress=on_detect_progress
            )

            # Phase 3: Update UI with results
            Clock.schedule_once(lambda dt: self._on_scan_complete())

        except Exception as e:
            Clock.schedule_once(lambda dt: self._on_scan_error(str(e)))

    def _update_scan_progress(self, count: int, current_path: str):
        self.progress_text = f'已找到 {count} 张图片...'
        self.status_text = current_path if current_path else ''

    def _update_detect_progress(self, phase: str, current: int, total: int):
        if total > 0:
            self.progress = min((current / total) * 100, 99)
        self.progress_text = phase

    def _on_scan_complete(self):
        self.scanning = False
        self.progress = 100

        if self._report:
            self.has_results = True
            self.dup_count = self._report.total_duplicate_groups
            self.wasted_text = self._format_size(self._report.total_wasted_bytes)
            self.status_text = (
                f'扫描完成: {self._report.total_images} 张图片, '
                f'{self._report.total_duplicate_groups} 组重复'
            )
            self.progress_text = '扫描完成!'

    def _on_no_images(self):
        self.scanning = False
        self.progress = 100
        self.status_text = '选中的目录中没有找到图片文件'
        self.progress_text = ''

    def _on_scan_cancelled(self):
        self.scanning = False
        self.progress = 0
        self.status_text = '扫描已取消'
        self.progress_text = ''

    def _on_scan_error(self, error: str):
        self.scanning = False
        self.progress = 0
        self.status_text = f'扫描出错: {error}'
        self.progress_text = ''
        popup = Popup(
            title='扫描错误',
            content=Label(text=f'扫描过程中发生错误:\n{error}'),
            size_hint=(0.7, 0.4),
        )
        popup.open()

    def view_results(self):
        """Navigate to the results screen."""
        if not self._report:
            return

        app = App.get_running_app()
        results_screen = app.root.get_screen('results')
        results_screen.set_report(self._report, self._cache)
        app.root.current = 'results'

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f'{size_bytes} B'
        elif size_bytes < 1024 * 1024:
            return f'{size_bytes / 1024:.1f} KB'
        elif size_bytes < 1024 * 1024 * 1024:
            return f'{size_bytes / (1024 * 1024):.1f} MB'
        else:
            return f'{size_bytes / (1024 * 1024 * 1024):.2f} GB'

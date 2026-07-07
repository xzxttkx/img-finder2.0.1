"""Preview screen: side-by-side image comparison with detailed info and actions."""

import os

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image as KivyImage
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.app import App

KV = '''
<PreviewScreen>:
    orientation: 'vertical'
    padding: dp(8)
    spacing: dp(6)

    # Header with navigation
    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: dp(8)
        Button:
            text: '< 返回'
            size_hint_x: None
            width: dp(72)
            background_normal: ''
            background_color: 0.5, 0.5, 0.5, 1
            color: 1, 1, 1, 1
            on_release: app.root.current = 'results'
        Label:
            id: nav_label
            text: root.nav_text
            size_hint_x: 1
            halign: 'center'
            valign: 'middle'
            text_size: self.size
            font_size: '14sp'

    # Side-by-side image comparison
    BoxLayout:
        id: compare_area
        size_hint_y: 1
        spacing: dp(4)

        # Left image panel
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.5
            spacing: dp(4)
            BoxLayout:
                id: left_image_box
                size_hint_y: 1
                canvas.before:
                    Color:
                        rgba: 0.95, 0.95, 0.95, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
            Label:
                id: left_info
                text: root.left_info_text
                size_hint_y: None
                height: dp(48)
                font_size: '10sp'
                color: 0.4, 0.4, 0.4, 1
                text_size: self.size
                halign: 'center'
                valign: 'top'

        # Right image panel
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.5
            spacing: dp(4)
            BoxLayout:
                id: right_image_box
                size_hint_y: 1
                canvas.before:
                    Color:
                        rgba: 0.95, 0.95, 0.95, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
            Label:
                id: right_info
                text: root.right_info_text
                size_hint_y: None
                height: dp(48)
                font_size: '10sp'
                color: 0.4, 0.4, 0.4, 1
                text_size: self.size
                halign: 'center'
                valign: 'top'

    # Action buttons
    BoxLayout:
        size_hint_y: None
        height: dp(44)
        spacing: dp(8)

        Button:
            text: '< 上一张'
            size_hint_x: 1
            background_normal: ''
            background_color: 0.5, 0.5, 0.5, 1
            color: 1, 1, 1, 1
            on_release: root.prev_image()
            disabled: not root.has_prev

        Button:
            text: '✓ 保留'
            size_hint_x: 1
            background_normal: ''
            background_color: 0.3, 0.7, 0.3, 1
            color: 1, 1, 1, 1
            on_release: root.keep_image()

        Button:
            text: '✗ 删除'
            size_hint_x: 1
            background_normal: ''
            background_color: 0.9, 0.3, 0.3, 1
            color: 1, 1, 1, 1
            on_release: root.delete_image()

        Button:
            text: '下一张 >'
            size_hint_x: 1
            background_normal: ''
            background_color: 0.5, 0.5, 0.5, 1
            color: 1, 1, 1, 1
            on_release: root.next_image()
            disabled: not root.has_next
'''


class PreviewScreen(BoxLayout, Screen):
    """Side-by-side image comparison and review screen."""

    nav_text = StringProperty('')
    left_info_text = StringProperty('')
    right_info_text = StringProperty('')
    has_prev = NumericProperty(0)
    has_next = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._group = None
        self._current_index = 0
        self._left_img_widget = None
        self._right_img_widget = None

    def set_group(self, group, highlight_path=None):
        """
        Load a duplicate group into the preview screen.

        Args:
            group: DuplicateGroup to preview.
            highlight_path: If given, set this as the current (left) image.
        """
        self._group = group
        if highlight_path:
            for i, img in enumerate(group.images):
                if img.path == highlight_path:
                    self._current_index = i
                    break
        else:
            self._current_index = 0

        self._refresh_display()

    def _refresh_display(self):
        """Update the side-by-side display with current and next image."""
        if not self._group or len(self._group.images) < 2:
            return

        images = self._group.images
        total = len(images)
        idx = self._current_index

        # Left: current image
        # Right: next image (or first if at end)
        left_img = images[idx]
        right_idx = (idx + 1) % total
        right_img = images[right_idx]

        # Update navigation state
        self.nav_text = f'{idx + 1} / {total} 张'
        self.has_prev = 1 if idx > 0 else 0
        self.has_next = 1 if idx < total - 1 else 0

        # Update info texts
        self.left_info_text = self._format_image_info(left_img, '当前')
        self.right_info_text = self._format_image_info(right_img, '对比')

        # Load images
        self._load_image('left', left_img.path)
        self._load_image('right', right_img.path)

    def _load_image(self, side, path):
        """Load an image into the left or right panel."""
        box_id = 'left_image_box' if side == 'left' else 'right_image_box'
        box = self.ids[box_id]
        box.clear_widgets()

        if os.path.exists(path):
            try:
                img = KivyImage(
                    source=path,
                    keep_ratio=True,
                    allow_stretch=True,
                    size_hint=(1, 1)
                )
                box.add_widget(img)
            except Exception:
                box.add_widget(Label(
                    text='无法加载图片',
                    color=(0.6, 0.6, 0.6, 1)
                ))
        else:
            box.add_widget(Label(
                text='文件不存在',
                color=(0.6, 0.6, 0.6, 1)
            ))

    def prev_image(self):
        """Navigate to the previous image in the group."""
        if self._current_index > 0:
            self._current_index -= 1
            self._refresh_display()

    def next_image(self):
        """Navigate to the next image in the group."""
        if self._current_index < len(self._group.images) - 1:
            self._current_index += 1
            self._refresh_display()

    def keep_image(self):
        """Mark current image as 'keep' — no action needed, just visual feedback."""
        if not self._group:
            return
        img = self._group.images[self._current_index]
        popup = Popup(
            title='已保留',
            content=Label(text=f'保留此图片:\n{os.path.basename(img.path)}'),
            size_hint=(0.6, 0.3),
        )
        popup.open()

    def delete_image(self):
        """Delete the current image from disk and group."""
        if not self._group or not self._group.images:
            return

        img = self._group.images[self._current_index]

        def do_delete(confirmed):
            if confirmed:
                try:
                    os.remove(img.path)
                except OSError as e:
                    popup2 = Popup(
                        title='删除失败',
                        content=Label(text=f'无法删除文件:\n{e}'),
                        size_hint=(0.7, 0.35),
                    )
                    popup2.open()
                    return

                # Remove from group
                self._group.images.pop(self._current_index)

                if len(self._group.images) < 2:
                    # Not enough images to compare, go back to results
                    popup2 = Popup(
                        title='已完成',
                        content=Label(text='此组已无重复图片'),
                        size_hint=(0.6, 0.3),
                    )
                    popup2.open()
                    App.get_running_app().root.current = 'results'
                    return

                # Adjust index
                if self._current_index >= len(self._group.images):
                    self._current_index = len(self._group.images) - 1
                self._refresh_display()
            popup.dismiss()

        content = BoxLayout(orientation='vertical', spacing='8dp', padding='8dp')
        content.add_widget(Label(
            text=f'确定删除此图片?\n{os.path.basename(img.path)}\n'
                 f'大小: {self._format_size(img.file_size)}'
        ))
        btns = BoxLayout(size_hint_y=None, height='40dp', spacing='8dp')
        btns.add_widget(Button(text='取消', on_release=lambda x: popup.dismiss()))
        btns.add_widget(Button(
            text='确认删除', on_release=lambda x: do_delete(True),
            background_normal='', background_color=(0.9, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        ))
        content.add_widget(btns)

        popup = Popup(title='确认删除', content=content, size_hint=(0.7, 0.4))
        popup.open()

    @staticmethod
    def _format_image_info(img, label) -> str:
        """Format image info for display below the preview."""
        fname = os.path.basename(img.path)
        size = PreviewScreen._format_size(img.file_size)

        # Try to get resolution
        try:
            from PIL import Image as PILImage
            with PILImage.open(img.path) as pil_img:
                res = f'{pil_img.width}x{pil_img.height}'
        except Exception:
            res = '?'

        return f'[{label}] {fname}\n{res}  {size}'

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

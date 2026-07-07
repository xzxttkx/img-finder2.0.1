"""Results screen: displays duplicate groups with filtering and actions."""

import os

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.app import App

KV = '''
<ResultsScreen>:
    orientation: 'vertical'
    padding: dp(12)
    spacing: dp(8)

    # Header
    BoxLayout:
        size_hint_y: None
        height: dp(44)
        spacing: dp(8)
        Button:
            text: '< 返回'
            size_hint_x: None
            width: dp(80)
            background_normal: ''
            background_color: 0.6, 0.6, 0.6, 1
            color: 1, 1, 1, 1
            on_release: app.root.current = 'scan'
        Label:
            text: '重复图片 (' + str(root.total_groups) + ' 组)'
            font_size: dp(18)
            size_hint_x: 1
            halign: 'left'
            valign: 'middle'
            text_size: self.size

    # Tab bar: filter by duplicate type
    BoxLayout:
        id: tab_bar
        size_hint_y: None
        height: dp(40)
        spacing: dp(4)

    # Scrollable results list
    ScrollView:
        id: scroll_view
        do_scroll_x: False
        BoxLayout:
            id: groups_container
            orientation: 'vertical'
            spacing: dp(8)
            size_hint_y: None
            height: self.minimum_height
            padding: dp(4)

    # Bottom action bar
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(8)
        Button:
            text: '导出报告'
            size_hint_x: 1
            background_normal: ''
            background_color: 0.3, 0.3, 0.3, 1
            color: 1, 1, 1, 1
            on_release: root.export_report()
        Button:
            text: '一键清理建议'
            size_hint_x: 1
            background_normal: ''
            background_color: 0.82, 0.15, 0.15, 1
            color: 1, 1, 1, 1
            on_release: root.quick_clean()
'''

GROUP_CARD_KV = '''
<GroupCard>:
    orientation: 'vertical'
    size_hint_y: None
    height: self.minimum_height
    padding: dp(10)
    spacing: dp(6)
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]
    canvas:
        Color:
            rgba: root.card_border_color
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, dp(8))
            width: 1.5
'''


class GroupCard(BoxLayout):
    """A card widget representing one duplicate group."""
    card_border_color = ObjectProperty((0.8, 0.8, 0.8, 1))

    def __init__(self, group, cache, **kwargs):
        super().__init__(**kwargs)
        self.group = group
        self.cache = cache
        self._expanded = False

        if group.duplicate_type == 'exact':
            self.card_border_color = (0.3, 0.7, 0.3, 1)  # Green for exact
        else:
            self.card_border_color = (1.0, 0.6, 0.1, 1)  # Orange for similar

        self._build_header()

    def _build_header(self):
        g = self.group
        count = len(g.images)
        wasted = self._format_size(g.total_wasted_size)
        dtype = '精确重复' if g.duplicate_type == 'exact' else '视觉相似'

        header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height='44dp',
            spacing='8dp'
        )

        icon = '📷'  # 📷
        info = Label(
            text=f'{icon} {dtype} - {count} 张  ({wasted})',
            size_hint_x=1,
            halign='left',
            valign='middle',
            text_size=(None, None),
            font_size='14sp',
            color=(0.2, 0.2, 0.2, 1)
        )
        header.add_widget(info)

        self._expand_btn = Button(
            text='▶',  # ▶
            size_hint_x=None,
            width='36dp',
            background_normal='',
            background_color=(0.95, 0.95, 0.95, 1),
            color=(0.4, 0.4, 0.4, 1),
            on_release=lambda x: self._toggle_expand()
        )
        header.add_widget(self._expand_btn)

        self.add_widget(header)

    def _toggle_expand(self):
        self._expanded = not self._expanded

        if self._expanded:
            self._expand_btn.text = '▼'  # ▼
            self._build_expanded_content()
        else:
            self._expand_btn.text = '▶'  # ▶
            self._collapse_content()

    def _build_expanded_content(self):
        """Show thumbnails and per-file info with action buttons."""
        g = self.group

        # File list
        for img in g.images:
            row = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height='36dp',
                spacing='8dp'
            )

            # Thumbnail placeholder + filename
            fname = os.path.basename(img.path)
            size_str = self._format_size(img.file_size)
            row.add_widget(Label(
                text=f'  {fname}  ({size_str})',
                size_hint_x=1,
                halign='left',
                valign='middle',
                text_size=(None, None),
                font_size='12sp',
                color=(0.3, 0.3, 0.3, 1),
                shorten=True,
                shorten_from='right'
            ))

            # Delete button per image
            del_btn = Button(
                text='✖',  # ✖
                size_hint_x=None,
                width='32dp',
                background_normal='',
                background_color=(0.95, 0.3, 0.3, 1),
                color=(1, 1, 1, 1),
                font_size='14sp'
            )
            del_btn.bind(on_release=lambda x, p=img.path: self._delete_single(p))
            row.add_widget(del_btn)

            # Preview button
            preview_btn = Button(
                text='🔍',  # 🔍
                size_hint_x=None,
                width='32dp',
                background_normal='',
                background_color=(0.3, 0.5, 0.9, 1),
                color=(1, 1, 1, 1),
                font_size='12sp'
            )
            preview_btn.bind(on_release=lambda x, p=img.path: self._preview_image(p))
            row.add_widget(preview_btn)

            self.add_widget(row)

        # Group actions
        actions = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height='36dp',
            spacing='8dp'
        )

        keep_btn = Button(
            text='保留最大',
            size_hint_x=1,
            background_normal='',
            background_color=(0.3, 0.7, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size='12sp'
        )
        keep_btn.bind(on_release=lambda x: self._keep_largest())
        actions.add_widget(keep_btn)

        del_all_btn = Button(
            text='删除其他',
            size_hint_x=1,
            background_normal='',
            background_color=(0.9, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size='12sp'
        )
        del_all_btn.bind(on_release=lambda x: self._delete_all_except_largest())
        actions.add_widget(del_all_btn)

        self.add_widget(actions)

    def _collapse_content(self):
        """Remove expanded children (keep only the header)."""
        children_to_remove = self.children[:-1]  # Keep the header (last child)
        for child in list(children_to_remove):
            self.remove_widget(child)

    def _delete_single(self, path):
        def do_delete(confirmed):
            if confirmed:
                try:
                    os.remove(path)
                    # Remove from group
                    self.group.images = [i for i in self.group.images if i.path != path]
                    # Clean cache
                    if self.cache:
                        self.cache.clean_orphaned(set())
                    # If only 1 left, this group is resolved
                    if len(self.group.images) <= 1:
                        self.parent.remove_widget(self)
                    else:
                        self._collapse_content()
                        self._toggle_expand()
                except OSError as e:
                    self._show_error(f'删除失败: {e}')
            popup.dismiss()

        content = BoxLayout(orientation='vertical', spacing='8dp', padding='8dp')
        content.add_widget(Label(text=f'确定删除?\n{path}'))
        btns = BoxLayout(size_hint_y=None, height='40dp', spacing='8dp')
        btns.add_widget(Button(text='取消', on_release=lambda x: popup.dismiss()))
        btns.add_widget(Button(text='删除', on_release=lambda x: do_delete(True),
                               background_normal='', background_color=(0.9, 0.3, 0.3, 1)))
        content.add_widget(btns)

        popup = Popup(title='确认删除', content=content, size_hint=(0.7, 0.35))
        popup.open()

    def _preview_image(self, path):
        """Open the preview screen for a specific image."""
        app = App.get_running_app()
        preview_screen = app.root.get_screen('preview')
        preview_screen.set_group(self.group, path)
        app.root.current = 'preview'

    def _keep_largest(self):
        """Keep only the largest file in the group, prompt to delete others."""
        if len(self.group.images) <= 1:
            return
        largest = max(self.group.images, key=lambda x: x.file_size)
        others = [i for i in self.group.images if i.path != largest.path]

        def do_delete(confirmed):
            if confirmed:
                deleted = 0
                errors = 0
                for img in others:
                    try:
                        os.remove(img.path)
                        deleted += 1
                    except OSError:
                        errors += 1

                self.group.images = [largest]
                self._show_info(f'已删除 {deleted} 张' + (f', {errors} 张失败' if errors else ''))
                if self.parent:
                    self.parent.remove_widget(self)
            popup.dismiss()

        wasted = self._format_size(sum(i.file_size for i in others))
        content = BoxLayout(orientation='vertical', spacing='8dp', padding='8dp')
        content.add_widget(Label(text=f'保留:\n{os.path.basename(largest.path)}\n\n删除 {len(others)} 张，释放 {wasted}'))
        btns = BoxLayout(size_hint_y=None, height='40dp', spacing='8dp')
        btns.add_widget(Button(text='取消', on_release=lambda x: popup.dismiss()))
        btns.add_widget(Button(text='确认删除', on_release=lambda x: do_delete(True),
                               background_normal='', background_color=(0.9, 0.3, 0.3, 1)))
        content.add_widget(btns)

        popup = Popup(title='保留最大文件', content=content, size_hint=(0.75, 0.4))
        popup.open()

    def _delete_all_except_largest(self):
        """Delete all files in group except the largest."""
        self._keep_largest()

    @staticmethod
    def _show_error(msg):
        content = BoxLayout(orientation='vertical', spacing='8dp', padding='8dp')
        content.add_widget(Label(text=msg))
        btn = Button(text='确定', size_hint_y=None, height='36dp',
                     on_release=lambda x: popup.dismiss())
        content.add_widget(btn)
        popup = Popup(title='错误', content=content, size_hint=(0.6, 0.3))
        popup.open()

    @staticmethod
    def _show_info(msg):
        content = BoxLayout(orientation='vertical', spacing='8dp', padding='8dp')
        content.add_widget(Label(text=msg))
        btn = Button(text='确定', size_hint_y=None, height='36dp',
                     on_release=lambda x: popup.dismiss())
        content.add_widget(btn)
        popup = Popup(title='提示', content=content, size_hint=(0.6, 0.3))
        popup.open()

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


class ResultsScreen(BoxLayout, Screen):
    """Displays duplicate groups with filtering, preview, and delete actions."""

    total_groups = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._report = None
        self._cache = None
        self._all_groups = []
        self._filter = 'all'  # 'all' | 'exact' | 'similar'
        self._tabs_built = False

    def set_report(self, report, cache=None):
        """Load a scan report into the results screen."""
        self._report = report
        self._cache = cache
        self._all_groups = report.all_groups
        self.total_groups = len(self._all_groups)
        self._filter = 'all'
        if not self._tabs_built:
            self._build_tabs()
            self._tabs_built = True
        self._refresh_list()

    def _build_tabs(self):
        """Build the tab toggle buttons."""
        tab_bar = self.ids.tab_bar
        tab_bar.clear_widgets()

        tabs = [
            ('all', '全部'),
            ('exact', '精确重复'),
            ('similar', '视觉相似'),
        ]

        for filter_key, label in tabs:
            btn = ToggleButton(
                text=label,
                group='filter_tabs',
                state='down' if filter_key == self._filter else 'normal',
                size_hint_x=1,
                background_normal='',
                font_size='13sp'
            )
            btn.bind(on_press=lambda x, k=filter_key: self._on_filter_change(k))
            tab_bar.add_widget(btn)

    def _on_filter_change(self, filter_key):
        self._filter = filter_key
        self._refresh_list()

    def _refresh_list(self):
        """Rebuild the group card list based on current filter."""
        container = self.ids.groups_container
        container.clear_widgets()

        if self._filter == 'exact':
            groups = [g for g in self._all_groups if g.duplicate_type == 'exact']
        elif self._filter == 'similar':
            groups = [g for g in self._all_groups if g.duplicate_type == 'similar']
        else:
            groups = self._all_groups

        if not groups:
            noresult = Label(
                text='没有发现重复图片 🎉',
                size_hint_y=None,
                height='60dp',
                font_size='16sp',
                color=(0.5, 0.5, 0.5, 1)
            )
            container.add_widget(noresult)
            return

        for group in groups:
            card = GroupCard(group, self._cache)
            container.add_widget(card)

        self.total_groups = len(groups)

    def export_report(self):
        """Export scan report to HTML file."""
        if not self._report:
            return

        from ..exporter import ReportExporter

        # Use user_data_dir or fallback to home
        app = App.get_running_app()
        output_dir = app.user_data_dir if app and app.user_data_dir else os.path.expanduser('~')

        try:
            path = ReportExporter.export_html(self._report, output_dir)
            popup = Popup(
                title='报告已导出',
                content=Label(text=f'报告已保存到:\n{path}'),
                size_hint=(0.7, 0.35),
            )
            popup.open()
        except Exception as e:
            popup = Popup(
                title='导出失败',
                content=Label(text=f'导出报告时出错:\n{e}'),
                size_hint=(0.7, 0.35),
            )
            popup.open()

    def quick_clean(self):
        """Show quick clean suggestions: delete all duplicates except one per group."""
        if not self._all_groups:
            return

        total_files = 0
        total_wasted = 0
        for g in self._all_groups:
            if len(g.images) > 1:
                # Keep largest, delete rest
                largest = max(g.images, key=lambda x: x.file_size)
                others = [i for i in g.images if i.path != largest.path]
                total_files += len(others)
                total_wasted += sum(i.file_size for i in others)

        def do_clean(confirmed):
            if confirmed:
                deleted = 0
                errors = 0
                for g in self._all_groups:
                    if len(g.images) <= 1:
                        continue
                    largest = max(g.images, key=lambda x: x.file_size)
                    for img in g.images:
                        if img.path != largest.path:
                            try:
                                os.remove(img.path)
                                deleted += 1
                            except OSError:
                                errors += 1
                    g.images = [largest]

                self._refresh_list()
                msg = f'已删除 {deleted} 张重复图片'
                if errors:
                    msg += f', {errors} 张删除失败'
                popup2 = Popup(title='清理完成', content=Label(text=msg),
                               size_hint=(0.7, 0.3))
                popup2.open()
            popup.dismiss()

        def format_size(s):
            if s < 1024 * 1024:
                return f'{s / 1024:.1f} KB'
            else:
                return f'{s / (1024 * 1024):.1f} MB'

        content = BoxLayout(orientation='vertical', spacing='8dp', padding='8dp')
        content.add_widget(Label(
            text=f'将删除 {total_files} 张重复图片\n'
                 f'每组保留最大的文件\n'
                 f'预计释放: {format_size(total_wasted)}',
            halign='center'
        ))
        btns = BoxLayout(size_hint_y=None, height='40dp', spacing='8dp')
        btns.add_widget(Button(text='取消', on_release=lambda x: popup.dismiss()))
        btns.add_widget(Button(
            text='确认清理', on_release=lambda x: do_clean(True),
            background_normal='', background_color=(0.9, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        ))
        content.add_widget(btns)

        popup = Popup(title='一键清理', content=content, size_hint=(0.75, 0.4))
        popup.open()

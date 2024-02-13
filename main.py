import wx
import wx.lib.scrolledpanel
import obs_text
import osc_server

SQUARE_BUTTON_SIZE = wx.Size(24, 24)

class TextSwitcherGUI(wx.Frame):
    def __init__(self):
        super().__init__(None, title="OBS OSC Text Switcher", style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE)
        self.SetMinSize((400, 250))

        self.obs_text_switcher = obs_text.OBSTextSwitcher()
        self.obs_text_switcher.load_settings()

        self.menu_bar = wx.MenuBar()
        self.file_menu = wx.Menu()
        self.menu_bar.Append(self.file_menu, "&File")
        self.menu_item_new = wx.MenuItem(self.file_menu, text="New\tCtrl+N", id=wx.ID_NEW)
        self.menu_item_open = wx.MenuItem(self.file_menu, text="Open...\tCtrl+O", id=wx.ID_OPEN)
        self.menu_item_save = wx.MenuItem(self.file_menu, text="Save\tCtrl+S", id=wx.ID_SAVE)
        self.menu_item_save_as = wx.MenuItem(self.file_menu, text="Save as...\tCtrl+Shift+S", id=wx.ID_SAVEAS)
        self.file_menu.Append(self.menu_item_new)
        self.file_menu.Append(self.menu_item_open)
        self.file_menu.Append(self.menu_item_save)
        self.file_menu.Append(self.menu_item_save_as)
        self.SetMenuBar(self.menu_bar)

        self.Bind(wx.EVT_MENU, self.new_file, self.menu_item_new)
        self.Bind(wx.EVT_MENU, self.open_file, self.menu_item_open)
        self.Bind(wx.EVT_MENU, self.save_file, self.menu_item_save)
        self.Bind(wx.EVT_MENU, self.save_file_as, self.menu_item_save_as)
        
        self.lines_panel = wx.lib.scrolledpanel.ScrolledPanel(self)
        self.lines_panel.SetupScrolling()
        self.lines_panel.SetAutoLayout(True)
        
        self.control_panel = ControlPanel(self)

        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(self.lines_panel, 3, wx.EXPAND)
        self.main_sizer.Add(self.control_panel, 2, wx.EXPAND)
        self.SetSizer(self.main_sizer)

        self.scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        self.lines_panel.SetSizer(self.scroll_sizer)
        self.add_button = wx.Button(self.lines_panel, label="+", size=SQUARE_BUTTON_SIZE)
        self.add_button.Bind(wx.EVT_BUTTON, lambda _: self.add_new_line())
        self.scroll_sizer.Add(self.add_button, 0, wx.EXPAND | wx.ALL, 4)

        self.text_lines = []
        self.active_index = -1
        self.current_file = None
        self.file_dirty = False

        self.osc_server = osc_server.OSCServer(self)

        self.Bind(wx.EVT_CLOSE, self.on_close_window)
    
    def ask_save_file(self):
        dialog = wx.MessageDialog(self, "Do you want to save the current lines?", "Save text?", wx.YES | wx.NO | wx.CANCEL | wx.ICON_QUESTION)
        return dialog.ShowModal()

    def on_close_window(self, event):
        if self.text_lines and self.file_dirty:
            choice = self.ask_save_file()
            if choice == wx.ID_CANCEL:
                return
            if choice == wx.ID_YES:
                self.save_file()
        self.osc_server.shutdown()
        event.Skip()
    
    def load_file_from_path(self, path):
        self.current_file = open(path, "r+", encoding="utf8")
        self.clear_lines()
        i = 0
        for line in self.current_file:
            if i >= 200:
                return
            self.add_new_line(line.removesuffix("\n"))
            i += 1
    
    def save_current_file(self):
        if self.current_file is None:
            raise IOError("There is no file currently opened")
        self.current_file.truncate(0)
        if self.current_file.seekable():
            self.current_file.seek(0)
        for text_line in self.text_lines:
            self.current_file.write(text_line.get_text())
            self.current_file.write("\n")
        self.current_file.flush()
        self.file_dirty = False

    def new_file(self, _=None):
        if self.text_lines and self.file_dirty:
            choice = self.ask_save_file()
            if choice == wx.ID_CANCEL:
                return wx.ID_CANCEL
            if choice == wx.ID_YES:
                self.save_file()
        
        if self.current_file:
            self.current_file.close()
            self.current_file = None

        self.clear_lines()
        self.file_dirty = False

    def open_file(self, _=None):
        if self.text_lines and self.file_dirty:
            choice = self.ask_save_file()
            if choice == wx.ID_CANCEL:
                return
            if choice == wx.ID_YES:
                if self.save_file() == wx.ID_CANCEL:
                    return wx.ID_CANCEL

        file_dialog = wx.FileDialog(self, style=wx.FD_OPEN, wildcard="*.txt")
        if file_dialog.ShowModal() == wx.ID_CANCEL:
            return wx.ID_CANCEL
        
        path = file_dialog.GetPath()
        self.load_file_from_path(path)
        self.file_dirty = False

    def save_file(self, _=None):
        if not self.current_file:
            if self.save_file_as() == wx.ID_CANCEL:
                return wx.ID_CANCEL
        
        self.save_current_file()
    
    def save_file_as(self, _=None):
        file_dialog = wx.FileDialog(self, style=wx.FD_SAVE, wildcard="*.txt")
        if file_dialog.ShowModal() == wx.ID_CANCEL:
            return wx.ID_CANCEL
        
        path = file_dialog.GetPath()
        self.current_file = open(path, "w+", encoding="utf8")
        self.save_current_file()

    def show_exception(self, exception):
        wx.MessageBox(str(exception), caption=type(exception).__name__, parent=self, style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
    
    def update_line_states(self):
        for index, line_panel in enumerate(self.text_lines):
            if index == self.active_index:
                line_panel.set_state("active")
            elif index == self.active_index + 1:
                line_panel.set_state("preview")
            else:
                line_panel.set_state(None)
    
    def add_new_line(self, text="", before_line=None):
        line_panel = TextLine(self.lines_panel, self, text)
        index = self.text_lines.index(before_line) if before_line else len(self.text_lines)
        self.text_lines.insert(index, line_panel)
        self.scroll_sizer.Insert(index, line_panel, 0, wx.EXPAND | wx.ALL, 4)
        self.lines_panel.FitInside()
        self.update_line_states()
        self.file_dirty = True

    def remove_line(self, line: "TextLine"):
        line.Destroy()
        self.text_lines.remove(line)
        self.lines_panel.FitInside()
        if self.active_index >= len(self.text_lines):
            self.active_index = len(self.text_lines) - 1
        self.update_line_states()
        self.file_dirty = True
    
    def clear_lines(self):
        for text_line in self.text_lines:
            text_line.Destroy()
        self.text_lines.clear()
        self.lines_panel.FitInside()
        self.active_index = -1
    
    def update_line_states(self):
        for index, text_line in enumerate(self.text_lines):
            text_line.update_state(index, self.active_index)

    def switch_to_line_index(self, line_index):
        if line_index < 0 or line_index >= len(self.text_lines):
            return
        new_line = self.text_lines[line_index]
        try:
            if self.obs_text_switcher.switch_text(new_line.get_text()):
                self.active_index = line_index
                self.update_line_states()
        except Exception as e:
            self.show_exception(e)
    
    def switch_to_text_line(self, text_line):
        try:
            index = self.text_lines.index(text_line)
            self.switch_to_line_index(index)
        except ValueError:
            pass

    def next_line(self):
        self.switch_to_line_index(self.active_index + 1)

    def prev_line(self):
        self.switch_to_line_index(self.active_index - 1)
    
    def hide_text(self):
        self.obs_text_switcher.switch_text("")

class TextLine(wx.Panel):
    def __init__(self, parent, gui: TextSwitcherGUI, text):
        super().__init__(parent)
        self.text_switcher_gui = gui
        self.add_button = wx.Button(self, label="+", size=SQUARE_BUTTON_SIZE)
        self.add_button.Bind(wx.EVT_BUTTON, lambda _: gui.add_new_line(before_line=self))
        self.remove_button = wx.Button(self, label="-", size=SQUARE_BUTTON_SIZE)
        self.remove_button.Bind(wx.EVT_BUTTON, lambda _: gui.remove_line(self))
        self.entry = wx.TextCtrl(self)
        self.entry.SetValue(text)
        self.entry.Bind(wx.EVT_KEY_DOWN, self.key_down_event)
        self.go_button = wx.Button(self, label="Go", size=wx.Size(30, SQUARE_BUTTON_SIZE.height))
        self.go_button.Bind(wx.EVT_BUTTON, lambda _: gui.switch_to_text_line(self))

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.add_button)
        self.sizer.Add(self.remove_button)
        self.sizer.Add(self.entry, 1, wx.EXPAND)
        self.sizer.Add(self.go_button)
        self.SetSizer(self.sizer)
    
    def get_text(self):
        return self.entry.GetValue()
    
    def update_state(self, index, active_index):
        if index == active_index:
            self.entry.SetBackgroundColour(wx.Colour(255, 200, 200))
        elif index == active_index + 1:
            self.entry.SetBackgroundColour(wx.Colour(200, 255, 200))
        else:
            self.entry.SetBackgroundColour(None)
        self.entry.Refresh()
    
    def focus_line(self):
        self.entry.SetFocus()
    
    def key_down_event(self, event: wx.KeyEvent):
        text_lines = self.text_switcher_gui.text_lines
        index = text_lines.index(self)
        if event.KeyCode == wx.WXK_DOWN:
            index += 1
        elif event.KeyCode == wx.WXK_UP:
            index -= 1
        else:
            self.text_switcher_gui.file_dirty = True
            event.Skip()
            return
        
        if index >= 0 and index < len(text_lines):
            text_lines[index].focus_line()

class ControlPanel(wx.Panel):
    def __init__(self, parent: TextSwitcherGUI):
        super().__init__(parent)
        self.text_switcher_gui = parent
        self.obs_text_switcher = parent.obs_text_switcher

        self.scene1_selector = wx.Choice(self)
        self.scene2_selector = wx.Choice(self)
        self.selector_divider1 = wx.StaticLine(self)

        self.source1_selector = wx.Choice(self)
        self.source2_selector = wx.Choice(self)
        self.selector_divider2 = wx.StaticLine(self)
        
        self.buttons_panel = wx.Panel(self)
        self.prev_button = wx.Button(self.buttons_panel, label="Previous", size=wx.Size(-1, 40))
        self.prev_button.Bind(wx.EVT_BUTTON, lambda _: parent.prev_line())
        self.next_button = wx.Button(self.buttons_panel, label="Next", size=wx.Size(-1, 40))
        self.next_button.Bind(wx.EVT_BUTTON, lambda _: parent.next_line())

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer_args = (0, wx.EXPAND | wx.ALL, 4)

        for selector in [self.scene1_selector, self.scene2_selector]:
            selector.Bind(wx.EVT_CHOICE, self.update_choices)
            self.sizer.Add(selector, *sizer_args)
        
        self.sizer.Add(self.selector_divider1, *sizer_args)

        for selector in [self.source1_selector, self.source2_selector]:
            selector.Bind(wx.EVT_CHOICE, self.update_choices)
            self.sizer.Add(selector, *sizer_args)
        
        self.sizer.Add(self.selector_divider2, *sizer_args)        
        self.sizer.Add(self.buttons_panel, *sizer_args)

        self.SetSizer(self.sizer)

        
        for button in [self.prev_button, self.next_button]:
            self.buttons_sizer.Add(button, 1)
        
        self.buttons_panel.SetSizer(self.buttons_sizer)

        self.update_choices()
    
    """
    Updates the items of a Choice and selects the matching item again if it still exists.
    Returns the selected item or None if the label is now selected.
    """
    def update_selector_items(self, selector: wx.Choice, new_items, label_text, default_item=None, select_first_item=False):
        old_items = selector.GetItems()
        old_index = selector.GetSelection()
        old_item = default_item if old_index == -1 else old_items[old_index]
        new_index = new_items.index(old_item) if old_item is not None and old_item in new_items else -1
        selector.SetItems([label_text, *new_items])

        if new_index == -1:
            if select_first_item and len(new_items) >= 1:
                selector.Select(1)
                return new_items[0]
            
            selector.Select(0)
            return None
        
        selector.Select(new_index + 1)  # +1 because of label item
        return new_items[new_index]

    def update_choices(self, _=None):
        try:
            scenes = self.obs_text_switcher.get_scene_names()

            scene1 = self.update_selector_items(self.scene1_selector, scenes, "Scene 1", default_item=self.obs_text_switcher.scene1)
            scene2 = self.update_selector_items(self.scene2_selector, scenes, "Scene 2", default_item=self.obs_text_switcher.scene2)
            
            scene1_sources = [] if scene1 is None else self.obs_text_switcher.get_text_sources(scene1)
            scene2_sources = [] if scene2 is None else self.obs_text_switcher.get_text_sources(scene2)

            source1 = self.update_selector_items(self.source1_selector, scene1_sources, "Source 1",
                                                 default_item=self.obs_text_switcher.source1,
                                                 select_first_item=True)
            source2 = self.update_selector_items(self.source2_selector, scene2_sources, "Source 2",
                                                 default_item=self.obs_text_switcher.source2,
                                                 select_first_item=True)

            self.obs_text_switcher.scene1 = scene1
            self.obs_text_switcher.scene2 = scene2
            self.obs_text_switcher.source1 = source1
            self.obs_text_switcher.source2 = source2
            self.obs_text_switcher.save_settings()

            for choice in [scene1, scene2, source1, source2]:
                if choice is None:
                    self.buttons_panel.Disable()
                    return
            self.buttons_panel.Enable()
        except Exception as e:
            self.text_switcher_gui.show_exception(e)

if __name__ == "__main__":
    app = wx.App()
    gui = TextSwitcherGUI()
    gui.Show()
    app.MainLoop()

import threading
import config
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from main import TextSwitcherGUI


class OSCServer(threading.Thread):
    def __init__(self, text_switcher_gui: TextSwitcherGUI):
        super().__init__()
        self.text_switcher_gui = text_switcher_gui

        self.dispatcher = Dispatcher()
        self.dispatcher.map("/obstext/next", self.next_text)
        self.dispatcher.map("/obstext/previous", self.previous_text)
        self.dispatcher.map("/obstext/hide", self.hide_text)

        self.server = BlockingOSCUDPServer((config.OSC_LISTEN_HOST, config.OSC_LISTEN_PORT), self.dispatcher)
        self.start()

    def run(self):
        self.server.serve_forever()
    
    def shutdown(self):
        self.server.shutdown()

    def next_text(self, address, *args):
        if len(args) == 1:
            self.text_switcher_gui.switch_to_line_index(args[0])
        else:
            self.text_switcher_gui.next_line()

    def previous_text(self, address, *args):
        self.text_switcher_gui.prev_line()

    def hide_text(self, address, *args):
        self.text_switcher_gui.hide_text()

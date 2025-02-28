import threading
import rtmidi

class MidiController(threading.Thread):
    def __init__(self, text_switcher_gui):
        super().__init__()
        self.text_switcher_gui = text_switcher_gui
        self.midi_in = rtmidi.RtMidiIn()
        self.running = True
        self.start()

    def run(self):
        while self.running:
            message = self.midi_in.getMessage(250)
            if message:
                self.handle_message(message)
    
    def get_devices(self):
        port_count = self.midi_in.getPortCount()
        return [self.midi_in.getPortName(i) for i in range(port_count)]
    
    def open_port(self, port_number):
        self.midi_in.closePort()
        self.midi_in = rtmidi.RtMidiIn()
        self.midi_in.openPort(port_number)
    
    def close_port(self):
        self.midi_in.closePort()

    def shutdown(self):
        self.running = False
        self.midi_in.closePort()
    
    def handle_message(self, msg):
        print(msg.isNoteOn())
        print(msg.getMidiNoteName(msg.getNoteNumber()))

        # self.text_switcher_gui.next_line()
        # self.text_switcher_gui.prev_line()
        # self.text_switcher_gui.hide_text()

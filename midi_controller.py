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
        port_count = self.midi_in.getPortCount()
        if port_count == 0:
            print("No MIDI input ports available.")
            return
        
        for i in range(port_count):
            print(f"Port {i}: {self.midi_in.getPortName(i)}")
        
        port_index = int(input("Enter the port index: "))
        self.midi_in.openPort(port_index)

        while self.running:
            message = self.midi_in.getMessage(250)
            if message:
                self.handle_message(message)

    def shutdown(self):
        self.running = False
        self.midi_in.closePort()
    
    def handle_message(self, msg):
        print(msg.isNoteOn())
        print(msg.getMidiNoteName(msg.getNoteNumber()))

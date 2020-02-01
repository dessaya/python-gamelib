import tkinter as tk
from tkinter.font import Font
from tkinter import simpledialog, messagebox
from collections import namedtuple
from queue import Queue, Empty
from enum import Enum
import threading
import traceback
import time
import signal
import os

class EventType(Enum):
    KeyPress = 'KeyPress'
    KeyRelease = 'KeyRelease'
    Motion = 'Motion'
    ButtonPress = 'ButtonPress'
    ButtonRelease = 'ButtonRelease'

class Event:
    def __init__(self, tkevent):
        self.tkevent = tkevent

    def __getattr__(self, k):
        if k == 'type': return EventType[str(self.tkevent.type)]
        if k == 'key': return self.tkevent.keysym
        if k == 'mouse_button': return self.tkevent.num
        return getattr(self.tkevent, k)

    def __repr__(self):
        return repr(self.tkevent)

class _TkWindow(tk.Tk):
    instance = None
    initialized = threading.Event()
    commands = Queue()

    def __init__(self):
        super().__init__()

        self.closed = False

        self.title("Gamelib")
        self.resizable(False, False)

        self.assets = {}

        self.canvas = tk.Canvas(background='black')
        self.canvas.grid(column=0, row=0, sticky="nwes")

        for event_type in EventType:
            self.bind(f"<{event_type.name}>", self.handle_event)
        self.bind(f"<<notify>>", self.process_commands)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.canvas.focus_set()
        self.after_idle(self.process_commands)

    def on_closing(self):
        self.closed = True
        self.quit()
        self.update()

    def notify(self):
        if not self.closed:
            self.event_generate('<<notify>>')

    def process_commands(self, *args):
        while True:
            try:
                method, *args = _TkWindow.commands.get(False)
                getattr(self, method)(*args)
            except Empty:
                break

    def handle_event(self, tkevent):
        _GameThread.events.put(Event(tkevent))

    def resize(self, w, h):
        self.canvas.configure(width=w, height=h)

    def clear(self):
        self.canvas.delete("all")

    def draw_image(self, path, x, y):
        self.canvas.create_image(x, y, anchor='nw', image=self.get_image(path))

    def draw(self, type, args, kwargs):
        options = {'fill': 'white'}
        options.update(kwargs)
        getattr(self.canvas, f'create_{type}')(*args, **options)

    def draw_text(self, text, x, y, size, kwargs):
        options = {'fill': 'white'}
        options.update(kwargs)
        self.canvas.create_text(x, y, text=text, font=self.get_font(size), **options)

    def get_font(self, size):
        name = f'font-{size}'
        if name not in self.assets:
            self.assets[name] = Font(size=size)
        return self.assets[name]

    def get_image(self, path):
        if path not in self.assets:
            self.assets[path] = tk.PhotoImage(file=path)
        return self.assets[path]

    def say(self, message):
        messagebox.showinfo(self.title(), message, parent=self)

    def input(self, prompt, response):
        response.put(simpledialog.askstring(self.title(), prompt, parent=self))

    def with_window(self, func, args):
        func(self, *args)

def _audio_init():
    # shamelessly stolen from https://github.com/TaylorSMarks/playsound

    class PlaysoundException(Exception):
        pass

    def _playsoundWin(sound):
        from ctypes import c_buffer, windll
        from random import random
        from sys    import getfilesystemencoding

        def winCommand(*command):
            buf = c_buffer(255)
            command = ' '.join(command).encode(getfilesystemencoding())
            errorCode = int(windll.winmm.mciSendStringA(command, buf, 254, 0))
            if errorCode:
                errorBuffer = c_buffer(255)
                windll.winmm.mciGetErrorStringA(errorCode, errorBuffer, 254)
                exceptionMessage = ('\n    Error ' + str(errorCode) + ' for command:'
                                    '\n        ' + command.decode() +
                                    '\n    ' + errorBuffer.value.decode())
                raise PlaysoundException(exceptionMessage)
            return buf.value

        alias = 'playsound_' + str(random())
        winCommand('open "' + sound + '" alias', alias)
        winCommand('set', alias, 'time format milliseconds')
        durationInMS = winCommand('status', alias, 'length')
        winCommand('play', alias, 'from 0 to', durationInMS.decode())

    def _playsoundOSX(sound):
        from AppKit     import NSSound
        from Foundation import NSURL

        if '://' not in sound:
            if not sound.startswith('/'):
                sound = os.getcwd() + '/' + sound
            sound = 'file://' + sound
        url   = NSURL.URLWithString_(sound)
        nssound = NSSound.alloc().initWithContentsOfURL_byReference_(url, True)
        if not nssound:
            raise IOError('Unable to load sound named: ' + sound)
        nssound.play()

    def _playsoundNix(sound):
        from urllib.request import pathname2url

        import gi
        gi.require_version('Gst', '1.0')
        from gi.repository import Gst

        Gst.init(None)

        playbin = Gst.ElementFactory.make('playbin', 'playbin')
        if sound.startswith(('http://', 'https://')):
            playbin.props.uri = sound
        else:
            playbin.props.uri = 'file://' + pathname2url(os.path.abspath(sound))

        set_result = playbin.set_state(Gst.State.PLAYING)
        if set_result != Gst.StateChangeReturn.ASYNC:
            raise PlaysoundException(
                "playbin.set_state returned " + repr(set_result))

        bus = playbin.get_bus()
        bus.add_signal_watch()
        def on_message(bus, message):
            if message.type in (Gst.MessageType.EOS, Gst.MessageType.ERROR):
                playbin.set_state(Gst.State.NULL)
        bus.connect("message", on_message)

    from platform import system
    system = system()

    if system == 'Windows':
        return _playsoundWin
    elif system == 'Darwin':
        return _playsoundOSX
    else:
        return _playsoundNix

_play_sound = _audio_init()

class _GameThread(threading.Thread):
    instance = None
    initialized = threading.Event()
    events = Queue()

    def start(self, game_main, args):
        self.game_main = game_main
        self.args = args
        super().start()

    def run(self):
        try:
            self.game_main(*self.args)
        finally:
            self.send_command_to_tk('destroy', notify=True)

    def notify_tk(self):
        self.wait_for_tk()
        w = _TkWindow.instance
        if w:
            w.notify()

    def wait_for_tk(self):
        if not _TkWindow.initialized.is_set():
            _GameThread.initialized.set()

            # block until Tk is initialized
            _TkWindow.initialized.wait()

    def send_command_to_tk(self, *args, notify=False):
        _TkWindow.commands.put(args)
        if notify:
            self.notify_tk()

    def wait(self, event_type=None):
        self.notify_tk()
        if not _TkWindow.instance:
            return None
        while True:
            event = _GameThread.events.get()
            if not event or not event_type or event.type == event_type:
                return event

    def get_events(self):
        self.notify_tk()
        events = []
        while True:
            try:
                event = _GameThread.events.get(False)
                if not event:
                    break
                events.append(event)
            except Empty:
                break
        return events

    def title(self, s):
        self.send_command_to_tk('title', s)

    def draw_begin(self):
        self.send_command_to_tk('clear')

    def draw_image(self, path, x, y):
        self.send_command_to_tk('draw_image', path, x, y)

    def draw_text(self, text, x, y, size=12, **kwargs):
        self.send_command_to_tk('draw_text', text, x, y, size, kwargs)

    def draw_arc(self, *args, **kwargs):
        self.send_command_to_tk('draw', 'arc', args, kwargs)

    def draw_line(self, *args, **kwargs):
        self.send_command_to_tk('draw', 'line', args, kwargs)

    def draw_oval(self, *args, **kwargs):
        self.send_command_to_tk('draw', 'oval', args, kwargs)

    def draw_polygon(self, *args, **kwargs):
        self.send_command_to_tk('draw', 'polygon', args, kwargs)

    def draw_rectangle(self, *args, **kwargs):
        self.send_command_to_tk('draw', 'rectangle', args, kwargs)

    def draw_end(self):
        self.send_command_to_tk('update', notify=True)

    def resize(self, w, h):
        self.send_command_to_tk('resize', w, h)

    def say(self, message):
        self.send_command_to_tk('say', message, notify=True)

    def input(self, prompt):
        response = Queue()
        self.send_command_to_tk('input', prompt, response, notify=True)
        return response.get()

    def is_alive(self):
        self.wait_for_tk()
        return bool(_TkWindow.instance)

    def loop(self, fps=30):
        while is_alive():
            frame_duration = 1.0 / fps
            a = time.time()
            yield
            b = time.time()
            time.sleep(max(0, frame_duration - (b - a)))

_GameThread.instance = _GameThread()

wait = _GameThread.instance.wait
get_events = _GameThread.instance.get_events
title = _GameThread.instance.title
draw_begin = _GameThread.instance.draw_begin
draw_image = _GameThread.instance.draw_image
draw_text = _GameThread.instance.draw_text
draw_arc = _GameThread.instance.draw_arc
draw_line = _GameThread.instance.draw_line
draw_oval = _GameThread.instance.draw_oval
draw_polygon = _GameThread.instance.draw_polygon
draw_rectangle = _GameThread.instance.draw_rectangle
draw_end = _GameThread.instance.draw_end
resize = _GameThread.instance.resize
say = _GameThread.instance.say
input = _GameThread.instance.input
is_alive = _GameThread.instance.is_alive
loop = _GameThread.instance.loop
play_sound = _play_sound

def _excepthook(args):
    traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback)

def _sigint_handler(sig, frame):
    w = _TkWindow.instance
    if w:
        w.on_closing()

def init(game_main, args=None):
    threading.excepthook = _excepthook

    _GameThread.instance.start(game_main, args or [])

    # block until wait() called on game thread
    _GameThread.initialized.wait()

    _TkWindow.instance = _TkWindow()
    _TkWindow.initialized.set()

    signal.signal(signal.SIGINT, _sigint_handler)

    try:
        _TkWindow.instance.mainloop()
    finally:
        _GameThread.events.put(None)
        _TkWindow.instance = None
        _GameThread.instance.join(1)
        if _GameThread.instance.is_alive():
            print('Killing unresponsive game thread. Make sure to call get_events() or wait() periodically.')
            os._exit(1)

if __name__ == '__main__':
    def interactive_main(_locals):
        import code
        code.interact(local=_locals)

    init(interactive_main, args=[locals()])

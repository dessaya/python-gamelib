import tkinter as tk
from tkinter.font import Font
from tkinter import simpledialog, messagebox
from collections import namedtuple
from queue import Queue
import threading
import traceback
import time
from enum import Enum

_commands = Queue()
_events = Queue()

_tk_initialized = threading.Event()
_game_thread_initialized = threading.Event()

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

    def __init__(self):
        super().__init__()

        self.title("TK Game")
        self.resizable(False, False)

        self.assets = {}

        self.canvas = tk.Canvas(background='black')
        self.canvas.grid(column=0, row=0, sticky="nwes")

        for event_type in EventType:
            self.bind(f"<{event_type.name}>", self.handle_event)
        self.bind("<<notify>>", self.process_commands)

        self.canvas.focus_set()
        self.after_idle(self.process_commands)

    def notify(self):
        self.update_idletasks()
        self.event_generate('<<notify>>')

    def process_commands(self, *args):
        while not _commands.empty():
            method, *args = _commands.get()
            getattr(self, method)(*args)

    def handle_event(self, tkevent):
        _events.put(Event(tkevent))

    def resize(self, w, h):
        self.canvas.configure(width=w, height=h)

    def clear(self):
        self.canvas.delete("all")

    def draw_image(self, path, x, y):
        self.canvas.create_image(x, y, anchor='nw', image=self.get_image(path))

    def draw(self, type, args, kwargs):
        getattr(self.canvas, f'create_{type}')(*args, **kwargs)

    def draw_text(self, text, x, y, size, color):
        self.canvas.create_text(x, y, anchor='nw', text=text, fill=color, font=self.get_font(size))

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
                from os import getcwd
                sound = getcwd() + '/' + sound
            sound = 'file://' + sound
        url   = NSURL.URLWithString_(sound)
        nssound = NSSound.alloc().initWithContentsOfURL_byReference_(url, True)
        if not nssound:
            raise IOError('Unable to load sound named: ' + sound)
        nssound.play()

    def _playsoundNix(sound):
        import os
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

def game_thread_main(callback, args):
    try:
        callback(*args)
    except:
        traceback.print_exc()
    finally:
        _game_thread_exit()

def _game_thread_exit():
    _commands.put(('destroy',))
    _game_thread_notify()

def init(callback, *args):
    # start game thread
    threading.Thread(target=game_thread_main, args=[callback, args]).start()

    # block until wait() called on game thread
    _game_thread_initialized.wait()

    _TkWindow.instance = _TkWindow()
    _tk_initialized.set()
    _TkWindow.instance.mainloop()
    _events.put(None)
    _TkWindow.instance = None

def _game_thread_wait_for_tk():
    if not _tk_initialized.is_set():
        _game_thread_initialized.set()

        # block until Tk is initialized
        _tk_initialized.wait()

def _game_thread_notify():
    _game_thread_wait_for_tk()
    if _TkWindow.instance:
        _TkWindow.instance.notify()

def wait():
    _game_thread_wait_for_tk()
    if not _TkWindow.instance:
        return None
    return _events.get()

def get_events():
    _game_thread_wait_for_tk()
    events = []
    while not _events.empty():
        events.append(_events.get())
    return events

def title(s):
    _commands.put(('title', s))
    _game_thread_notify()

def draw_begin():
    _commands.put(('clear',))

def draw_image(path, x, y):
    _commands.put(('draw_image', path, x, y))

def draw_text(text, x, y, size=12, color='white'):
    _commands.put(('draw_text', text, x, y, size, color))

def draw_arc(*args, **kwargs):
    _commands.put(('draw', 'arc', args, kwargs))

def draw_line(*args, **kwargs):
    _commands.put(('draw', 'line', args, kwargs))

def draw_oval(*args, **kwargs):
    _commands.put(('draw', 'oval', args, kwargs))

def draw_polygon(*args, **kwargs):
    _commands.put(('draw', 'polygon', args, kwargs))

def draw_rectangle(*args, **kwargs):
    _commands.put(('draw', 'rectangle', args, kwargs))

def draw_end():
    _game_thread_notify()

def resize(w, h):
    _commands.put(('resize', w, h))
    _game_thread_notify()

def say(message):
    _commands.put(('say', message))
    _game_thread_notify()

def input(prompt):
    response = Queue()
    _commands.put(('input', prompt, response))
    _game_thread_notify()
    return response.get()

def with_window(func, *args):
    _commands.put(('with_window', func, args))
    _game_thread_notify()

def is_alive():
    _game_thread_wait_for_tk()
    return bool(_TkWindow.instance)

def loop(fps):
    now = 0
    frame_duration = 1.0 / fps
    while is_alive():
        a = time.time()
        yield
        b = time.time()
        time.sleep(max(0, frame_duration - (b - a)))

play_sound = _audio_init()

if __name__ == '__main__':
    def interactive_main(local):
        _game_thread_notify()
        import code
        code.interact(local=local)

    init(interactive_main, locals())

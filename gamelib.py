"""
Gamelib is a pure-Python single-file library/framework for writing simple games. It is
intended for educational purposes (e.g. to be used in basic programming courses).

https://github.com/dessaya/python-gamelib
"""

import tkinter as tk
from tkinter.font import Font
from tkinter import simpledialog, messagebox
from queue import Queue, Empty
from enum import Enum
import threading
import time
import signal
import os
import sys

class _TkWindow(tk.Tk):
    instance = None
    initialized = threading.Event()
    commands = Queue()

    busy_count = 0
    idle = threading.Event()
    idle.set()

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
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.canvas.focus_set()
        self.after_idle(self.process_commands)

    def close(self):
        self.closed = True
        self.quit()
        self.update()

    def notify(self):
        if not self.closed:
            self.event_generate('<<notify>>', when='tail')

    def process_commands(self, *args):
        _TkWindow.busy_count += 1
        _TkWindow.idle.clear()
        try:
            while True:
                try:
                    method, *args = _TkWindow.commands.get(False)
                    getattr(self, method)(*args)
                except Empty:
                    break
        finally:
            _TkWindow.busy_count -= 1
            if _TkWindow.busy_count == 0:
                _TkWindow.idle.set()

    def handle_event(self, tkevent):
        _GameThread.events.put(Event(tkevent))

    def resize(self, w, h):
        self.canvas.configure(width=w, height=h)

    def clear(self):
        self.canvas.delete("all")

    def icon(self, path):
        self.tk.call('wm', 'iconphoto', self._w, self.get_image(path))

    def draw_image(self, path, x, y):
        self.canvas.create_image(x, y, anchor='nw', image=self.get_image(path))

    def draw(self, type, args, kwargs):
        options = {'fill': 'white'}
        options.update(kwargs)
        getattr(self.canvas, f'create_{type}')(*args, **options)

    def draw_text(self, text, x, y, font, size, bold, italic, kwargs):
        options = {'fill': 'white'}
        options.update(kwargs)
        self.canvas.create_text(x, y, text=text, font=self.get_font(font, size, bold, italic), **options)

    def get_font(self, family, size, bold, italic):
        weight = 'normal'
        if bold:
            weight = 'bold'
        slant = 'roman'
        if italic:
            slant = 'italic'
        name = f'font-{family}-{size}-{weight}-{slant}'
        if name not in self.assets:
            self.assets[name] = Font(family=family, size=size, weight=weight, slant=slant)
        return self.assets[name]

    def get_image(self, path):
        if path not in self.assets:
            check_image_format(path)
            self.assets[path] = tk.PhotoImage(file=path)
        return self.assets[path]

    def say(self, message, done):
        messagebox.showinfo(self.title(), message, parent=self)
        done.put(True)

    def input(self, prompt, response):
        response.put(simpledialog.askstring(self.title(), prompt, parent=self))

    def with_window(self, func, args):
        func(self, *args)

def check_image_format(path):
    "Produce a warning message if the image format is not supported"
    ext = path[-4:].lower()
    supported = (".gif", ".ppm", ".pgm", ".pbm")
    if ext not in supported:
        print(f"{path}: Warning: image format {ext} is not supported and may not work properly on some platforms (Windows/Mac/Linux).")
        print(f"Please use one of: {supported}.")

def check_audio_format(path):
    "Produce a warning message if the audio format is not supported"
    ext = path[-4:].lower()
    if ext != ".wav":
        print(f"{path}: Warning: audio format {ext} is not supported and may not work properly on some platforms (Windows/Mac/Linux).")
        print(f"Please use WAV.")

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
                                    '\n    ' + errorBuffer.value.decode(getfilesystemencoding(), 'ignore'))
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

    def play_sound(sound):
        """
        Play a sound located at the given path.

        Example:
            ```
            gamelib.play_sound('sound/jump.wav')
            ```

        Note:
            The only sound format that is supported accross all platforms (Windows/Mac/Linux)
            is WAV.
        """

        check_audio_format(sound)
        if system == 'Windows':
            _playsoundWin(sound)
        elif system == 'Darwin':
            _playsoundOSX(sound)
        else:
            _playsoundNix(sound)

    return play_sound

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
        except Exception as e:
            sys.excepthook(*sys.exc_info())
        finally:
            self.send_command_to_tk('close', notify=True)

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
        """
        Wait until the next `Event`: a key is pressed/released, the mouse is moved, etc,
        and return it.

        This function is normally used in combination with `gamelib.is_alive`,
        in turn-based games.

        Args:
            event_type: If an `EventType` is passed, the function will ignore any
                        events that are not of this type. (It will still return `None`
                        when the game is closed).

        Returns:
            An `Event`, or `None` if the user closed the game window.

        Example:
            ```
            while gamelib.is_alive():
                event = gamelib.wait(gamelib.EventType.KeyPress):
                gamelib.say(f'You pressed {event.key}')
            ```
        """
        self.notify_tk()
        if not _TkWindow.instance:
            return None
        while True:
            event = _GameThread.events.get()
            if not event or not event_type or event.type == event_type:
                return event

    def get_events(self):
        """
        Get the list of `Event`s that happened since the last call to `get_events`.

        This function is normally used in combination with `loop`, in action games.

        Example:
            ```
            while gamelib.loop(fps=30):
                # this is executed 30 times per second
                for event in gamelib.get_events():
                    if event.type == gamelib.EventType.KeyPress and event.key == 'q':
                        return
            ```
        """
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
        """Set the window title to `s`."""
        self.send_command_to_tk('title', s)

    def icon(self, path):
        """
        Set the window icon to the image located at `path`.

        Example:
            ```
            gamelib.icon('images/icon.gif')
            ```

        Note:
            The only image formats that are supported accross all platforms (Windows/Mac/Linux)
            are GIF and PPM/PGM/PBM.
        """
        self.send_command_to_tk('icon', path)

    def draw_begin(self):
        """
        Clear the window.

        Any call to `draw_*` should be between `draw_begin` and `draw_end`.

        Example:
            ```
            gamelib.draw_begin()
            gamelib.draw_rectangle(0, 0, 10, 10, fill='red')
            gamelib.draw_end()
            ```
        """
        _TkWindow.idle.wait()
        self.send_command_to_tk('clear')

    def draw_image(self, path, x, y):
        """
        Draw an image located at `path` in the coordinates `x, y`.

        Example:
            ```
            gamelib.draw_image('images/player.gif', 10, 10)
            ```

        Note:
            The only image formats that are supported accross all platforms (Windows/Mac/Linux)
            are GIF and PPM/PGM/PBM.
        """
        self.send_command_to_tk('draw_image', path, x, y)

    def draw_text(self, text, x, y, font=None, size=12, bold=False, italic=False, **options):
        """
        Draw some `text` at coordinates `x, y` with the given properties.

        Args:
            text: The text to draw.
            x:    The screen coordinates for the text.
            y:    The screen coordinates for the text.
            font: Font family name (eg: `'Helvetica'`). **Note:** the only font guaranteed to be
                  available in all systems is the default font. If the selected font is not found,
                  the default font will be used instead.
            size: Size of the text.
            bold: Whether or not to use bold weight.
            italic: Whether or not to use italic slant.

        Some of the supported extra options are:

        * `fill`: Fill color. It can be named colors like `'red'`, `'white'`, etc,
          or a specific color in `'#rrggbb'` hexadecimal format.
        * `anchor`: Where to place the text relative to the given position.
          It may be any combination of `n` (North), `s` (South), `e`
          (East), `w` (West) and `c` (center). Default is `c`.

        To see all supported options, see the documentation for
        [`tkinter.Canvas.create_text`](https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/create_text.html).

        Example:
            ```
            gamelib.draw_text('Hello world!', 10, 10, fill='red', anchor='nw')
            ```
        """
        self.send_command_to_tk('draw_text', text, x, y, font, size, bold, italic, options)

    def draw_arc(self, x1, y1, x2, y2, **options):
        """
        Draw an arc, pieslice, or chord in the bounding box between points `x1, y1` and
        `x2, y2`.

        To see all supported options, see the documentation for
        [`tkinter.Canvas.create_arc`](https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/create_arc.html).

        Example:
            ```
            gamelib.draw_arc(10, 10, 20, 20, outline='white', fill='red')
            ```
        """
        self.send_command_to_tk('draw', 'arc', [x1, y1, x2, y2], options)

    def draw_line(self, x1, y1, x2, y2, **options):
        """
        Draw a straight line between points `x1, y1` and `x2, y2`.

        To see all supported options, see the documentation for
        [`tkinter.Canvas.create_line`](https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/create_line.html).

        Example:
            ```
            gamelib.draw_line(10, 10, 30, 20, fill='blue', width=2)
            ```
        """
        self.send_command_to_tk('draw', 'line', [x1, y1, x2, y2], options)

    def draw_oval(self, x1, y1, x2, y2, **options):
        """
        Draw an ellipse in the bounding box between points `x1, y1` and `x2, y2`.

        To see all supported options, see the documentation for
        [`tkinter.Canvas.create_oval`](https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/create_oval.html).

        Example:
            ```
            gamelib.draw_oval(10, 10, 30, 20, outline='white', fill='red')
            ```
        """
        self.send_command_to_tk('draw', 'oval', [x1, y1, x2, y2], options)

    def draw_polygon(self, points, **options):
        """
        Draw a polygon with vertices in the given `points` coordinates list. The list must have
        an even amount of numbers; each pair determines a vertex. The last vertex is automatically
        joined with the first one with a segment.

        To see all supported options, see the documentation for
        [`tkinter.Canvas.create_polygon`](https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/create_polygon.html).

        Example:
            ```
            gamelib.draw_polygon([10, 10, 30, 20, 0, 40], outline='white', fill='red')
            ```
        """
        self.send_command_to_tk('draw', 'polygon', points, options)

    def draw_rectangle(self, x1, y1, x2, y2, **options):
        """
        Draw an rectangle in the bounding box between points `x1, y1` and `x2, y2`.

        To see all supported options, see the documentation for
        [`tkinter.Canvas.create_rectangle`](https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/create_rectangle.html).

        Example:
            ```
            gamelib.draw_rectangle(10, 10, 30, 20, outline='white', fill='red')
            ```
        """
        self.send_command_to_tk('draw', 'rectangle', [x1, y1, x2, y2], options)

    def draw_end(self):
        """
        Refresh the window.

        Any call to `draw_*` should be between `draw_begin` and `draw_end`.

        Example:
            ```
            gamelib.draw_begin()
            gamelib.draw_rectangle(0, 0, 10, 10, fill='red')
            gamelib.draw_end()
            ```
        """
        self.send_command_to_tk('update', notify=True)

    def resize(self, w, h):
        """Resize the window to be `w` pixels wide and `h` pixels tall."""
        self.send_command_to_tk('resize', w, h)

    def say(self, message):
        """Present the user with the given `message` in a dialog box with an OK button."""
        done = Queue()
        self.send_command_to_tk('say', message, done, notify=True)
        done.get()

    def input(self, prompt):
        """
        Ask the user to enter a text value.

        Args:
            prompt: A message to display.

        Returns:
            A string containing the value that the user typed. `None` if the user
            clicked on Cancel instead of OK.
        """
        response = Queue()
        self.send_command_to_tk('input', prompt, response, notify=True)
        return response.get()

    def is_alive(self):
        """
        Returns True if the game window is open.

        Example:
            ```
            while gamelib.is_alive():
                event = gamelib.wait(gamelib.EventType.KeyPress):
                gamelib.say(f'You pressed {event.key}')
            ```
        """
        self.wait_for_tk()
        return bool(_TkWindow.instance)

    _last_loop_time = None

    def loop(self, fps=30):
        """
        When used in a `while` loop, the body will be executed `fps` times per second.

        Returns:
            `True` if the game window is still open, `False` otherwise.

        Example:
            ```
            while gamelib.loop(fps=30):
                # this is executed 30 times per second
                for event in gamelib.get_events():
                    if event.type == gamelib.EventType.KeyPress and event.key == 'q':
                        return
            ```
        """
        frame_duration = 1.0 / fps
        a = _GameThread._last_loop_time
        b = time.time()
        if a:
            time.sleep(max(0, frame_duration - (b - a)))
        _GameThread._last_loop_time = time.time()
        return self.is_alive()

_GameThread.instance = _GameThread()

wait = _GameThread.instance.wait
get_events = _GameThread.instance.get_events
title = _GameThread.instance.title
icon = _GameThread.instance.icon
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
play_sound = _audio_init()

def _sigint_handler(sig, frame):
    w = _TkWindow.instance
    if w:
        w.close()
    else:
        raise KeyboardInterrupt()

def init(game_main, args=None):
    """
    Initialize gamelib.

    Args:
        game_main: Your `main` function.
        args: List of arguments to be passed to the `main` function, or `None`.
    """
    _GameThread.instance.start(game_main, args or [])

    # block until wait(), get_events(), etc called on game thread.
    # This prevents rendering the window before the user has a chance to configure it.
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
        os._exit(0)

class EventType(Enum):
    "An enumeration of the different types of `Event`s supported by gamelib."

    KeyPress = 'KeyPress'
    "The user pressed a key."
    KeyRelease = 'KeyRelease'
    "The user released a key."
    Motion = 'Motion'
    "The user moved the mouse over the window."
    ButtonPress = 'ButtonPress'
    "The user pressed a mouse button."
    ButtonRelease = 'ButtonRelease'
    "The user released a mouse button."

class Event:
    """
    Represents an event generated by the user.

    Attributes:
        type: An `EventType`.
        key: A key that has been pressed/released.
        mouse_button: 0, 1 or 2 for left, right and middle mouse buttons respectively.
        x: The current mouse horizontal position, in pixels.
        y: The current mouse vertical position, in pixels.

    This is actually a wrapper for the
    [Tkinter Event class](https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/event-handlers.html).
    Any of the `tk.Event` attributes can be accessed through this object.

    ## See also

    `wait`, `get_events`
    """

    def __init__(self, tkevent):
        self.tkevent = tkevent

    def __getattr__(self, k):
        if k == 'type': return EventType[self.tkevent.type.name]
        if k == 'key': return self.tkevent.keysym
        if k == 'mouse_button': return self.tkevent.num
        return getattr(self.tkevent, k)

    def __repr__(self):
        return repr(self.tkevent)

if __name__ == '__main__':
    def interactive_main(_locals):
        import code
        code.interact(local=_locals)

    init(interactive_main, args=[locals()])

# Gamelib

Gamelib is a pure-Python single-file library/framework for writing simple games. It is
intended for educational purposes (e.g. to be used in basic programming courses).

Here is a "hello world" example:

```python
import gamelib

def main():
    gamelib.resize(300, 300)

    gamelib.draw_begin()
    gamelib.draw_text('Hello world!', 150, 150)
    gamelib.draw_end()

    # wait until the user presses any key
    gamelib.wait(gamelib.EventType.KeyPress)

gamelib.init(main)
```

And this example shows a rectangle moving around the screen:

```python
import gamelib

def main():
    gamelib.resize(300, 300)

    x, y = 150, 80
    dx, dy = 5, 5

    while gamelib.loop(fps=30):
        for event in gamelib.get_events():
            if event.type == gamelib.EventType.KeyPress and event.key == 'q':
                return

        gamelib.draw_begin()
        gamelib.draw_rectangle(x-10, y-10, x+10, y+10, fill='red')
        gamelib.draw_end()

        x += dx
        y += dy
        if x > 300 or x < 0:
            dx *= -1
        if y > 300 or y < 0:
            dy *= -1

gamelib.init(main)
```

## Goals

* **Easy to learn:** Writing a simple game should be almost as easy as writing console
  programs. It should not require knowledge about inheritance, components, double-buffering,
  color channels, blitting or actors.
* **Simple, basic API:** Support drawing stuff and maybe playing sounds, nothing more.
* **Portable** Support Windows / Mac OS / Linux desktop.
* **Easy to install:** See [relevant XKCD](https://xkcd.com/1987/). `gamelib.py` should
  not depend on anything that's not available in a fresh Python installation.
  That rules out `pip`.

## Installation

Just [download](https://raw.githubusercontent.com/dessaya/python-gamelib/master/gamelib.py)
`gamelib.py` and place it alongside your project :)

## Documentation

First, look into the provided examples!

* [Hello world](https://github.com/dessaya/python-gamelib/blob/master/example-01-hello-world.py)
* [Bouncing square](https://github.com/dessaya/python-gamelib/blob/master/example-02-bounce.py)
* [Game of Life](https://github.com/dessaya/python-gamelib/blob/master/example-03-life.py)
* [Pong](https://github.com/dessaya/python-gamelib/blob/master/example-04-pong.py)

Gamelib library reference: https://dessaya.github.io/python-gamelib/

To generate the HTML documentation:

```
$ pip3 install pdoc3
$ bash docs/generate.sh
```

## Run the examples

```
$ python3 example-01-hello-world.py
```

## Limitations

* Very limited drawing API (based on [Tkinter Canvas](https://effbot.org/tkinterbook/canvas.htm)).
    * Don't expect to be able to draw thousands of elements at 60 FPS.
    * The only image formats that are supported accross all platforms are GIF and PPM/PGM/PBM.
* Very limited sound API (just a single function: `play_sound()`, based on
  [playsound](https://github.com/TaylorSMarks/playsound)).
    * The only sound format supported accross all platforms is probably WAV.
* Very limited GUI API (just two functions: `say()` and `input()`).
* Supports only a single window.
* No joystick support.

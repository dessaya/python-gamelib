# Gamelib

Gamelib is a pure-Python single-file library/framework for writing simple games. It is
intended for educational purposes (e.g. to be used in basic programming courses).

Here is a "hello world" example:

```python
import gamelib

def main():
    gamelib.resize(300, 300)

    gamelib.draw_begin()
    gamelib.draw_text('Hello world!', 0, 0)
    gamelib.draw_end()

    # wait until the user closes the window
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

    for _ in gamelib.loop(fps=30):
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

# Goals

* **Easy to learn:** Writing games should be almost as simple as writing console
  programs. It should not require knowledge about OOP, double-buffering, color channels,
  blitting or actors.
* **Simple, basic API:** Support drawing stuff and maybe playing sounds, nothing more.
* **Portable** Support Windows / Mac OS / Linux desktop.
* **Easy to install:** See [relevant XKCD](https://xkcd.com/1987/). It should
  not require installing anything else after a fresh Python installation.
  That rules out `pip`.

# Installation

Just download `gamelib.py` and place it alongside your project :)

# Documentation

```
>>> import gamelib
>>> help(gamelib)
```

Also look at the examples.

# Run the examples

```
$ python3 example-01-hello-world.py
```

# Acknowledgements

* Sound support is stolen from https://github.com/TaylorSMarks/playsound

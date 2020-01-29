# Gamelib

Gamelib is a pure-Python single-file library/framework for writing simple games. It is
intended for educational purposes (e.g. to be used in basic programming courses).

Here is a "hello world" that shows a rectangle moving around the screen:

```python
import gamelib

def main():
    gamelib.resize(300, 300)

    x, y = 150, 80
    dx, dy = 5, 5

    for _ in gamelib.loop(fps=30):
        for event in gamelib.get_events():
            if event.type == 'KeyPress' and event.key == 'q':
                return

        gamelib.draw_begin()
        gamelib.draw('rectangle', x-10, y-10, x+10, y+10, fill='red')
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

* **Easy to install:** See [relevant XKCD](https://xkcd.com/1987/).
* **Easy to learn:** Writing games should be almost as simple as writing console
  programs. It should not require knowledge about OOP, double-buffering, color channels,
  blitting or actors.
* **Portable** Support Windows / Mac OS / Linux desktop.
* **Simple, basic API:** Support drawing stuff and maybe playing sounds, nothing more.

# Installation

Just download `gamelib.py` and place it alongside your project :)

# Run the examples

```
$ python3 example-01-bounce.py
```

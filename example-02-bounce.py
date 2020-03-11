"""
This example shows a rectangle moving around the window.
"""

import gamelib

def main():
    gamelib.resize(300, 300)

    x, y = 150, 80
    dx, dy = 5, 5

    while gamelib.loop():
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

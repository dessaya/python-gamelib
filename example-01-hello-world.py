"""
This example simply shows a message until the user presses a key.
"""

import gamelib

def main():
    gamelib.resize(300, 300)

    gamelib.draw_begin()
    gamelib.draw_text('Hello world!', 150, 150)
    gamelib.draw_end()

    gamelib.wait(gamelib.EventType.KeyPress)

gamelib.init(main)

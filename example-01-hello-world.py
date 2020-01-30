import gamelib

def main():
    gamelib.resize(300, 300)

    gamelib.draw_begin()
    gamelib.draw_text('Hello world!', 0, 0)
    gamelib.draw_end()

    gamelib.wait(gamelib.EventType.KeyPress)

gamelib.init(main)

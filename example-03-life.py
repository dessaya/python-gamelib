"""
An implementation of Conway's Game of Life.
"""

import gamelib

# size in pixels of a single cell
CELL_SIZE = 10

def life_create(map):
    life = []
    for r in map:
        row = []
        for c in r:
            row.append(c == '#')
        life.append(row)
    return life

def neighbors(life, r, c):
    amount = 0
    for dr, dc in (
        (-1, -1),
        (0, -1),
        (1, -1),
        (-1, 0),
        (1, 0),
        (-1, 1),
        (0, 1),
        (1, 1),
    ):
        nf = (r + dr) % len(life)
        cell = life[nf][(c + dc) % len(life[nf])]
        if cell:
            amount += 1
    return amount

def cell_next(life, r, c):
    cell = life[r][c]
    n = neighbors(life, r, c)
    if not cell:
        # reproduction
        return n == 3
    if n < 2:
        # death by solitude
        return False
    if n in (2, 3):
        # happy case
        return True
    # death by overpopulation
    return False

def life_next(life):
    life_new = []
    for r in range(len(life)):
        row = []
        for c in range(len(life[0])):
            row.append(cell_next(life, r, c))
        life_new.append(row)
    return life_new

def draw(life):
    gamelib.draw_begin()
    for y, row in enumerate(life):
        for x, cell in enumerate(row):
            if cell:
                gamelib.draw_rectangle(
                    x * CELL_SIZE,
                    y * CELL_SIZE,
                    x * CELL_SIZE + CELL_SIZE,
                    y * CELL_SIZE + CELL_SIZE,
                    fill='white',
                )
    gamelib.draw_end()

def main():
    gamelib.title("Game of life")
    life = life_create([
        '..........',
        '..........',
        '..........',
        '.....#....',
        '......#...',
        '....###...',
        '..........',
        '..........',
    ])
    gamelib.resize(len(life[0]) * CELL_SIZE, len(life) * CELL_SIZE)
    while gamelib.is_alive():
        draw(life)
        gamelib.wait(gamelib.EventType.KeyPress)
        life = life_next(life)

gamelib.init(main)

"""
The game Pong!
Keys:
    Left player:  Q/A
    Right player: Up/Down arrow keys
"""

import gamelib
from collections import namedtuple
import random

SIZE = 300, 300

PADDLE1 = 0
PADDLE2 = 1

PADDLE_GAP = 10
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 60

BALL_RADIUS = 5

FPS = 30
VELOCITY = 150 / FPS

State = namedtuple('State', ['paddles', 'ball_pos', 'ball_vel', 'score'])

def move_paddle(state, p, dy):
    W, H = SIZE
    paddles = list(state.paddles)
    y = paddles[p]
    y += dy * VELOCITY * 1.5
    if y < 0: y = 0
    if y > H: y = H
    paddles[p] = y
    return state._replace(paddles=tuple(paddles))

def paddle_collision(state, p):
    W, H = SIZE
    bx, by = state.ball_pos

    py = state.paddles[p]
    px = PADDLE_GAP if p == 0 else H - PADDLE_GAP

    if abs(bx - px) > PADDLE_WIDTH / 2 + BALL_RADIUS: return False
    if abs(by - py) > PADDLE_HEIGHT / 2 + BALL_RADIUS: return False
    return True

def move_ball(state):
    W, H = SIZE
    x, y = state.ball_pos
    vx, vy = state.ball_vel

    x = x + vx * VELOCITY
    y = y + vy * VELOCITY

    if y < BALL_RADIUS or y > H - BALL_RADIUS:
        vy = -vy

    if (
        (vx < 0 and paddle_collision(state, PADDLE1)) or
        (vx > 0 and paddle_collision(state, PADDLE2))
    ):
        vx = -vx
        vy += 2 * (random.random() - 0.5)

    return state._replace(ball_pos=(x, y), ball_vel=(vx, vy))

def draw_paddle(state, p):
    W, H = SIZE
    x = PADDLE_GAP if p == 0 else H - PADDLE_GAP
    y = state.paddles[p]
    gamelib.draw_rectangle(
        x - PADDLE_WIDTH / 2,
        y - PADDLE_HEIGHT / 2,
        x + PADDLE_WIDTH / 2,
        y + PADDLE_HEIGHT / 2,
        fill='white',
    )

def draw_ball(state):
    x, y = state.ball_pos
    gamelib.draw_oval(
        x - BALL_RADIUS,
        y - BALL_RADIUS,
        x + BALL_RADIUS,
        y + BALL_RADIUS,
        fill='white',
    )

def random_ball_velocity():
    vx, vy = 1 if random.random() > 0.5 else -1, random.random()
    norm = (vx * vx + vy * vy) ** 0.5
    return vx / norm, vy / norm

def check_goal(state):
    W, H = SIZE
    x, y = state.ball_pos
    vx, vy = state.ball_vel
    score1, score2 = state.score

    if vx > 0 and x > W:
        return state._replace(
            ball_pos=(W / 2, H / 2),
            ball_vel=random_ball_velocity(),
            score=(score1 + 1, score2),
        )
    if vx < 0 and x < 0:
        return state._replace(
            ball_pos=(W / 2, H / 2),
            ball_vel=random_ball_velocity(),
            score=(score1, score2 + 1),
        )
    return state

def draw_score(state):
    W, H = SIZE
    score1, score2 = state.score
    gamelib.draw_text(f"{score1} - {score2}", W / 2, 10, anchor='n', fill='white')


def main():
    gamelib.title("Pong")

    W, H = SIZE
    gamelib.resize(W, H)

    state = State(
        paddles=(H / 2, H / 2),
        ball_pos=(W / 2, H / 2),
        ball_vel=random_ball_velocity(),
        score=(0, 0),
    )

    key_pressed = {}

    while gamelib.loop():
        gamelib.draw_begin()
        draw_paddle(state, PADDLE1)
        draw_paddle(state, PADDLE2)
        draw_ball(state)
        draw_score(state)
        gamelib.draw_end()

        for event in gamelib.get_events():
            if event.type == gamelib.EventType.KeyPress:
                key_pressed[event.key] = True
            if event.type == gamelib.EventType.KeyRelease:
                key_pressed[event.key] = False

        if key_pressed.get('q', False):    state = move_paddle(state, PADDLE1, -1)
        if key_pressed.get('a', False):    state = move_paddle(state, PADDLE1, +1)
        if key_pressed.get('Up', False):   state = move_paddle(state, PADDLE2, -1)
        if key_pressed.get('Down', False): state = move_paddle(state, PADDLE2, +1)

        state = move_ball(state)
        state = check_goal(state)

gamelib.init(main)

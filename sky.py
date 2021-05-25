import time
import curses
import asyncio
import curses
import random
from statistics import median

from curses_tools import draw_frame, get_frame_size, read_controls
from physics import update_speed
from obstacles import Obstacle, show_obstacles

TIC_TIMEOUT = 0.1

FRAME_1_PATH = 'frames/rocket_frame_1.txt'
FRAME_2_PATH = 'frames/rocket_frame_2.txt'
TRASH_PATH = 'frames/trash_large.txt'
SPEED = 3 #сколько символов перепрыгивает корабль за одно нажатие
starship_row, starship_column = 0, 0
TRASH_FRAME_PATHS = [
    'frames/duck.txt',
    'frames/hubble.txt',
    'frames/lamp.txt',
    'frames/trash_large.txt',
    'frames/trash_small.txt',
    'frames/trash_xl.txt'
    ]

#obstacles = []

async def fire(canvas, start_row, start_column, rows_speed=-0.3*SPEED, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""
    global obstacles, obstacles_in_last_collisions
    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        for obstacle in obstacles:
            if obstacle.has_collision(round(row), round(column)):
                obstacles_in_last_collisions.append(obstacle)
                return

        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(random.randint(10, 40))

        canvas.addstr(row, column, symbol)
        await sleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)


async def animate_ship(canvas, frame1, frame2):
    previous_row, previous_column = 1, 1
    while True:

        draw_frame(canvas, previous_row, previous_column, frame2, negative=True)
        draw_frame(canvas, starship_row, starship_column, frame1)
        previous_row, previous_column = starship_row, starship_column #запоминаем кадр для стирания в следующем фрейме
        await sleep()

        draw_frame(canvas, previous_row, previous_column, frame1, negative=True)
        draw_frame(canvas, starship_row, starship_column, frame2)
        previous_row, previous_column = starship_row, starship_column
        await sleep()


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    global obstacles, obstacles_in_last_collisions
    rows_number, columns_number = canvas.getmaxyx()
    frame_rows, frame_columns = get_frame_size(garbage_frame)

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 1

    obstacle = Obstacle(row, column, frame_rows, frame_columns)
    obstacles.append(obstacle)

    try:
        while row < rows_number:
            draw_frame(canvas, row, column, garbage_frame)
            await asyncio.sleep(0)
            draw_frame(canvas, row, column, garbage_frame, negative=True)
            if obstacle in obstacles_in_last_collisions:
                obstacles_in_last_collisions.remove(obstacle)
                return

            row += speed
            obstacle.row = row
    finally:
        obstacles.remove(obstacle)

    #await sleep()


async def fill_orbit_with_garbage(canvas, window_rows, window_columns, trash_frames):
    while True:
        await sleep(random.randint(10, 50))
        column = random.randint(1, window_columns - 2) # цифры - поправка на рамку
        frame = random.choice(trash_frames)
        coroutine = fly_garbage(canvas, column, frame)
        coroutines.append(coroutine)


async def control(canvas, window_rows, window_columns, frame_rows, frame_columns):
    global starship_row, starship_column
    #вычисляем правую и нижнию границу один раз при условии что размеры окна не меняются во время работы
    max_allowed_row = window_rows-frame_rows-1
    max_allowed_column = window_columns-frame_columns-1
    row_speed = column_speed = 0

    while True:
        rows_direction, columns_direction, space_pressed = read_controls(canvas)

        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)
        new_row = starship_row + row_speed * SPEED
        new_column = starship_column + column_speed * SPEED

        # new_row = starship_row + rows_direction * SPEED
        # new_column = starship_column + columns_direction * SPEED

        starship_row = median([1, new_row, max_allowed_row])
        starship_column = median([1, new_column, max_allowed_column])

        if space_pressed:
            coroutine = fire(canvas, starship_row, starship_column + frame_columns//2) #середина коробля
            coroutines.append(coroutine)

        await asyncio.sleep(0)
        #await sleep()


async def sleep(tics=1):
    for i in range(tics):
        await asyncio.sleep(0)


def draw(canvas):
    global starship_row, starship_column, coroutines
    global obstacles, obstacles_in_last_collisions
    window_rows, window_columns = curses.window.getmaxyx(canvas)
    curses.curs_set(False)
    canvas.nodelay(True)
    canvas.border()
    obstacles = []
    obstacles_in_last_collisions = []

    #инициализация корабля
    with open(FRAME_1_PATH, 'r') as my_file:
        frame1 = my_file.read()
    with open(FRAME_2_PATH, 'r') as my_file:
        frame2 = my_file.read()

    frame_rows, frame_columns = get_frame_size(frame1)
    starship_row = window_rows//2 - frame_rows//2 #середина экрана с поправкой на размер фрейма корабля
    starship_column = window_columns//2 - frame_columns//2

    trash_frames = []
    for path in TRASH_FRAME_PATHS:
        with open(path, "r") as garbage_file:
            frame = garbage_file.read()
            trash_frames.append(frame)

    coroutines = []
    for coroutine in [
            animate_ship(canvas, frame1, frame2),
            control(canvas, window_rows, window_columns, frame_rows, frame_columns),
            fire(canvas, starship_row, window_columns // 2),  # середина экрана с поправкой на высоту фрейма корабля
            fill_orbit_with_garbage(canvas, window_rows, window_columns, trash_frames),
            show_obstacles(canvas, obstacles)
            ]:
        coroutines.append(coroutine)

    # инициализация звёзд
    for i in range(100):
        row = random.randint(1, window_rows - 2) # цифры - поправка на рамку
        column = random.randint(1, window_columns - 2)
        symbol = random.choice(['+', '*', '.', ':'])
        coroutine = blink(canvas, row, column, symbol)
        coroutines.append(coroutine)

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        if len(coroutines) == 0:
            break
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
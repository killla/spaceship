import time
import curses
import asyncio
import curses
import random
from statistics import median


TIC_TIMEOUT = 0.1
SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258
FRAME_1_PATH = 'frames/rocket_frame_1.txt'
FRAME_2_PATH = 'frames/rocket_frame_2.txt'
SPEED = 5 #сколько символов перепрыгивает корабль за одно нажатие
starship_row, starship_column = 0, 0


def read_controls(canvas):
    """Read keys pressed and returns tuple witl controls state."""

    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 1

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -1

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True

    return rows_direction, columns_direction, space_pressed


def draw_frame(canvas, start_row, start_column, text, negative=False):
    """Draw multiline text fragment on canvas, erase text instead of drawing if negative=True is specified."""

    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue

        if row >= rows_number:
            break

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue

            if column >= columns_number:
                break

            if symbol == ' ':
                continue

            # Check that current position it is not in a lower right corner of the window
            # Curses will raise exception in that case. Don`t ask why…
            # https://docs.python.org/3/library/curses.html#curses.window.addch
            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


def get_frame_size(text):
    """Calculate size of multiline text fragment, return pair — number of rows and colums."""

    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


async def fire(canvas, start_row, start_column, rows_speed=-0.3*SPEED, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

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
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for i in range(random.randint(10, 40)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for i in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for i in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for i in range(3):
            await asyncio.sleep(0)


async def animate_ship(canvas, frame1, frame2):
    previous_row, previous_column = 1, 1
    while True:

        draw_frame(canvas, previous_row, previous_column, frame2, negative=True)
        draw_frame(canvas, starship_row, starship_column, frame1)
        previous_row, previous_column = starship_row, starship_column #запоминаем кадр для стирания в следующем фрейме
        for i in range(1):
            await asyncio.sleep(0)

        draw_frame(canvas, previous_row, previous_column, frame1, negative=True)
        draw_frame(canvas, starship_row, starship_column, frame2)
        previous_row, previous_column = starship_row, starship_column
        for i in range(1):
            await asyncio.sleep(0)


async def control(canvas, window_rows, window_columns, frame_rows, frame_columns):
    global starship_row, starship_column
    #вычисляем правую и нижнию границу один раз при условии что размеры окна не меняются во время работы
    max_allowed_row = window_rows-frame_rows-1
    max_allowed_column = window_columns-frame_columns-1
    while True:
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        new_row = starship_row + rows_direction * SPEED
        new_column = starship_column + columns_direction * SPEED

        starship_row = median([1, new_row, max_allowed_row])
        starship_column = median([1, new_column, max_allowed_column])

        await asyncio.sleep(0)


def draw(canvas):
    global starship_row, starship_column
    window_rows, window_columns = curses.window.getmaxyx(canvas)
    curses.curs_set(False)
    canvas.nodelay(True)
    canvas.border()

    with open(FRAME_1_PATH, 'r') as my_file:
        frame1 = my_file.read()
    with open(FRAME_2_PATH, 'r') as my_file:
        frame2 = my_file.read()

    frame_rows, frame_columns = get_frame_size(frame1)
    starship_row = window_rows//2 - frame_rows//2 #середина экрана с поправкой на размер фрейма корабля
    starship_column = window_columns//2 - frame_columns//2

    coroutines = []
    for coroutine in [
            animate_ship(canvas, frame1, frame2),
            control(canvas, window_rows, window_columns, frame_rows, frame_columns),
            fire(canvas, starship_row, window_columns // 2)  # середина экрана с поправкой на высоту фрейма корабля
            ]:
        coroutines.append(coroutine)
    # звезды
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
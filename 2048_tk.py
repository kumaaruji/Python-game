

# import tkinter as tk
import random
import sys
from functools import reduce

# -- Functional board helpers (board is tuple of tuples) ----

def empty_board(size):
    """Return an empty board as tuple-of-tuples"""
    return tuple(tuple(0 for _ in range(size)) for _ in range(size))

def board_to_list(board):
    return [list(row) for row in board]

def list_to_board(lst):
    return tuple(tuple(row) for row in lst)

def iter_positions(board):
    n = len(board)
    for r in range(n):
        for c in range(n):
            yield r, c

def get_empty_positions(board):
    return [(r,c) for r,c in iter_positions(board) if board[r][c]==0]

def add_random_tile(board, rnd=random.random):
    empties = get_empty_positions(board)
    if not empties:
        return board, None
    r,c = random.choice(empties)
    value = 4 if rnd() < 0.1 else 2
    lst = board_to_list(board)
    lst[r][c] = value
    return list_to_board(lst), (r,c,value)

# -- Row operations (pure functions) --

def compress_row_left(row):
    """Slide non-zero tiles to left without merging"""
    new = [x for x in row if x!=0]
    new += [0]*(len(row)-len(new))
    return new

def merge_row_left(row):
    """Merge adjacent equal tiles moving left. Return (new_row, score_gained)"""
    row = compress_row_left(row)
    score = 0
    for i in range(len(row)-1):
        if row[i] != 0 and row[i] == row[i+1]:
            row[i] *= 2
            score += row[i]
            row[i+1] = 0
    row = compress_row_left(row)
    return row, score

def move_left(board):
    lst = board_to_list(board)
    total_score = 0
    changed = False
    for i in range(len(lst)):
        newrow, s = merge_row_left(lst[i])
        if newrow != lst[i]:
            changed = True
        lst[i] = newrow
        total_score += s
    return list_to_board(lst), changed, total_score

def rotate_cw(board):
    """Rotate board clockwise"""
    n = len(board)
    lst = [[board[n-1-c][r] for c in range(n)] for r in range(n)]
    return list_to_board(lst)

def rotate_ccw(board):
    n = len(board)
    lst = [[board[c][n-1-r] for c in range(n)] for r in range(n)]
    return list_to_board(lst)

def move_right(board):
    # Mirror, move left, mirror back
    n = len(board)
    lst = [list(reversed(row)) for row in board_to_list(board)]
    temp_board = list_to_board(lst)
    moved_board, changed, s = move_left(temp_board)
    lst = [list(reversed(row)) for row in board_to_list(moved_board)]
    return list_to_board(lst), changed, s

def move_up(board):
    # rotate cw, move left, rotate ccw
    rb = rotate_cw(board)
    moved, changed, s = move_left(rb)
    return rotate_ccw(moved), changed, s

def move_down(board):
    rb = rotate_ccw(board)
    moved, changed, s = move_left(rb)
    return rotate_cw(moved), changed, s

def any_moves_possible(board):
    # if any empty exists -> True
    if get_empty_positions(board):
        return True
    n = len(board)
    for r in range(n):
        for c in range(n-1):
            if board[r][c] == board[r][c+1]:
                return True
    for c in range(n):
        for r in range(n-1):
            if board[r][c] == board[r+1][c]:
                return True
    return False

def reached_goal(board, goal=2048):
    for r,c in iter_positions(board):
        if board[r][c] >= goal:
            return True
    return False

# --- Game state management (pure-ish functions) --

def init_game(size=4, rnd=random.random):
    board = empty_board(size)
    board, _ = add_random_tile(board, rnd)
    board, _ = add_random_tile(board, rnd)
    return board, 0  # board, score

def apply_move(board, direction):
    """
    direction in {'left','right','up','down'}
    returns new_board, moved_flag, score_gained
    """
    if direction == 'left':
        return move_left(board)
    if direction == 'right':
        return move_right(board)
    if direction == 'up':
        return move_up(board)
    if direction == 'down':
        return move_down(board)
    raise ValueError("Invalid direction")

# -- GUI (tkinter) ---

class GameUI:
    TILE_COLORS = {
        0: "#cdc1b4", 2: "#eee4da", 4: "#ede0c8", 8: "#f2b179",
        16: "#f59563", 32: "#f67c5f", 64: "#f65e3b", 128: "#edcf72",
        256: "#edcc61", 512: "#edc850", 1024: "#edc53f", 2048: "#edc22e"
    }
    TILE_FONT = ("Helvetica", 24, "bold")
    def __init__(self, root, size=4, goal=2048):
        self.root = root
        self.size = size
        self.goal = goal
        self.root.title(f"2048 - {size}x{size}")
        self.frame = tk.Frame(root, bg='#bbada0', padx=10, pady=10)
        self.frame.pack()
        self.score = 0
        self.board, _ = init_game(size)
        self.setup_ui()
        self.draw_board()
        root.bind("<Key>", self.on_key)

    def setup_ui(self):
        top = tk.Frame(self.root)
        top.pack(pady=(8,0))
        self.score_label = tk.Label(top, text=f"Score: {self.score}", font=("Helvetica",14,"bold"))
        self.score_label.pack(side=tk.LEFT, padx=10)
        restart_btn = tk.Button(top, text="Restart", command=self.restart)
        restart_btn.pack(side=tk.LEFT, padx=10)
        size_label = tk.Label(top, text=f"Size: {self.size}x{self.size}", font=("Helvetica",12))
        size_label.pack(side=tk.LEFT, padx=10)
        self.canvas = tk.Canvas(self.frame, width=120*self.size, height=120*self.size, bg='#bbada0', highlightthickness=0)
        self.canvas.pack()

    def restart(self):
        self.score = 0
        self.board, _ = init_game(self.size)
        self.draw_board()

    def draw_board(self):
        self.canvas.delete("all")
        cell_size = 120
        padding = 12
        for r in range(self.size):
            for c in range(self.size):
                x0 = c*cell_size + padding
                y0 = r*cell_size + padding
                x1 = x0 + cell_size - 2*padding
                y1 = y0 + cell_size - 2*padding
                v = self.board[r][c]
                color = self.TILE_COLORS.get(v, "#3c3a32")
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=color, width=0, radius=8)
                if v != 0:
                    text = str(v)
                    font = ("Helvetica", 28, "bold") if v < 1024 else ("Helvetica", 20, "bold")
                    self.canvas.create_text((x0+x1)//2, (y0+y1)//2, text=text, font=font)
        self.score_label.config(text=f"Score: {self.score}")
        # check win/lose
        if reached_goal(self.board, self.goal):
            self.popup("You win!", "You reached the goal. Press Restart to play again.")
        elif not any_moves_possible(self.board):
            self.popup("Game over", "No more moves available. Press Restart to try again.")

    def popup(self, title, message):
        top = tk.Toplevel(self.root)
        top.title(title)
        tk.Label(top, text=message, padx=20, pady=10).pack()
        tk.Button(top, text="OK", command=top.destroy).pack(pady=(0,10))
        top.transient(self.root)
        top.grab_set()
        self.root.wait_window(top)

    def on_key(self, event):
        key = event.keysym
        mapping = {
            'Left':'left','Right':'right','Up':'up','Down':'down',
            'a':'left','d':'right','w':'up','s':'down',
            'A':'left','D':'right','W':'up','S':'down'
        }
        direction = mapping.get(key)
        if direction:
            self.perform_move(direction)

    def perform_move(self, direction):
        new_board, changed, gained = apply_move(self.board, direction)
        if not changed:
            return
        self.score += gained
        new_board, added = add_random_tile(new_board)
        self.board = new_board
        self.draw_board()

# -- Utility to allow running as script ---

def main(argv=None):
    argv = argv or sys.argv[1:]
    size = 4
    goal = 2048
    if len(argv) >= 1:
        try:
            size = int(argv[0])
            if size < 2: size = 4
        except:
            size = 4
    root = tk.Tk()
    game = GameUI(root, size=size, goal=goal)
    root.mainloop()

if __name__ == "__main__":
    main()

"""
3D Maze Game using Python Turtle (Raycasting Engine)
Controls: W/A/S/D or Arrow Keys to move, Q to quit
Find the glowing green EXIT door!
"""

import turtle
import math
import time

# ─── MAP ───────────────────────────────────────────────────────────────────────
# E = exit door cell (treated as open floor for movement, special render)
MAP = [
    "####################",
    "#    #    #    #   #",
    "#    #    #    #   #",
    "#       ##     #   #",
    "#    #    #        #",
    "####      #   ###  #",
    "#    ##   #   #    #",
    "#     #       #    #",
    "#     #   ##  #    #",
    "#         #      E##",
    "####################",
]

MAP_W = len(MAP[0])
MAP_H = len(MAP)

EXIT_X, EXIT_Y = 0, 0
for ry in range(MAP_H):
    for rx in range(MAP_W):
        if MAP[ry][rx] == "E":
            EXIT_X, EXIT_Y = rx, ry

EXIT_TRIGGER = 0.9   # how close the player needs to get

# ─── PLAYER ────────────────────────────────────────────────────────────────────
player_x     = 1.5
player_y     = 1.5
player_angle = 0.0
steps        = 0
start_time   = time.time()
won          = False

MOVE_SPEED = 0.07
TURN_SPEED = 0.06

# ─── RENDERER SETTINGS ─────────────────────────────────────────────────────────
SCREEN_W  = 640
SCREEN_H  = 400
NUM_RAYS  = 120
FOV       = math.pi / 3
HALF_FOV  = FOV / 2
MAX_DEPTH = 16
COL_W     = SCREEN_W / NUM_RAYS
HALF_H    = SCREEN_H / 2

# ─── COLOURS ───────────────────────────────────────────────────────────────────
SKY_COLOR   = "#1a0a2e"
FLOOR_COLOR = "#0f2a1a"

def shade(dist):
    brightness = max(0, min(255, int(255 / (1 + dist * dist * 0.3))))
    r = int(brightness * 0.55)
    g = int(brightness * 0.20)
    b = int(brightness * 0.80)
    return f"#{r:02x}{g:02x}{b:02x}"

def shade_exit(dist):
    """Pulsing green glow for the exit door."""
    pulse = 0.75 + 0.25 * math.sin(time.time() * 5)
    brightness = max(0, min(255, int(280 / (1 + dist * dist * 0.25))))
    g = int(brightness * pulse)
    r = int(brightness * 0.05)
    b = int(brightness * 0.30)
    return f"#{r:02x}{g:02x}{b:02x}"

# ─── SCREEN SETUP ──────────────────────────────────────────────────────────────
screen = turtle.Screen()
screen.setup(width=SCREEN_W, height=SCREEN_H)
screen.title("3D Maze — Find the EXIT!")
screen.bgcolor(SKY_COLOR)
screen.tracer(0)

pen = turtle.Turtle(); pen.hideturtle(); pen.speed(0); pen.penup()
hud = turtle.Turtle(); hud.hideturtle(); hud.speed(0); hud.penup()
overlay = turtle.Turtle(); overlay.hideturtle(); overlay.speed(0); overlay.penup()

# ─── INPUT ─────────────────────────────────────────────────────────────────────
keys = {"w": False, "s": False, "a": False, "d": False}

def key_press(k):   keys[k] = True
def key_release(k): keys[k] = False

for k in ("w", "s", "a", "d"):
    screen.onkeypress(lambda k=k: key_press(k), k)
    screen.onkeyrelease(lambda k=k: key_release(k), k)
    screen.onkeypress(lambda k=k: key_press(k), k.upper())
    screen.onkeyrelease(lambda k=k: key_release(k), k.upper())

screen.onkeypress(lambda: key_press("w"),  "Up");    screen.onkeyrelease(lambda: key_release("w"),  "Up")
screen.onkeypress(lambda: key_press("s"),  "Down");  screen.onkeyrelease(lambda: key_release("s"),  "Down")
screen.onkeypress(lambda: key_press("a"),  "Left");  screen.onkeyrelease(lambda: key_release("a"),  "Left")
screen.onkeypress(lambda: key_press("d"),  "Right"); screen.onkeyrelease(lambda: key_release("d"),  "Right")

running = True
def quit_game():
    global running
    running = False
screen.onkeypress(quit_game, "q")
screen.onkeypress(quit_game, "Q")
screen.listen()

# ─── MAP HELPERS ───────────────────────────────────────────────────────────────
def cell_at(x, y):
    ix, iy = int(x), int(y)
    if 0 <= ix < MAP_W and 0 <= iy < MAP_H:
        return MAP[iy][ix]
    return "#"

def is_wall(x, y):
    c = cell_at(x, y)
    return c == "#"

def is_exit_cell(ix, iy):
    return ix == EXIT_X and iy == EXIT_Y

# ─── RAYCASTER ─────────────────────────────────────────────────────────────────
def cast_ray(ox, oy, angle):
    """DDA. Returns (dist, side, hit_exit)."""
    sin_a = math.sin(angle) or 1e-6
    cos_a = math.cos(angle) or 1e-6

    delta_x = abs(1 / cos_a)
    delta_y = abs(1 / sin_a)
    map_x   = int(ox)
    map_y   = int(oy)
    step_x  = 1 if cos_a > 0 else -1
    step_y  = 1 if sin_a > 0 else -1
    side_x  = (map_x + 1 - ox) * delta_x if cos_a > 0 else (ox - map_x) * delta_x
    side_y  = (map_y + 1 - oy) * delta_y if sin_a > 0 else (oy - map_y) * delta_y

    for _ in range(MAX_DEPTH * 4):
        if side_x < side_y:
            side_x += delta_x; map_x += step_x; hit_side = 0
        else:
            side_y += delta_y; map_y += step_y; hit_side = 1

        c = cell_at(map_x, map_y)
        if c == "#":
            dist = (map_x - ox + (1 - step_x)/2) / cos_a if hit_side == 0 \
                   else (map_y - oy + (1 - step_y)/2) / sin_a
            return max(0.01, dist), hit_side, False
        if c == "E":
            dist = (map_x - ox + (1 - step_x)/2) / cos_a if hit_side == 0 \
                   else (map_y - oy + (1 - step_y)/2) / sin_a
            return max(0.01, dist), hit_side, True

    return MAX_DEPTH, 0, False

# ─── DRAW HELPERS ──────────────────────────────────────────────────────────────
def draw_rect(t, x, y, w, h, color):
    t.goto(x, y)
    t.fillcolor(color)
    t.begin_fill()
    t.setheading(0)
    for _ in range(2):
        t.forward(w); t.right(90); t.forward(h); t.right(90)
    t.end_fill()

# ─── RENDER ────────────────────────────────────────────────────────────────────
def render():
    pen.clear()
    pen.pendown()
    draw_rect(pen, -SCREEN_W/2,  SCREEN_H/2, SCREEN_W, SCREEN_H/2, SKY_COLOR)
    draw_rect(pen, -SCREEN_W/2,  0,          SCREEN_W, SCREEN_H/2, FLOOR_COLOR)
    pen.penup()

    angle_step  = FOV / NUM_RAYS
    start_angle = player_angle - HALF_FOV

    for col in range(NUM_RAYS):
        ray_angle = start_angle + col * angle_step
        dist, side, hit_exit = cast_ray(player_x, player_y, ray_angle)
        dist *= math.cos(ray_angle - player_angle)   # fish-eye fix

        wall_h = min(SCREEN_H, SCREEN_H / (dist + 0.001))

        if hit_exit:
            col_color = shade_exit(dist)
            # Draw a glow halo slightly wider/taller
            glow_color = shade_exit(dist + 1.5)
            gx = -SCREEN_W/2 + col * COL_W - 1
            gy = (wall_h + 20) / 2
            draw_rect(pen, gx, gy, COL_W + 3, wall_h + 20, glow_color)
        else:
            col_color = shade(dist)
            if side == 1:
                r = int(col_color[1:3], 16)
                g = int(col_color[3:5], 16)
                b = int(col_color[5:7], 16)
                col_color = f"#{max(0,r-40):02x}{max(0,g-40):02x}{max(0,b-40):02x}"

        x = -SCREEN_W/2 + col * COL_W
        y = wall_h / 2
        draw_rect(pen, x, y, COL_W + 1, wall_h, col_color)

    pen.penup()

# ─── HUD ───────────────────────────────────────────────────────────────────────
def draw_hud():
    hud.clear()
    cell = 8
    ox = -SCREEN_W/2 + 5
    oy =  SCREEN_H/2 - 5

    for row in range(MAP_H):
        for ci in range(MAP_W):
            cx = ox + ci * cell
            cy = oy - row * cell
            ch = MAP[row][ci]
            if ch == "#":
                color = "#553377"
            elif ch == "E":
                pulse = 0.6 + 0.4 * math.sin(time.time() * 5)
                g_val = int(200 * pulse)
                color = f"#00{g_val:02x}44"
            else:
                color = "#111111"
            draw_rect(hud, cx, cy, cell-1, cell-1, color)

    # Player dot
    px = ox + player_x * cell
    py = oy - player_y * cell
    hud.goto(px, py)
    hud.dot(5, "#00ffcc")

    # Timer
    elapsed = int(time.time() - start_time)
    mins, secs = divmod(elapsed, 60)
    hud.goto(-28, SCREEN_H/2 - 18)
    hud.color("#ffffff")
    hud.write(f"{mins:02d}:{secs:02d}", font=("Courier", 13, "bold"))

    # Step counter
    hud.goto(-SCREEN_W/2 + 5, -SCREEN_H/2 + 14)
    hud.color("#aaaaaa")
    hud.write(f"Steps: {steps}   |   W/A/S/D = move   Q = quit",
              font=("Courier", 9, "normal"))

    # Exit hint arrow (compass bearing toward exit)
    dx = (EXIT_X + 0.5) - player_x
    dy = (EXIT_Y + 0.5) - player_y
    bearing = math.atan2(dy, dx) - player_angle
    hud.goto(SCREEN_W/2 - 30, SCREEN_H/2 - 30)
    hud.color("#00ff88")
    hud.setheading(-math.degrees(bearing) + 90)
    hud.pendown(); hud.forward(12); hud.penup()

# ─── WIN SCREEN ────────────────────────────────────────────────────────────────
def draw_win_screen():
    overlay.clear()
    # Dark semi-transparent backdrop
    draw_rect(overlay, -SCREEN_W/2, SCREEN_H/2, SCREEN_W, SCREEN_H, "#050510")

    elapsed = int(time.time() - start_time)
    mins, secs = divmod(elapsed, 60)

    overlay.goto(0, 80)
    overlay.color("#00ff88")
    overlay.write("🎉  YOU ESCAPED!  🎉",
                  align="center", font=("Courier", 26, "bold"))

    overlay.goto(0, 20)
    overlay.color("#ffffff")
    overlay.write(f"Time:  {mins:02d}:{secs:02d}",
                  align="center", font=("Courier", 18, "normal"))

    overlay.goto(0, -20)
    overlay.color("#aaffcc")
    overlay.write(f"Steps: {steps}",
                  align="center", font=("Courier", 18, "normal"))

    overlay.goto(0, -70)
    overlay.color("#555577")
    overlay.write("Press Q to quit",
                  align="center", font=("Courier", 12, "normal"))

    screen.update()

# ─── MOVEMENT ──────────────────────────────────────────────────────────────────
def update_player():
    global player_x, player_y, player_angle, steps

    if keys["a"]: player_angle -= TURN_SPEED
    if keys["d"]: player_angle += TURN_SPEED

    dx = math.cos(player_angle) * MOVE_SPEED
    dy = math.sin(player_angle) * MOVE_SPEED
    moved = False

    if keys["w"]:
        nx, ny = player_x + dx, player_y + dy
        if not is_wall(nx, player_y): player_x = nx; moved = True
        if not is_wall(player_x, ny): player_y = ny; moved = True
    if keys["s"]:
        nx, ny = player_x - dx, player_y - dy
        if not is_wall(nx, player_y): player_x = nx; moved = True
        if not is_wall(player_x, ny): player_y = ny; moved = True

    if moved:
        steps += 1

# ─── CHECK WIN ─────────────────────────────────────────────────────────────────
def check_win():
    dist = math.hypot(player_x - (EXIT_X + 0.5), player_y - (EXIT_Y + 0.5))
    return dist < EXIT_TRIGGER

# ─── MAIN LOOP ─────────────────────────────────────────────────────────────────
last_time = time.time()

while running:
    try:
        screen.update()

        if won:
            draw_win_screen()
            time.sleep(0.05)
            continue

        update_player()

        if check_win():
            won = True
            render()
            draw_hud()
            draw_win_screen()
            continue

        render()
        draw_hud()
        screen.update()

        elapsed = time.time() - last_time
        if elapsed < 1/30:
            time.sleep(1/30 - elapsed)
        last_time = time.time()

    except turtle.Terminator:
        break

try:
    turtle.bye()
except Exception:
    pass

import pygame
import random
import sys
import math

# Initialize Pygame and mixer for sound
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)

# Constants
WIDTH, HEIGHT = 600, 400
CELL_SIZE = 10
GRID_WIDTH = WIDTH // CELL_SIZE
GRID_HEIGHT = HEIGHT // CELL_SIZE
FPS = 10  # initial speed

# Colors (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
DARK_GREEN = (0, 150, 0)
BLUE = (0, 100, 255)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AC Holding Snake Game 0.1")
clock = pygame.time.Clock()

# Fonts
title_font = pygame.font.SysFont("Arial", 28, bold=True)
menu_font = pygame.font.SysFont("Arial", 24)
small_font = pygame.font.SysFont("Arial", 18)
game_over_font = pygame.font.SysFont("Arial", 40, bold=True)

# ----------------------------------------------------------------------
# Famicom-style sound engine (square wave with envelope)
# ----------------------------------------------------------------------
def generate_famicom_tone(frequency, duration, volume=0.3, attack=0.01, decay=0.05):
    """
    Generate a square wave tone with a simple envelope to avoid clicks.
    Returns a pygame.mixer.Sound object.
    """
    sample_rate = pygame.mixer.get_init()[0]
    n_samples = int(sample_rate * duration)
    attack_samples = int(sample_rate * attack)
    decay_samples = int(sample_rate * decay)
    sustain_samples = n_samples - attack_samples - decay_samples
    if sustain_samples < 0:
        # Duration too short, adjust
        attack_samples = n_samples // 2
        decay_samples = n_samples - attack_samples
        sustain_samples = 0

    buffer = bytearray()
    period = int(sample_rate / frequency)
    # Pre‑compute square wave values (1 or -1) for one period
    wave = [1 if i < period // 2 else -1 for i in range(period)]

    for i in range(n_samples):
        # Determine amplitude envelope
        if i < attack_samples:
            env = i / attack_samples  # linear ramp up
        elif i < attack_samples + sustain_samples:
            env = 1.0
        else:
            env = 1.0 - (i - attack_samples - sustain_samples) / decay_samples
        # Square wave value
        val = wave[i % period]
        sample = int(volume * 32767 * env * val)
        # Little‑endian 16‑bit
        buffer.append(sample & 0xFF)
        buffer.append((sample >> 8) & 0xFF)

    return pygame.mixer.Sound(buffer=bytes(buffer))

# Create sounds with Famicom character
beep_sound = generate_famicom_tone(880, 0.1, 0.3)   # high beep
boop_sound = generate_famicom_tone(440, 0.2, 0.3)   # low boop

# ----------------------------------------------------------------------
# Game functions
# ----------------------------------------------------------------------
def draw_grid():
    # Optional grid lines
    pass

def draw_snake(snake):
    for segment in snake:
        rect = pygame.Rect(segment[0], segment[1], CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, DARK_GREEN, rect)
        pygame.draw.rect(screen, GREEN, rect, 1)

def draw_food(food):
    rect = pygame.Rect(food[0], food[1], CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(screen, RED, rect)

def show_score(score):
    score_text = small_font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

def show_game_over(score, win=False):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    if win:
        game_over_text = game_over_font.render("YOU WIN!", True, YELLOW)
    else:
        game_over_text = game_over_font.render("GAME OVER", True, RED)

    score_text = small_font.render(f"Final Score: {score}", True, WHITE)
    restart_text = small_font.render("Press SPACE to play again  |  ESC to menu", True, WHITE)

    text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
    score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))

    screen.blit(game_over_text, text_rect)
    screen.blit(score_text, score_rect)
    screen.blit(restart_text, restart_rect)

def random_food(snake):
    """Return a free cell for food, or None if the grid is full."""
    free_cells = []
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            pos = (x * CELL_SIZE, y * CELL_SIZE)
            if pos not in snake:
                free_cells.append(pos)
    if not free_cells:
        return None
    return random.choice(free_cells)

def run_game():
    """Run one game session. Returns 'menu' when user wants to go back."""
    start_x = (GRID_WIDTH // 2) * CELL_SIZE
    start_y = (GRID_HEIGHT // 2) * CELL_SIZE
    snake = [(start_x, start_y),
             (start_x - CELL_SIZE, start_y),
             (start_x - 2 * CELL_SIZE, start_y)]
    direction = (CELL_SIZE, 0)
    next_direction = direction
    food = random_food(snake)
    score = 0
    speed = FPS
    game_over = False
    win = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_SPACE:
                        return 'restart'
                    elif event.key == pygame.K_ESCAPE:
                        return 'menu'
                else:
                    if event.key == pygame.K_UP and direction != (0, CELL_SIZE):
                        next_direction = (0, -CELL_SIZE)
                    elif event.key == pygame.K_DOWN and direction != (0, -CELL_SIZE):
                        next_direction = (0, CELL_SIZE)
                    elif event.key == pygame.K_LEFT and direction != (CELL_SIZE, 0):
                        next_direction = (-CELL_SIZE, 0)
                    elif event.key == pygame.K_RIGHT and direction != (-CELL_SIZE, 0):
                        next_direction = (CELL_SIZE, 0)
                    elif event.key == pygame.K_ESCAPE:
                        return 'menu'

        if game_over:
            screen.fill(BLACK)
            show_game_over(score, win)
            pygame.display.update()
            clock.tick(10)
            continue

        if food is None:
            win = True
            game_over = True
            boop_sound.play()
            continue

        direction = next_direction
        head_x, head_y = snake[0]
        new_head = (head_x + direction[0], head_y + direction[1])
        snake.insert(0, new_head)

        if new_head == food:
            beep_sound.play()
            score += 1
            speed = min(20, FPS + score // 3)
            food = random_food(snake)
        else:
            snake.pop()

        if (new_head[0] < 0 or new_head[0] >= WIDTH or
            new_head[1] < 0 or new_head[1] >= HEIGHT):
            game_over = True
            boop_sound.play()
        elif new_head in snake[1:]:
            game_over = True
            boop_sound.play()

        screen.fill(BLACK)
        draw_grid()
        draw_snake(snake)
        if food:
            draw_food(food)
        show_score(score)
        pygame.display.update()
        clock.tick(speed)

# ----------------------------------------------------------------------
# Menu and info screens
# ----------------------------------------------------------------------
def show_info_screen(title, lines):
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 'menu'
                waiting = False

        screen.fill(BLACK)
        title_surf = menu_font.render(title, True, BLUE)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 50))
        screen.blit(title_surf, title_rect)

        y_offset = 120
        for line in lines:
            text = small_font.render(line, True, WHITE)
            text_rect = text.get_rect(center=(WIDTH // 2, y_offset))
            screen.blit(text, text_rect)
            y_offset += 30

        instr = small_font.render("Press any key to return to menu", True, GRAY)
        instr_rect = instr.get_rect(center=(WIDTH // 2, HEIGHT - 40))
        screen.blit(instr, instr_rect)

        pygame.display.update()
        clock.tick(10)

    return 'menu'

def how_to_play():
    lines = [
        "Use ARROW KEYS to move the snake.",
        "Eat the red food to grow and increase score.",
        "Avoid hitting the walls or your own tail.",
        "Each food increases your score by 1.",
        "The snake speeds up slightly every 3 points.",
        "Fill the entire grid to win!"
    ]
    return show_info_screen("HOW TO PLAY", lines)

def help_screen():
    lines = [
        "Press ESC during game to return to menu.",
        "After game over, press SPACE to replay or ESC to menu.",
        "Use arrow keys to navigate the menu."
    ]
    return show_info_screen("HELP", lines)

def credits_screen():
    lines = [
        "AC Holding Snake Game 0.1",
        "Developed by: AC Holding",
        "Sound: Famicom-style square wave",
        "Pygame powered",
        "© 2025 AC Holding"
    ]
    return show_info_screen("CREDITS", lines)

def about_screen():
    lines = [
        "AC Holding Snake Game 0.1",
        "Classic Snake game with retro sound effects.",
        "Version: 0.1",
        "Resolution: 600x400",
        "Inspired by the original Snake game.",
        "Now with win condition!"
    ]
    return show_info_screen("ABOUT", lines)

def main_menu():
    options = [
        "PLAY GAME",
        "HOW TO PLAY",
        "HELP",
        "CREDITS",
        "ABOUT",
        "EXIT GAME"
    ]
    selected = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    return options[selected]
                elif event.key == pygame.K_ESCAPE:
                    return 'quit'

        screen.fill(BLACK)

        title_surf = title_font.render("AC Holding Snake Game 0.1", True, GREEN)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 60))
        screen.blit(title_surf, title_rect)

        for i, opt in enumerate(options):
            color = WHITE if i != selected else RED
            text = menu_font.render(opt, True, color)
            text_rect = text.get_rect(center=(WIDTH // 2, 150 + i * 40))
            screen.blit(text, text_rect)

        pygame.display.update()
        clock.tick(30)

# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    running = True
    while running:
        choice = main_menu()
        if choice == 'quit':
            running = False
        elif choice == "PLAY GAME":
            while True:
                result = run_game()
                if result == 'menu':
                    break
                elif result == 'quit':
                    running = False
                    break
        elif choice == "HOW TO PLAY":
            how_to_play()
        elif choice == "HELP":
            help_screen()
        elif choice == "CREDITS":
            credits_screen()
        elif choice == "ABOUT":
            about_screen()
        elif choice == "EXIT GAME":
            running = False

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()c

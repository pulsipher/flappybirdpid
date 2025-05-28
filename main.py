import pygame
import random
import sys

# === CONFIGURATION ===
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
BIRD_RADIUS = 20
PIPE_WIDTH = 60
GAP_HEIGHT = 150
GRAVITY = 5000
FLAP_STRENGTH = -800
PIPE_SPEED = 6
PIPE_INTERVAL = 1350  # milliseconds
DESIRED_HEIGHT = SCREEN_HEIGHT // 2  # for P controller
KC_MIN = -0.5
KC_MAX = 1
SP_MIN = 0
SP_MAX = 100

# === SETUP ===
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird - Manual or P-Controller")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 60)

# === CLASSES ===
class Bird:
    def __init__(self):
        self.x = 100
        self.y = SCREEN_HEIGHT // 2
        self.vel = 0
        self.image = pygame.image.load("bird.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (40, 40))  # adjust as needed
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self, dt, flap=False):
        if flap:
            self.vel = FLAP_STRENGTH
        self.y += self.vel * dt + 0.5 * GRAVITY * dt * dt
        self.vel += GRAVITY * dt

    def draw(self):
        screen.blit(self.image, (self.x - self.width // 2, self.y - self.height // 2))

    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

class Pipe:
    def __init__(self):
        self.x = SCREEN_WIDTH
        self.gap_y = random.randint(100, SCREEN_HEIGHT - 200)

    def update(self):
        self.x -= PIPE_SPEED

    def draw(self):
        pygame.draw.rect(screen, (0, 255, 0), (self.x, 0, PIPE_WIDTH, self.gap_y))
        pygame.draw.rect(screen, (0, 255, 0), (self.x, self.gap_y + GAP_HEIGHT, PIPE_WIDTH, SCREEN_HEIGHT))

    def get_rects(self):
        top_rect = pygame.Rect(self.x, 0, PIPE_WIDTH, self.gap_y)
        bottom_rect = pygame.Rect(self.x, self.gap_y + GAP_HEIGHT, PIPE_WIDTH, SCREEN_HEIGHT)
        return top_rect, bottom_rect

# === GAME OVER SCREEN ===
def show_game_over(score):
    while True:
        screen.fill((0, 0, 0))
        game_over_text = big_font.render("Game Over", True, (255, 0, 0))
        score_text = font.render(f"Final Score: {score}", True, (255, 255, 255))
        restart_text = font.render("Press [r] to Restart", True, (200, 200, 200))
        menu_text = font.render("Press [m] for Main Menu", True, (200, 200, 200))
        quit_text = font.render("Press [q] to Quit", True, (200, 200, 200))
        screen.blit(game_over_text, (100, 180))
        screen.blit(score_text, (120, 260))
        screen.blit(restart_text, (60, 320))
        screen.blit(menu_text, (60, 380))
        screen.blit(quit_text, (60, 440))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True  # restart
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_m:
                    return False
                
def slider(screen, rect, val, min_val, max_val, name):
    knob_radius = 8
    pygame.draw.rect(screen, (180, 180, 180), rect)  # slider bar

    # Map KC to knob x position
    knob_x = rect.x + int((val - min_val) / (max_val - min_val) * rect.width)
    knob_y = rect.centery
    pygame.draw.circle(screen, (255, 0, 0), (knob_x, knob_y), knob_radius)

    # Display value
    text = font.render(f"{name}: {val:.2f}", True, (0, 0, 0))
    screen.blit(text, (rect.x, rect.y - 30))

    mouse_down = pygame.mouse.get_pressed()[0]
    if mouse_down:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if rect.collidepoint(mouse_x, mouse_y):
            # Map mouse x back to KC
            relative_x = max(0, min(mouse_x - rect.x, rect.width))
            val = min_val + (relative_x / rect.width) * (max_val - min_val)
    return val

# === MAIN GAME ===
def run_game(control_mode='manual'):
    while True:
        bird = Bird()
        pipes = []
        score = 0
        last_pipe_time = pygame.time.get_ticks()
        running = True
        target_pipe = None

        KC = 0.5  # default gain
        kc_slider_rect = pygame.Rect(20, SCREEN_HEIGHT - 20, 150, 10)
        SP = 45 # default setpoint
        sp_slider_rect = pygame.Rect(200, SCREEN_HEIGHT - 20, 150, 10)

        while running:
            clock.tick(60)
            screen.fill((135, 206, 250))

            # Input
            flap = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            keys = pygame.key.get_pressed()
            if control_mode == 'manual':
                flap = keys[pygame.K_SPACE] or keys[pygame.K_UP]
            elif control_mode == 'p':
                if target_pipe is None or bird.x > target_pipe.x + PIPE_WIDTH * 1.1:
                    target_pipe = next((pipe for pipe in pipes if pipe.x + PIPE_WIDTH > bird.x), None)
                if target_pipe:
                    setpoint = target_pipe.gap_y + GAP_HEIGHT * (1 - SP / 100)
                else:
                    setpoint = DESIRED_HEIGHT
                for x in range(bird.x, SCREEN_WIDTH, 20):
                    pygame.draw.line(screen, (255, 0 , 0), (x, setpoint), (x + 10, setpoint), 1)
                error = -(setpoint - bird.y)
                flap = (KC * error) > 1

            # Update
            dt = clock.tick(60) / 1000  # convert to seconds
            bird.update(dt, flap)
            bird.draw()
        
            current_time = pygame.time.get_ticks()
            if current_time - last_pipe_time > PIPE_INTERVAL:
                pipes.append(Pipe())
                last_pipe_time = current_time

            for pipe in pipes:
                pipe.update()
                pipe.draw()

            # Collision
            bird_rect = bird.get_rect()
            for pipe in pipes:
                top, bottom = pipe.get_rects()
                if bird_rect.colliderect(top) or bird_rect.colliderect(bottom):
                    running = False

            if bird.y < 0 or bird.y > SCREEN_HEIGHT:
                running = False

            # Score
            for pipe in pipes:
                if pipe.x + PIPE_WIDTH < bird.x and not hasattr(pipe, 'scored'):
                    score += 1
                    pipe.scored = True

            score_text = font.render(f"Score: {score}", True, (0, 0, 0))
            screen.blit(score_text, (10, 10))

            # Make slider for Kc if controller is engaged
            if control_mode == 'p':
                KC = slider(screen, kc_slider_rect, KC, KC_MIN, KC_MAX, "Kc")
                SP = slider(screen, sp_slider_rect, SP, SP_MIN, SP_MAX, "SP (%)")

            pygame.display.flip()

        # Show game over and handle restart
        restart = show_game_over(score)
        if not restart:
            break

# === MAIN MENU ===
def main():
    while True:
        screen.fill((0, 0, 0))
        title = font.render("Flappy Bird", True, (255, 255, 255))
        option1 = font.render("Press [m] for Manual Mode", True, (255, 255, 255))
        option2 = font.render("Press [p] for P-Controller Mode", True, (255, 255, 255))
        screen.blit(title, (120, 150))
        screen.blit(option1, (10, 250))
        screen.blit(option2, (10, 300))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    run_game(control_mode='manual')
                elif event.key == pygame.K_p:
                    run_game(control_mode='p')

if __name__ == "__main__":
    main()

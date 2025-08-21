import pygame
import random
import sys
from collections import deque
import webbrowser
import os

pygame.init()

# ---- SOUND (safe init) -------------------------------------------------------
try:
    pygame.mixer.init()
    SOUND_ON = True
except pygame.error:
    SOUND_ON = False

def load_sound(path):
    if not SOUND_ON:
        return None
    try:
        return pygame.mixer.Sound(path)
    except pygame.error:
        return None

def play_sfx(sfx):
    if SOUND_ON and sfx is not None:
        sfx.play()

def play_music(path, loop=-1):
    if SOUND_ON:
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loop)
        except pygame.error:
            pass

def stop_music():
    if SOUND_ON:
        pygame.mixer.music.stop()

# ---- FILE NAMES (make sure these exist in your folder) -----------------------
MUSIC_GAMEPLAY = "suspense_loop.wav"
MUSIC_GAMEOVER = "game_over_bg.wav"

SFX_ORB       = load_sound("orb.wav")
SFX_COLLISION = load_sound("collision.wav")
SFX_GAMEOVER  = load_sound("game_over.wav")

# ---- SCREEN ------------------------------------------------------------------
WIDTH, HEIGHT = 800, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Chase")

# ---- LOAD IMAGES -------------------------------------------------------------
bg_img       = pygame.image.load("spacebg.png")
bg_img       = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))

player_img   = pygame.image.load("spaceship.png")
player_img   = pygame.transform.scale(player_img, (40, 40))

shadow_img   = pygame.image.load("alien.png")
shadow_img   = pygame.transform.scale(shadow_img, (40, 40))

orb_img      = pygame.image.load("fuelcore.png")
orb_img      = pygame.transform.scale(orb_img, (40, 40))

# ---- GAME CONSTANTS ----------------------------------------------------------
PLAYER_SPEED = 5
INITIAL_SHADOW_SPEED = 5
INITIAL_DELAY = 120  # ~2s at 60 FPS

clock = pygame.time.Clock()
FONT = pygame.font.SysFont(None, 36)
BIG  = pygame.font.SysFont(None, 92)


# ---- CLASSES -----------------------------------------------------------------
class Player:
    def __init__(self):
        self.image = player_img
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.trail = deque()

    def move(self, keys):
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and self.rect.left > 0:
            self.rect.x -= PLAYER_SPEED
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.rect.right < WIDTH:
            self.rect.x += PLAYER_SPEED
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and self.rect.top > 0:
            self.rect.y -= PLAYER_SPEED
        if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and self.rect.bottom < HEIGHT:
            self.rect.y += PLAYER_SPEED

    def update_trail(self):
        self.trail.append(self.rect.center)
        if len(self.trail) > 5000:
            self.trail.popleft()

    def draw(self):
        WIN.blit(self.image, self.rect)


class Shadow:
    def __init__(self, trail, delay, speed):
        self.image = shadow_img
        self.trail = trail
        self.delay = delay
        self.index = 0
        self.speed = speed
        self.rect = self.image.get_rect(center=(-100, -100))

    def move(self):
        if len(self.trail) > self.delay:
            target_index = min(self.index, len(self.trail) - self.delay - 1)
            tx, ty = self.trail[target_index]
            dx = tx - self.rect.centerx
            dy = ty - self.rect.centery
            dist = max(1, (dx*dx + dy*dy) ** 0.5)
            self.rect.centerx += int(self.speed * dx / dist)
            self.rect.centery += int(self.speed * dy / dist)
            self.index += 1

    def draw(self):
        WIN.blit(self.image, self.rect)


class Orb:
    def __init__(self):
        self.image = orb_img
        self.rect = self.image.get_rect(
            center=(
                random.randint(20, WIDTH - 20),
                random.randint(20, HEIGHT - 20)
            )
        )
    def draw(self):
        WIN.blit(self.image, self.rect)


# ---- UI ----------------------------------------------------------------------
def draw_center_text(text, font, y, color=(255, 255, 255)):
    surf = font.render(text, True, color)
    WIN.blit(surf, (WIDTH//2 - surf.get_width()//2, y))

def show_start_screen():
    WIN.blit(bg_img, (0, 0))
    draw_center_text("SPACE CHASE", BIG, 60, (255, 50, 50))
    lines = [
        "RULES:",
        "• Move with arrow keys (you are the SPACESHIP).",
        "• RED ALIENS retrace your past path (with a delay).",
        "• Collect glowing FUEL CORES to score and add delay.",
        "• Every 2nd core spawns a new alien shadow.",
        "• Make aliens collide to remove one.",
        "• If any alien hits you → GAME OVER.",
        "",
        "Press SPACE to start"
    ]
    y = 180
    for line in lines:
        draw_center_text(line, FONT, y); y += 36
    pygame.display.update()

def show_countdown(seconds=3):
    for n in range(seconds, 0, -1):
        end_t = pygame.time.get_ticks() + 1000
        play_sfx(SFX_ORB)  # 🔔 Play orb sound each countdown tick
        while pygame.time.get_ticks() < end_t:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
            WIN.blit(bg_img, (0, 0))
            draw_center_text(str(n), BIG, HEIGHT//2 - 60)
            pygame.display.update()
    end_t = pygame.time.get_ticks() + 600
    play_sfx(SFX_ORB)  # 🔔 Play again on "GO!"
    while pygame.time.get_ticks() < end_t:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        WIN.blit(bg_img, (0, 0))
        draw_center_text("GO!", BIG, HEIGHT//2 - 60)
        pygame.display.update()

def show_game_over(score):
    WIN.blit(bg_img, (0, 0))
    draw_center_text("GAME OVER", BIG, 120)
    draw_center_text(f"Final Score: {score}", FONT, 240)
    draw_center_text("Press R to Restart  |  Q to Quit", FONT, 320)
    pygame.display.update()


# ---- GAME LOOP ---------------------------------------------------------------
def game_loop():
    player = Player()
    shadow_speed = INITIAL_SHADOW_SPEED
    shadows = [Shadow(player.trail, INITIAL_DELAY, shadow_speed)]
    orb = Orb()
    score = 0

    while True:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        player.move(keys)
        player.update_trail()

        for sh in shadows:
            sh.move()

        # Player hit
        for sh in shadows:
            if player.rect.colliderect(sh.rect):
                play_sfx(SFX_GAMEOVER)
                return score

        # Shadow vs shadow
        kill_idx = None
        for i in range(len(shadows)):
            for j in range(i+1, len(shadows)):
                if shadows[i].rect.colliderect(shadows[j].rect):
                    kill_idx = j
                    play_sfx(SFX_COLLISION)
                    break
            if kill_idx is not None:
                break
        if kill_idx is not None:
            shadows.pop(kill_idx)

        # Orb pickup
        if player.rect.colliderect(orb.rect):
            score += 1
            orb = Orb()
            play_sfx(SFX_ORB)
            for s in shadows:
                s.delay += 30
            if score % 2 == 0:  # spawn every 2nd orb
                shadow_speed += 0.5
                shadows.append(Shadow(player.trail, INITIAL_DELAY, shadow_speed))

        # Draw
        WIN.blit(bg_img, (0, 0))
        player.draw()
        for sh in shadows:
            sh.draw()
        orb.draw()
        WIN.blit(FONT.render(f"Score: {score}", True, (255, 255, 255)), (10, 10))
        pygame.display.update()


# ---- MAIN --------------------------------------------------------------------
def main():
    while True:
        stop_music()
        show_start_screen()
        waiting = True
        while waiting:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    waiting = False

        show_countdown(3)
        play_music(MUSIC_GAMEPLAY, loop=-1)

        score = game_loop()

        stop_music()
        play_music(MUSIC_GAMEOVER, loop=-1)
        show_game_over(score)

        waiting = True
        while waiting:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        waiting = False
                    elif event.key == pygame.K_q:
                        # Open local feedback form
                        webbrowser.open("file://" + os.path.abspath("index.html"))
                        pygame.quit()
                        sys.exit()

if __name__ == "__main__":
    main()

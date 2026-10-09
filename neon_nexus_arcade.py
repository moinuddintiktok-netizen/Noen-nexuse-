"""
NEON NEXUS: ARCADE OVERDRIVE
Created by Chishti Bro Computers & Developers
Founder: Moinuddin Chishti

Controls:
  A/D or Left/Right : Move paddle
  Mouse              : Move paddle
  Space / Click      : Launch ball
  P / Esc            : Pause
  R                  : Restart run
  M                  : Toggle sound
  F11                : Toggle fullscreen
  Touch              : Drag/tap controls supported

Install: pip install pygame
Run:     python neon_nexus_arcade.py
"""
import math
import random
import sys
import os
import json
from pathlib import Path

import pygame

pygame.init()
try:
    pygame.mixer.init()
    SOUND_OK = True
except pygame.error:
    SOUND_OK = False

WIDTH, HEIGHT = 1100, 760
FPS = 60
TITLE = "NEON NEXUS: ARCADE OVERDRIVE"
SAVE_PATH = Path.home() / ".neon_nexus_arcade.json"

# Palette
BG = (5, 8, 22)
PANEL = (10, 18, 42)
CYAN = (35, 225, 255)
BLUE = (55, 115, 255)
PURPLE = (190, 70, 255)
PINK = (255, 55, 175)
GOLD = (255, 200, 65)
GREEN = (60, 255, 170)
WHITE = (235, 248, 255)
MUTED = (110, 145, 180)
RED = (255, 75, 95)

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

def font(size, bold=False):
    return pygame.font.SysFont("consolas", size, bold=bold)

F_SMALL = font(15, True)
F_MED = font(21, True)
F_BIG = font(38, True)
F_HUGE = font(54, True)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def glow_rect(surface, color, rect, radius=8, strength=2):
    rect = pygame.Rect(rect)
    for i in range(strength, 0, -1):
        alpha_surface = pygame.Surface((rect.w + i * 8, rect.h + i * 8), pygame.SRCALPHA)
        pygame.draw.rect(alpha_surface, (*color, max(8, 20 // i)),
                         alpha_surface.get_rect(), border_radius=radius + i * 2,
                         width=max(1, 2 - i // 2))
        surface.blit(alpha_surface, (rect.x - i * 4, rect.y - i * 4))
    pygame.draw.rect(surface, color, rect, border_radius=radius, width=2)
    inner = rect.inflate(-4, -4)
    if inner.w > 0 and inner.h > 0:
        pygame.draw.rect(surface, (*color,), inner, border_radius=max(2, radius - 2), width=1)

def draw_text(surface, text, fnt, color, pos, center=False, shadow=True):
    img = fnt.render(str(text), True, color)
    rect = img.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    if shadow:
        sh = fnt.render(str(text), True, (0, 20, 45))
        surface.blit(sh, rect.move(2, 3))
    surface.blit(img, rect)
    return rect

class Particle:
    def __init__(self, x, y, color, burst=1.0):
        self.x, self.y = x, y
        a = random.random() * math.tau
        sp = random.uniform(55, 260) * burst
        self.vx, self.vy = math.cos(a) * sp, math.sin(a) * sp
        self.life = self.max_life = random.uniform(.25, .7)
        self.r = random.randint(2, 5)
        self.color = color

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= .985
        self.vy = self.vy * .985 + 30 * dt

    def draw(self, surf):
        if self.life <= 0:
            return
        radius = max(1, int(self.r * self.life / self.max_life))
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), radius)

class FloatingText:
    def __init__(self, x, y, text, color=WHITE):
        self.x, self.y, self.text, self.color = x, y, text, color
        self.life = 1.0

    def update(self, dt):
        self.life -= dt
        self.y -= 38 * dt

    def draw(self, surf):
        if self.life > 0:
            img = F_MED.render(self.text, True, self.color)
            img.set_alpha(int(255 * min(1, self.life * 2)))
            surf.blit(img, img.get_rect(center=(int(self.x), int(self.y))))

class Paddle:
    def __init__(self):
        self.w = 135
        self.h = 17
        self.x = WIDTH / 2
        self.y = HEIGHT - 68
        self.speed = 620
        self.wide_timer = 0
        self.sticky_timer = 0
        self.laser_timer = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y), self.w, self.h)

    def update(self, dt, keys, mouse_x=None):
        if self.wide_timer > 0:
            self.wide_timer -= dt
        if self.sticky_timer > 0:
            self.sticky_timer -= dt
        if self.laser_timer > 0:
            self.laser_timer -= dt
        target = None
        if mouse_x is not None:
            target = mouse_x
        else:
            direction = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
            self.x += direction * self.speed * dt
        if target is not None:
            self.x += (target - self.x) * min(1, dt * 16)
        self.w = 190 if self.wide_timer > 0 else 135
        self.x = clamp(self.x, self.w / 2 + 18, WIDTH - self.w / 2 - 18)

    def draw(self, surf):
        r = self.rect
        color = GOLD if self.sticky_timer > 0 else CYAN
        glow_rect(surf, color, r, 9, 3)
        pygame.draw.line(surf, WHITE, (r.left + 16, r.top + 4), (r.right - 16, r.top + 4), 2)
        if self.laser_timer > 0:
            for x in (r.left + 12, r.right - 12):
                pygame.draw.circle(surf, PINK, (x, r.top), 5)

class Ball:
    def __init__(self, x, y, vx=0, vy=0, attached=False):
        self.x, self.y = float(x), float(y)
        self.radius = 8
        self.vx, self.vy = float(vx), float(vy)
        self.attached = attached
        self.trail = []
        self.sticky_hold = False

    def launch(self, speed=390):
        angle = random.uniform(-.65, .65)
        self.vx = math.sin(angle) * speed
        self.vy = -math.cos(angle) * speed
        self.attached = False
        self.sticky_hold = False

    def draw(self, surf):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(140 * (i + 1) / max(1, len(self.trail)))
            rad = max(1, int(self.radius * (i + 1) / max(1, len(self.trail)) * .65))
            pygame.draw.circle(surf, (35, 120, 255), (int(tx), int(ty)), rad)
        pygame.draw.circle(surf, (*CYAN,), (int(self.x), int(self.y)), self.radius + 5, 1)
        pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, CYAN, (int(self.x - 2), int(self.y - 2)), 3)

class Brick:
    def __init__(self, x, y, w, h, hp, color, kind="normal"):
        self.rect = pygame.Rect(x, y, w, h)
        self.hp = hp
        self.max_hp = hp
        self.color = color
        self.kind = kind
        self.flash = 0

    def hit(self):
        self.hp -= 1
        self.flash = .12
        return self.hp <= 0

    def draw(self, surf):
        if self.flash > 0:
            color = WHITE
            self.flash -= 1 / FPS
        else:
            color = self.color
        glow_rect(surf, color, self.rect, 6, 1)
        inner = self.rect.inflate(-8, -7)
        if inner.w > 0 and inner.h > 0:
            pygame.draw.rect(surf, tuple(min(255, c // 3) for c in color), inner, border_radius=4)
        if self.hp > 1:
            for i in range(self.hp):
                pygame.draw.circle(surf, WHITE, (self.rect.right - 10 - i * 8, self.rect.top + 7), 2)

class PowerUp:
    TYPES = ["wide", "multiball", "laser", "slow", "life", "shield", "sticky"]
    COLORS = {
        "wide": GOLD, "multiball": PURPLE, "laser": PINK, "slow": CYAN,
        "life": GREEN, "shield": BLUE, "sticky": GOLD
    }
    LABELS = {
        "wide": "W", "multiball": "3", "laser": "L", "slow": "S",
        "life": "+", "shield": "D", "sticky": "T"
    }

    def __init__(self, x, y, kind=None):
        self.x, self.y = x, y
        self.kind = kind or random.choice(self.TYPES)
        self.rect = pygame.Rect(int(x - 13), int(y - 13), 26, 26)
        self.speed = 155

    def update(self, dt):
        self.y += self.speed * dt
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, surf):
        c = self.COLORS[self.kind]
        pygame.draw.rect(surf, c, self.rect, border_radius=7, width=2)
        pygame.draw.rect(surf, (20, 25, 55), self.rect.inflate(-6, -6), border_radius=4)
        draw_text(surf, self.LABELS[self.kind], F_SMALL, c, self.rect.center, center=True)

class Game:
    def __init__(self):
        self.best = self.load_best()
        self.fullscreen = False
        self.sound = True
        self.reset()

    def load_best(self):
        try:
            return int(json.loads(SAVE_PATH.read_text()).get("best", 0))
        except Exception:
            return 0

    def save_best(self):
        try:
            SAVE_PATH.write_text(json.dumps({"best": self.best}))
        except Exception:
            pass

    def reset(self):
        self.score = 0
        self.lives = 3
        self.level = 1
        self.combo = 0
        self.max_combo = 0
        self.bricks_broken = 0
        self.powerups_collected = 0
        self.paddle = Paddle()
        self.balls = [Ball(WIDTH / 2, HEIGHT - 91, attached=True)]
        self.bricks = []
        self.powerups = []
        self.particles = []
        self.texts = []
        self.bolts = []
        self.shield_timer = 0
        self.slow_timer = 0
        self.screen_state = "menu"
        self.level_banner = 1.6
        self.shake = 0
        self.stars = [(random.randrange(WIDTH), random.randrange(HEIGHT), random.choice([1, 1, 2])) for _ in range(95)]
        self.make_level()

    def make_level(self):
        self.bricks.clear()
        cols = 10
        gap = 7
        margin = 58
        bw = (WIDTH - margin * 2 - gap * (cols - 1)) // cols
        bh = 27
        rows = min(5 + (self.level - 1) // 2, 8)
        palette = [CYAN, BLUE, PURPLE, PINK, GOLD, GREEN]
        pattern = self.level % 4
        for row in range(rows):
            for col in range(cols):
                if pattern == 1 and (row + col) % 7 == 0:
                    continue
                if pattern == 2 and (col < row // 2 or col >= cols - row // 2):
                    continue
                if pattern == 3 and (row + col) % 5 == 0:
                    hp = 2
                else:
                    hp = 1 + (1 if self.level >= 4 and row < 2 and random.random() < .28 else 0)
                kind = "normal"
                if random.random() < min(.08 + self.level * .01, .18):
                    kind = "power"
                color = palette[(row + self.level - 1) % len(palette)]
                x = margin + col * (bw + gap)
                y = 104 + row * (bh + gap)
                self.bricks.append(Brick(x, y, bw, bh, hp, color, kind))
        self.level_banner = 1.6
        if not self.balls:
            self.balls = [Ball(self.paddle.x, self.paddle.y - 15, attached=True)]

    def new_ball(self, x, y, speed=410):
        angle = random.uniform(-.9, .9)
        self.balls.append(Ball(x, y, math.sin(angle) * speed, -abs(math.cos(angle) * speed)))

    def burst(self, x, y, color, count=12, power=1.0):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, power))

    def popup(self, x, y, msg, color=WHITE):
        self.texts.append(FloatingText(x, y, msg, color))

    def apply_power(self, kind):
        self.powerups_collected += 1
        p = self.paddle
        if kind == "wide":
            p.wide_timer = 12
            self.popup(p.x, p.y - 25, "PADDLE OVERDRIVE!", GOLD)
        elif kind == "multiball":
            originals = [b for b in self.balls if not b.attached]
            if not originals:
                originals = self.balls[:1]
            for b in originals[:3]:
                self.new_ball(b.x, b.y, max(320, math.hypot(b.vx, b.vy)))
            self.popup(p.x, p.y - 25, "MULTIBALL!", PURPLE)
        elif kind == "laser":
            p.laser_timer = 10
            self.popup(p.x, p.y - 25, "LASER PADDLE!", PINK)
        elif kind == "slow":
            self.slow_timer = 8
            self.popup(p.x, p.y - 25, "TIME DILATION", CYAN)
        elif kind == "life":
            self.lives = min(9, self.lives + 1)
            self.popup(p.x, p.y - 25, "+1 LIFE", GREEN)
        elif kind == "shield":
            self.shield_timer = 10
            self.popup(p.x, p.y - 25, "NEXUS SHIELD", BLUE)
        elif kind == "sticky":
            p.sticky_timer = 9
            self.popup(p.x, p.y - 25, "STICKY CATCH", GOLD)

    def launch_all(self):
        launched = False
        for b in self.balls:
            if b.attached:
                b.launch(390 + self.level * 12)
                launched = True
        if launched:
            self.screen_state = "playing"

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

    def handle_events(self):
        mouse_x = None
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.save_best()
                pygame.quit()
                sys.exit()
            if e.type == pygame.VIDEORESIZE and not self.fullscreen:
                # Game keeps a logical 1100x760 canvas and scales to window.
                pass
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_F11:
                    self.toggle_fullscreen()
                elif e.key == pygame.K_m:
                    self.sound = not self.sound
                elif e.key in (pygame.K_p, pygame.K_ESCAPE):
                    if self.screen_state == "playing":
                        self.screen_state = "paused"
                    elif self.screen_state == "paused":
                        self.screen_state = "playing"
                    elif self.screen_state in ("gameover", "victory"):
                        self.reset()
                        self.screen_state = "playing"
                elif e.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if self.screen_state == "menu":
                        self.screen_state = "playing"
                        self.launch_all()
                    elif self.screen_state in ("gameover", "victory"):
                        self.reset()
                        self.screen_state = "playing"
                        self.launch_all()
                    elif self.screen_state == "paused":
                        self.screen_state = "playing"
                    else:
                        self.launch_all()
                elif e.key == pygame.K_r:
                    self.reset()
                    self.screen_state = "playing"
                elif e.key == pygame.K_F1:
                    self.screen_state = "menu"
            if e.type == pygame.MOUSEMOTION:
                mouse_x = e.pos[0] * WIDTH / max(1, screen.get_width())
            if e.type == pygame.MOUSEBUTTONDOWN:
                mx = e.pos[0] * WIDTH / max(1, screen.get_width())
                if self.screen_state == "menu":
                    self.screen_state = "playing"
                    self.launch_all()
                elif self.screen_state in ("gameover", "victory"):
                    self.reset()
                    self.screen_state = "playing"
                    self.launch_all()
                elif self.screen_state == "paused":
                    self.screen_state = "playing"
                else:
                    self.launch_all()
                    mouse_x = mx
            if e.type == pygame.FINGERDOWN:
                mouse_x = e.x * WIDTH
                if self.screen_state == "menu":
                    self.screen_state = "playing"
                    self.launch_all()
                else:
                    self.launch_all()
            if e.type == pygame.FINGERMOTION:
                mouse_x = e.x * WIDTH
        return mouse_x

    def update(self, dt, mouse_x):
        keys = pygame.key.get_pressed()
        if self.screen_state != "playing":
            for p in self.particles:
                p.update(dt)
            self.particles = [p for p in self.particles if p.life > 0]
            for t in self.texts:
                t.update(dt)
            self.texts = [t for t in self.texts if t.life > 0]
            return

        self.paddle.update(dt, keys, mouse_x)
        if self.shield_timer > 0:
            self.shield_timer -= dt
        if self.slow_timer > 0:
            self.slow_timer -= dt
        if self.level_banner > 0:
            self.level_banner -= dt
        if self.shake > 0:
            self.shake -= dt

        for b in self.balls[:]:
            if b.attached:
                b.x = self.paddle.x
                b.y = self.paddle.y - 15
                continue
            b.trail.append((b.x, b.y))
            if len(b.trail) > 8:
                b.trail.pop(0)
            slow = .72 if self.slow_timer > 0 else 1.0
            b.x += b.vx * dt * slow
            b.y += b.vy * dt * slow

            if b.x - b.radius < 18:
                b.x = 18 + b.radius
                b.vx = abs(b.vx)
                self.burst(b.x, b.y, CYAN, 4, .35)
            elif b.x + b.radius > WIDTH - 18:
                b.x = WIDTH - 18 - b.radius
                b.vx = -abs(b.vx)
                self.burst(b.x, b.y, CYAN, 4, .35)
            if b.y - b.radius < 75:
                b.y = 75 + b.radius
                b.vy = abs(b.vy)
                self.burst(b.x, b.y, BLUE, 4, .35)

            if b.vy > 0 and b.y + b.radius >= self.paddle.y and b.y - b.radius <= self.paddle.y + self.paddle.h:
                if self.paddle.rect.left <= b.x <= self.paddle.rect.right:
                    b.y = self.paddle.y - b.radius
                    if self.paddle.sticky_timer > 0:
                        b.attached = True
                        b.vx = b.vy = 0
                    else:
                        offset = (b.x - self.paddle.x) / (self.paddle.w / 2)
                        angle = offset * 1.05
                        speed = min(720, max(390, math.hypot(b.vx, b.vy) * 1.025))
                        b.vx = math.sin(angle) * speed
                        b.vy = -abs(math.cos(angle) * speed)
                    self.combo = 0
                    self.burst(b.x, self.paddle.y, CYAN, 7, .45)

            if b.y > HEIGHT + 20:
                if self.shield_timer > 0:
                    b.y = HEIGHT - 100
                    b.vy = -abs(b.vy)
                    self.shield_timer = 0
                    self.popup(b.x, HEIGHT - 115, "SHIELD SAVE!", BLUE)
                else:
                    self.balls.remove(b)

            if self.paddle.laser_timer > 0 and random.random() < dt * 7:
                self.bolts.append([self.paddle.x - self.paddle.w * .34, self.paddle.y, -720])
                self.bolts.append([self.paddle.x + self.paddle.w * .34, self.paddle.y, -720])

            for brick in self.bricks[:]:
                if b in self.balls and brick.rect.collidepoint(int(b.x), int(b.y)):
                    dx = min(abs(b.x - brick.rect.left), abs(brick.rect.right - b.x))
                    dy = min(abs(b.y - brick.rect.top), abs(brick.rect.bottom - b.y))
                    if dx < dy:
                        b.vx *= -1
                    else:
                        b.vy *= -1
                    destroyed = brick.hit()
                    self.burst(b.x, b.y, brick.color, 9 if destroyed else 3, .7)
                    if destroyed:
                        self.bricks.remove(brick)
                        self.combo += 1
                        self.max_combo = max(self.max_combo, self.combo)
                        self.bricks_broken += 1
                        points = 100 * self.level + min(self.combo, 20) * 15
                        self.score += points
                        self.popup(brick.rect.centerx, brick.rect.centery, f"+{points}", GOLD if self.combo >= 3 else WHITE)
                        if self.combo >= 3:
                            self.popup(WIDTH / 2, 83, f"{self.combo}x COMBO!", PINK)
                        if brick.kind == "power" or random.random() < .11:
                            self.powerups.append(PowerUp(brick.rect.centerx, brick.rect.centery))
                    else:
                        self.score += 20
                    self.shake = .08
                    break

        # Laser bolts destroy bricks on contact.
        for bolt in self.bolts[:]:
            bolt[1] += bolt[2] * dt
            if bolt[1] < 75:
                self.bolts.remove(bolt)
                continue
            for brick in self.bricks[:]:
                if brick.rect.collidepoint(int(bolt[0]), int(bolt[1])):
                    if bolt in self.bolts:
                        self.bolts.remove(bolt)
                    if brick.hit():
                        self.bricks.remove(brick)
                        self.score += 100 * self.level
                        self.bricks_broken += 1
                        self.burst(brick.rect.centerx, brick.rect.centery, PINK, 8)
                        if random.random() < .15:
                            self.powerups.append(PowerUp(brick.rect.centerx, brick.rect.centery))
                    break

        for power in self.powerups[:]:
            power.update(dt)
            if power.rect.colliderect(self.paddle.rect):
                self.apply_power(power.kind)
                self.powerups.remove(power)
                self.burst(power.x, power.y, power.COLORS[power.kind], 14)
            elif power.y > HEIGHT + 20:
                self.powerups.remove(power)

        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        for t in self.texts:
            t.update(dt)
        self.texts = [t for t in self.texts if t.life > 0]

        if not self.balls:
            self.lives -= 1
            if self.lives <= 0:
                self.screen_state = "gameover"
                self.best = max(self.best, self.score)
                self.save_best()
            else:
                self.balls = [Ball(self.paddle.x, self.paddle.y - 15, attached=True)]
                self.screen_state = "ready"

        if not self.bricks:
            self.level += 1
            self.score += 500 * self.level
            self.balls = [Ball(self.paddle.x, self.paddle.y - 15, attached=True)]
            self.powerups.clear()
            self.make_level()
            self.screen_state = "ready"

        self.best = max(self.best, self.score)

    def draw_background(self, surf):
        surf.fill(BG)
        for x, y, r in self.stars:
            twinkle = (pygame.time.get_ticks() // 300 + x + y) % 3
            col = (20, 45 + twinkle * 10, 75 + twinkle * 15)
            pygame.draw.circle(surf, col, (x, y), r)
        # Grid / arena rails
        for x in range(20, WIDTH, 44):
            pygame.draw.line(surf, (9, 22, 49), (x, 75), (x, HEIGHT - 20), 1)
        for y in range(90, HEIGHT - 10, 44):
            pygame.draw.line(surf, (9, 22, 49), (18, y), (WIDTH - 18, y), 1)
        pygame.draw.rect(surf, (20, 60, 105), (17, 72, WIDTH - 34, HEIGHT - 91), 2, border_radius=18)
        pygame.draw.line(surf, CYAN, (30, 74), (170, 74), 3)
        pygame.draw.line(surf, PURPLE, (WIDTH - 170, 74), (WIDTH - 30, 74), 3)

    def draw_hud(self, surf):
        draw_text(surf, "NEON NEXUS", F_MED, CYAN, (28, 22))
        draw_text(surf, "ARCADE OVERDRIVE", F_SMALL, PURPLE, (29, 48))
        draw_text(surf, f"SCORE  {self.score:07d}", F_MED, WHITE, (360, 26), center=True)
        draw_text(surf, f"BEST  {self.best:07d}", F_SMALL, GOLD, (360, 51), center=True)
        draw_text(surf, f"LEVEL {self.level:02d}", F_MED, GOLD, (WIDTH - 245, 25))
        draw_text(surf, f"LIVES {'♥ ' * self.lives}", F_SMALL, PINK, (WIDTH - 245, 51))
        if self.combo >= 3:
            draw_text(surf, f"COMBO x{self.combo}", F_SMALL, PINK, (WIDTH / 2, HEIGHT - 28), center=True)
        active = []
        if self.paddle.wide_timer > 0: active.append(f"WIDE {self.paddle.wide_timer:.0f}s")
        if self.paddle.laser_timer > 0: active.append(f"LASER {self.paddle.laser_timer:.0f}s")
        if self.paddle.sticky_timer > 0: active.append(f"STICKY {self.paddle.sticky_timer:.0f}s")
        if self.shield_timer > 0: active.append(f"SHIELD {self.shield_timer:.0f}s")
        if self.slow_timer > 0: active.append(f"SLOW {self.slow_timer:.0f}s")
        if active:
            draw_text(surf, "  |  ".join(active), F_SMALL, GREEN, (WIDTH / 2, 91), center=True)

    def draw_overlay(self, surf, title, lines, accent=CYAN):
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((2, 5, 18, 205))
        surf.blit(shade, (0, 0))
        glow_rect(surf, accent, (WIDTH / 2 - 300, HEIGHT / 2 - 170, 600, 340), 22, 4)
        draw_text(surf, title, F_HUGE, accent, (WIDTH / 2, HEIGHT / 2 - 105), center=True)
        for i, line in enumerate(lines):
            draw_text(surf, line, F_MED if i == 0 else F_SMALL,
                      WHITE if i == 0 else MUTED, (WIDTH / 2, HEIGHT / 2 - 25 + i * 32), center=True)
        draw_text(surf, "CHISHTI BRO COMPUTERS & DEVELOPERS", F_SMALL, GOLD,
                  (WIDTH / 2, HEIGHT / 2 + 135), center=True)

    def draw(self):
        self.draw_background(screen)
        self.draw_hud(screen)
        for brick in self.bricks:
            brick.draw(screen)
        for power in self.powerups:
            power.draw(screen)
        for bolt in self.bolts:
            pygame.draw.line(screen, PINK, (int(bolt[0]), int(bolt[1] + 12)),
                             (int(bolt[0]), int(bolt[1] - 8)), 3)
            pygame.draw.circle(screen, WHITE, (int(bolt[0]), int(bolt[1] - 8)), 3)
        for b in self.balls:
            b.draw(screen)
        self.paddle.draw(screen)
        if self.shield_timer > 0:
            pygame.draw.arc(screen, BLUE, (18, HEIGHT - 60, WIDTH - 36, 55), math.pi, math.tau, 4)
        for p in self.particles:
            p.draw(screen)
        for t in self.texts:
            t.draw(screen)

        if self.screen_state == "menu":
            self.draw_overlay(screen, "NEON NEXUS", [
                "ARCADE OVERDRIVE  //  BREAK THE GRID",
                "Move: A/D or arrows or mouse / touch",
                "Launch: SPACE or tap  •  Pause: P  •  Fullscreen: F11",
                "Power-ups: Multiball, Laser, Wide, Shield, Slow, Sticky, Extra Life",
                "PRESS SPACE OR TAP TO START"
            ], CYAN)
        elif self.screen_state == "paused":
            self.draw_overlay(screen, "PAUSED", ["Take a breath, arcade pilot.", "Press P / SPACE or tap to resume"], GOLD)
        elif self.screen_state == "ready":
            self.draw_overlay(screen, f"LEVEL {self.level}", ["Ball ready — aim your launch!", "Press SPACE or tap to launch"], GREEN)
        elif self.screen_state == "gameover":
            self.draw_overlay(screen, "GAME OVER", [
                f"Final score: {self.score}",
                f"Bricks smashed: {self.bricks_broken}  •  Best combo: x{self.max_combo}",
                "Press SPACE or tap to run it back"
            ], PINK)
        elif self.screen_state == "victory":
            self.draw_overlay(screen, "NEXUS CLEARED", ["Incredible run!", "Press SPACE to play again"], GOLD)

        # Tiny control footer
        draw_text(screen, "A/D or ← → MOVE   •   SPACE LAUNCH   •   P PAUSE   •   M SOUND   •   F11 FULLSCREEN",
                  F_SMALL, (80, 115, 150), (WIDTH / 2, HEIGHT - 12), center=True, shadow=False)

        # Scale logical canvas to actual window for resize support.
        actual = pygame.display.get_surface()
        if actual.get_size() != (WIDTH, HEIGHT):
            scaled = pygame.transform.smoothscale(screen, actual.get_size())
            actual.blit(scaled, (0, 0))
        pygame.display.flip()

    def run(self):
        while True:
            dt = min(clock.tick(FPS) / 1000.0, .033)
            mouse_x = self.handle_events()
            self.update(dt, mouse_x)
            self.draw()

if __name__ == "__main__":
    Game().run()

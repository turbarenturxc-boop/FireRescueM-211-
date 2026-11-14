"""FIRE RESCUE: ENDLESS INFERNO (SF211 OOP) — SINGLE-FILE EDITION

This single main.py includes all game classes. No core/, entities/ or image files.
Install: py -3.14 -m pip install pygame-ce
Play:    py -3.14 main.py
Checks:  py -3.14 main.py --check

Controls: arrows/WASD move; hold SPACE/J spray or rescue; E rescue;
          P pause, Esc return to menu; Enter start; R replay.
High score is stored in endless_highscore.json next to this main.py.
Covers Weeks 10-13: Polymorphism, Abstract Base Class, Observer, State.
"""

import json
import math
import os
import random
import sys
import tempfile
import unittest
from abc import ABC, abstractmethod
from pathlib import Path

# In --check mode we can run on a machine without an active display.
if "--check" in sys.argv:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

try:
    import pygame
except ImportError as exc:
    raise SystemExit(
        "Pygame is missing. Install with: py -3.14 -m pip install pygame-ce"
    ) from exc



# ======================================================================
# CONSTANTS / CONFIG (original: config.py)
# ======================================================================

WIDTH, HEIGHT = 320, 480
SCALE = 2
FPS = 60
COLS, ROWS = 5, 4
ROOM_X = (66, 113, 160, 207, 254)
ROOM_Y = (156, 218, 280, 342)

INK = (16, 20, 42)
WHITE = (246, 239, 217)
GOLD = (255, 215, 103)
ORANGE = (255, 145, 66)
FIRE = (240, 77, 57)
BLUE = (103, 213, 251)
MINT = (114, 238, 180)
BRICK = (141, 75, 80)
DARK = (35, 39, 73)

# Custom Pygame events (Week 12): game logic announces WHAT happened;
# observers decide what to do with the announcement.
FIRE_OUT = pygame.USEREVENT + 1
PERSON_SAVED = pygame.USEREVENT + 2
PLAYER_HIT = pygame.USEREVENT + 3
SURVIVAL_BONUS = pygame.USEREVENT + 4


# ======================================================================
# BASE CLASS: ABC (original: entities/base.py)
# ======================================================================

class GameObject(pygame.sprite.Sprite, ABC):
    """Every concrete sprite must update its behavior and draw its pixels."""

    def __init__(self, size, center):
        super().__init__()
        self.image = pygame.Surface(size, pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=center)

    @abstractmethod
    def update(self, dt):
        """Advance one simulation step. Called by all_sprites.update(dt)."""

    @abstractmethod
    def draw(self):
        """Refresh self.image so that all_sprites.draw(screen) can display it."""


# ======================================================================
# ROOM (original: entities/room.py)
# ======================================================================

class Room(GameObject):
    def __init__(self, col, row):
        self.col = col
        self.row = row
        super().__init__((44, 68), (ROOM_X[col], ROOM_Y[row] - 6))
        self._fire = 0.0
        self.victim = False
        self.rescued = False
        self.rescue_progress = 0.0
        self.clock = 0.0
        self.flash = 0.0
        self.font = pygame.font.SysFont("consolas", 10, bold=True)
        self.draw()

    @property
    def fire(self):
        """Encapsulation: fire intensity must always be between 0 and 1.7."""
        return self._fire

    @fire.setter
    def fire(self, value):
        self._fire = max(0.0, min(1.7, float(value)))

    @property
    def needs_rescue(self):
        return self.victim and not self.rescued

    @property
    def x(self):
        return ROOM_X[self.col]

    @property
    def y(self):
        return ROOM_Y[self.row]

    def ignite(self, strength=0.75):
        self.fire += strength
        self.flash = 0.30

    def add_victim(self):
        self.victim = True
        self.rescued = False
        self.rescue_progress = 0.0

    def spray(self, dt):
        """Return True only when a burning room is completely extinguished."""
        if self.fire <= 0:
            return False
        self.fire -= 1.25 * dt
        if self.fire <= 0.01:
            self.fire = 0
            self.flash = 0.30
            return True
        return False

    def rescue(self, dt):
        """Rescue works only if the person is present and the fire is out."""
        if not self.needs_rescue or self.fire > 0:
            return False
        self.rescue_progress += dt
        if self.rescue_progress >= 0.85:
            self.rescued = True
            self.rescue_progress = 0
            self.flash = 0.40
            return True
        return False

    def update(self, dt):
        self.clock += dt
        self.flash = max(0, self.flash - dt)
        self.draw()

    def draw(self):
        s = self.image
        s.fill((0, 0, 0, 0))
        # Local origin is (room center x-22, room center y-40).
        pygame.draw.rect(s, (67, 40, 55), (5, 15, 35, 46))
        pygame.draw.rect(s, (237, 190, 128), (7, 15, 30, 42))
        pygame.draw.rect(s, (26, 32, 59), (10, 18, 24, 36))
        if self.fire <= 0:
            pygame.draw.rect(s, (54, 98, 120), (12, 21, 20, 30))
            pygame.draw.rect(s, (87, 146, 159), (12, 21, 7, 27))
        else:
            pygame.draw.rect(s, (109, 48, 47), (11, 20, 22, 32))
            for i in range(4):
                x = 12 + 6 * i
                wave = int(math.sin(self.clock * 13 + i * 2) * 3)
                top = 41 - min(10, int(self.fire * 6)) + wave
                pygame.draw.polygon(s, FIRE, [(x, 52), (x+6, 52), (x+3, top)])
                pygame.draw.polygon(s, ORANGE, [(x+2, 51), (x+5, 51), (x+3, top+6)])
            pygame.draw.rect(s, GOLD, (18, 45, 8, 6))
            for k in range(2):
                smoke_y = 20 - int((self.clock*10 + k*9) % 18)
                pygame.draw.rect(s, (83, 83, 101), (17+k*7, smoke_y, 6, 4))
        if self.needs_rescue:
            wave = int(math.sin(self.clock * 9 + self.col) * 3)
            pygame.draw.rect(s, MINT, (16, 40, 14, 13))
            pygame.draw.rect(s, (235, 173, 123), (17, 28, 10, 10))
            pygame.draw.rect(s, DARK, (17, 28, 10, 3))
            pygame.draw.rect(s, INK, (23, 33, 2, 2))
            pygame.draw.line(s, (235, 173, 123), (29, 43), (35, 32+wave), 3)
            tag = self.font.render("HELP!", False, FIRE)
            pygame.draw.rect(s, (247, 239, 204), (7, 1, 30, 12))
            s.blit(tag, tag.get_rect(center=(22, 7)))
        pygame.draw.rect(s, (251, 212, 157), (20, 18, 4, 35))
        pygame.draw.rect(s, (253, 220, 167), (8, 35, 28, 3))
        pygame.draw.rect(s, (89, 49, 59), (5, 56, 35, 5))
        pygame.draw.rect(s, (243, 194, 133), (4, 54, 36, 3))
        if self.flash > 0:
            pygame.draw.rect(s, GOLD, (7, 15, 30, 42), 2)


# ======================================================================
# FIREFIGHTER (original: entities/player.py)
# ======================================================================

class Firefighter(GameObject):
    def __init__(self):
        self.col, self.row = 2, ROWS - 1
        self.x = float(ROOM_X[self.col])
        self.feet_y = float(ROOM_Y[self.row] + 25)
        super().__init__((40, 56), (round(self.x), round(self.feet_y - 19)))
        self._lives = 3
        self.invincible = 1.5
        self.action = False
        self.action_progress = 0.0
        self.clock = 0.0
        self.old_hitbox = self.hitbox
        self.draw()

    @property
    def lives(self):
        return self._lives

    @lives.setter
    def lives(self, value):
        """Encapsulation keeps health between zero and three hearts."""
        self._lives = max(0, min(3, int(value)))

    @property
    def hitbox(self):
        # Tight hitbox around head/body/boots, not the transparent sprite edges.
        return pygame.Rect(round(self.x)-11, round(self.feet_y)-42, 23, 48)

    @property
    def swept_hitbox(self):
        return self.old_hitbox.union(self.hitbox)

    @property
    def arrived(self):
        return (abs(ROOM_X[self.col]-self.x) < 3
                and abs(ROOM_Y[self.row]+25-self.feet_y) < 3)

    def move(self, dc, dr):
        self.col = max(0, min(COLS-1, self.col+dc))
        self.row = max(0, min(ROWS-1, self.row+dr))
        self.action_progress = 0.0

    def take_damage(self):
        if self.invincible > 0:
            return False
        self.lives -= 1
        self.invincible = 2.0
        return True

    def update(self, dt):
        self.old_hitbox = self.hitbox
        self.clock += dt
        self.invincible = max(0, self.invincible - dt)
        speed = min(1, dt*17)
        self.x += (ROOM_X[self.col]-self.x)*speed
        self.feet_y += (ROOM_Y[self.row]+25-self.feet_y)*speed
        self.rect.center = (round(self.x), round(self.feet_y-19))
        self.draw()

    def draw(self):
        s = self.image
        s.fill((0, 0, 0, 0))
        if self.invincible > 0 and int(self.clock * 12) % 2 == 0:
            return
        # Sprite 40x56, feet at local y=49.
        r = pygame.draw.rect
        r(s, (39, 47, 79), (12, 39, 7, 10))
        r(s, (39, 47, 79), (23, 39, 7, 10))
        r(s, GOLD, (12, 46, 7, 3))
        r(s, GOLD, (23, 46, 7, 3))
        r(s, (28, 31, 49), (10, 49, 10, 4))
        r(s, (28, 31, 49), (22, 49, 10, 4))
        r(s, (121, 161, 176), (7, 23, 7, 17))
        r(s, BLUE, (8, 26, 4, 10))
        r(s, (216, 65, 58), (10, 23, 20, 17))
        r(s, GOLD, (10, 30, 20, 4))
        r(s, GOLD, (18, 23, 4, 15))
        r(s, (238, 169, 118), (13, 12, 15, 13))
        r(s, (38, 42, 62), (21, 17, 6, 3))
        r(s, (249, 223, 134), (8, 7, 24, 6))
        r(s, (240, 190, 79), (11, 3, 18, 9))
        r(s, FIRE, (15, 4, 10, 4))
        r(s, (238, 160, 115), (7, 26, 4, 11))
        r(s, (238, 160, 115), (30, 26, 4, 11))
        r(s, (155, 173, 177), (29, 29, 11, 4))
        if self.action:
            for i in range(4):
                r(s, BLUE, (30-i*5, 22-i*3, 3, 3))
        if self.action_progress > 0:
            r(s, (10, 19, 35), (3, 0, 34, 5))
            r(s, BLUE, (4, 1, int(32*self.action_progress), 3))


# ======================================================================
# HAZARDS: DEBRIS / FIREBALL (original: entities/hazards.py)
# ======================================================================

class Hazard(GameObject):
    """Shared collision sweep; subclasses define their own motion and art."""

    def __init__(self, size, x, y):
        super().__init__(size, (round(x), round(y)))
        self.x = float(x)
        self.y = float(y)
        self.old_hitbox = self.hitbox
        self.landed = False

    @property
    def hitbox(self):
        return pygame.Rect(round(self.x)-8, round(self.y)-8, 16, 16)

    @property
    def swept_hitbox(self):
        # Union checks all positions between the old and new positions in a frame.
        return self.old_hitbox.union(self.hitbox)

    def remember_position(self):
        self.old_hitbox = self.hitbox


class Debris(Hazard):
    """A falling chunk of masonry. It can hit the firefighter MID-FALL."""

    def __init__(self, x, speed):
        super().__init__((22, 22), x, 101)
        self.speed = speed
        self.clock = 0.0
        self.draw()

    def update(self, dt):
        self.remember_position()
        self.y += self.speed * dt
        self.clock += dt
        self.rect.center = (round(self.x), round(self.y))
        self.landed = self.y > 435
        self.draw()

    def draw(self):
        s = self.image
        s.fill((0, 0, 0, 0))
        pygame.draw.rect(s, (32, 28, 48), (2, 3, 18, 17))
        pygame.draw.rect(s, (104, 104, 117), (3, 4, 15, 14))
        shift = 1 if math.sin(self.clock*11) >= 0 else -1
        pygame.draw.rect(s, (175, 156, 145), (6+shift, 5, 8, 4))
        pygame.draw.rect(s, (73, 77, 92), (7, 12, 9, 5))
        pygame.draw.rect(s, GOLD, (14, 9, 3, 3))


class Fireball(Hazard):
    """Fire demon's projectile: moves towards one room and sets it on fire."""

    def __init__(self, start_x, target_room, duration=1.5):
        super().__init__((24, 28), start_x, 79)
        self.start_x = start_x
        self.start_y = 79.0
        self.target_room = target_room
        self.duration = max(0.4, duration)
        self.age = 0.0
        self.draw()

    def update(self, dt):
        self.remember_position()
        self.age = min(self.duration, self.age + dt)
        p = self.age/self.duration
        self.x = (self.start_x + (self.target_room.x-self.start_x)*p
                  + math.sin(p*math.pi)*7)
        self.y = (self.start_y + (self.target_room.y+9-self.start_y)*p
                  - math.sin(p*math.pi)*15)
        self.rect.center = (round(self.x), round(self.y))
        self.landed = p >= 1
        self.draw()

    def draw(self):
        s = self.image
        s.fill((0, 0, 0, 0))
        pygame.draw.rect(s, (123, 35, 58), (4, 8, 16, 16))
        pygame.draw.rect(s, FIRE, (5, 5, 14, 19))
        pygame.draw.polygon(s, FIRE, [(9, 8), (12, 0), (15, 8)])
        pygame.draw.polygon(s, ORANGE, [(7, 18), (11, 6), (17, 20)])
        pygame.draw.rect(s, GOLD, (10, 15, 5, 7))


# ======================================================================
# FIRE DEMON (original: entities/demon.py)
# ======================================================================

class FireDemon(GameObject):
    def __init__(self):
        super().__init__((52, 58), (160, 74))
        self.time = 0.0
        self.attack_flash = 0.0
        self.draw()

    @property
    def x(self):
        return self.rect.centerx

    def throw_fire(self, room, threat):
        """Factory Method: create the appropriate projectile for the target."""
        self.attack_flash = 0.35
        duration = max(0.80, 1.65 - 0.075*(threat-1))
        return Fireball(self.x, room, duration)

    def update(self, dt):
        self.time += dt
        self.attack_flash = max(0, self.attack_flash - dt)
        self.rect.center = (round(160+61*math.sin(self.time*1.35)),
                            round(74+2*math.sin(self.time*5)))
        self.draw()

    def draw(self):
        s = self.image
        s.fill((0, 0, 0, 0))
        r = pygame.draw.rect
        r(s, (40, 23, 46), (8, 39, 36, 5))
        r(s, (111, 36, 60), (15, 25, 22, 17))
        r(s, FIRE, (16, 24, 20, 15))
        r(s, ORANGE, (14, 10, 24, 19))
        r(s, FIRE, (15, 2, 6, 14))
        r(s, FIRE, (31, 2, 6, 14))
        r(s, GOLD, (17, 16, 6, 6))
        r(s, GOLD, (29, 16, 6, 6))
        r(s, (27, 23, 48), (20, 18, 3, 3))
        r(s, (27, 23, 48), (30, 18, 3, 3))
        r(s, (61, 25, 48), (22, 28, 8, 3))
        r(s, ORANGE, (12, 32, 7, 8))
        r(s, ORANGE, (34, 30 if self.attack_flash else 33, 8, 8))
        if self.attack_flash:
            r(s, GOLD, (40, 22, 9, 9))


# ======================================================================
# PARTICLE (original: entities/particle.py)
# ======================================================================

class Particle(GameObject):
    def __init__(self, x, y, vx, vy, life, color):
        super().__init__((3, 3), (round(x), round(y)))
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.life = life
        self.color = color
        self.draw()

    def update(self, dt):
        self.x += self.vx*dt
        self.y += self.vy*dt
        self.vy += 45*dt
        self.life -= dt
        self.rect.center = (round(self.x), round(self.y))
        if self.life <= 0:
            self.kill()  # Sprite Groups remove dead particles automatically.
        else:
            self.draw()

    def draw(self):
        self.image.fill(self.color)


# ======================================================================
# CUSTOM EVENTS (original: core/events.py)
# ======================================================================

def announce(event_type, **data):
    """Post a fact to Pygame's event queue, without changing score directly."""
    pygame.event.post(pygame.event.Event(event_type, data))


# ======================================================================
# OBSERVERS: SCORE / NOTICE (original: core/score.py)
# ======================================================================

class ScoreManager:
    """Observer of scoring events; persists the highest score in JSON."""

    def __init__(self, filename=None):
        self.path = Path(filename) if filename else Path(__file__).resolve().parent / "endless_highscore.json"
        self._score = 0
        self._best = self._read_best()

    @property
    def score(self):
        return self._score

    @property
    def best(self):
        return self._best

    def _read_best(self):
        try:
            return max(0, int(json.loads(self.path.read_text(encoding="utf8")).get("best", 0)))
        except (OSError, ValueError, TypeError, AttributeError):
            return 0

    def reset(self):
        self._score = 0

    def save(self):
        try:
            self.path.write_text(json.dumps({"best": self._best}, indent=2), encoding="utf8")
        except OSError:
            pass  # Do not crash when the game folder is read-only.

    def handle_event(self, event):
        if event.type in (FIRE_OUT, PERSON_SAVED, SURVIVAL_BONUS):
            self._score += event.points
            if self._score > self._best:
                self._best = self._score
                self.save()


class NoticeManager:
    """A second Observer: reacts to the SAME events by changing HUD text."""

    def __init__(self):
        self.message = ""
        self.timer = 0.0

    def reset(self):
        self.message, self.timer = "DODGE THE FIRE DEMON!", 2.0

    def update(self, dt):
        self.timer = max(0, self.timer - dt)

    def handle_event(self, event):
        if event.type == FIRE_OUT:
            self.message = "+100 FIRE OUT!"
        elif event.type == PERSON_SAVED:
            self.message = "+250 PERSON RESCUED!"
        elif event.type == PLAYER_HIT:
            self.message = "OUCH! DODGE THE HAZARDS!"
        elif event.type == SURVIVAL_BONUS:
            self.message = "+20 SURVIVAL BONUS!"
        else:
            return
        self.timer = 1.2


# ======================================================================
# PIXEL ART / HUD (original: core/scene.py)
# ======================================================================

def block(screen, color, x, y, w, h):
    pygame.draw.rect(screen, color, (int(x), int(y), max(0, int(w)), max(0, int(h))))


def text(screen, font, content, x, y, color=WHITE, center=False):
    img = font.render(str(content), False, color)
    pos = img.get_rect(center=(x, y)) if center else img.get_rect(topleft=(x, y))
    screen.blit(font.render(str(content), False, INK), pos.move(1, 2))
    screen.blit(img, pos)


def draw_heart(screen, x, y, on):
    pattern = (".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X...")
    for row, line in enumerate(pattern):
        for col, pixel in enumerate(line):
            if pixel == "X":
                block(screen, FIRE if on else (65, 71, 94), x+2*col, y+2*row, 2, 2)


class Scene:
    """Non-interactive background art and HUD used by several game states."""

    def __init__(self):
        self.font_xs = pygame.font.SysFont("consolas", 11, bold=True)
        self.font_sm = pygame.font.SysFont("consolas", 14, bold=True)
        self.font_md = pygame.font.SysFont("consolas", 20, bold=True)
        self.font_lg = pygame.font.SysFont("consolas", 27, bold=True)

    def draw_building(self, s, clock):
        # Night sky and silhouettes.
        for y in range(0, HEIGHT, 8):
            f = y/HEIGHT
            block(s, (int(15+17*f), int(23+12*f), int(51+16*f)), 0, y, WIDTH, 8)
        for i in range(28):
            x, y = (i*97+21) % WIDTH, (i*53+43) % 340
            block(s, (126, 136, 160), x, y, 2 if i%6 == 0 else 1, 2)
        pygame.draw.circle(s, (251, 232, 183), (285, 81), 13)
        pygame.draw.circle(s, (27, 33, 69), (291, 74), 12)
        for i in range(10):
            x, h = i*39-4, 70+(i*41)%95
            block(s, (30, 40, 74), x, HEIGHT-h-22, 32, h+30)
            for yy in range(HEIGHT-h-10, HEIGHT-20, 16):
                for xx in range(x+6, x+28, 12):
                    block(s, (57, 68, 98), xx, yy, 3, 5)
        for i in range(3):
            x = int((i*110+clock*(5+i)) % 430) - 75
            block(s, (63, 65, 86), x, 67+i*27, 45, 7)
        # Street and five-column brick apartment building.
        block(s, (22, 53, 74), 0, 428, WIDTH, 52)
        block(s, GOLD, 0, 432, WIDTH, 4)
        block(s, (15, 22, 42), 29, 106, 262, 326)
        block(s, (99, 49, 65), 34, 110, 252, 320)
        block(s, BRICK, 38, 110, 244, 316)
        block(s, (179, 95, 87), 41, 110, 5, 314)
        block(s, (97, 51, 65), 275, 110, 6, 314)
        for y in range(116, 422, 12):
            block(s, (105, 49, 62), 40, y, 240, 2)
            for x in range(47+(y//12 % 2)*15, 276, 31):
                block(s, (105, 49, 62), x, y+2, 2, 10)
        for x in (49, 91, 138, 185, 231, 272):
            block(s, (194, 119, 98), x, 115, 3, 302)
            block(s, (111, 60, 73), x+3, 115, 2, 302)
        for y in (185, 247, 309, 371):
            block(s, (239, 190, 129), 33, y, 255, 5)
            block(s, (88, 53, 65), 33, y+5, 255, 3)
        block(s, (19, 23, 43), 28, 100, 264, 13)
        block(s, (236, 183, 127), 32, 96, 256, 9)
        block(s, (249, 211, 155), 37, 91, 246, 6)
        block(s, (60, 66, 81), 66, 77, 21, 18)
        block(s, (91, 103, 112), 70, 68, 13, 27)
        block(s, (45, 42, 67), 101, 113, 119, 17)
        text(s, self.font_xs, "EMBER TOWER", 160, 121, GOLD, center=True)
        # Front door (drawn behind room sprites).
        block(s, (60, 46, 67), 132, 381, 56, 50)
        block(s, (244, 185, 126), 130, 380, 60, 6)
        block(s, (35, 44, 78), 139, 389, 42, 37)
        block(s, (76, 143, 157), 141, 391, 18, 33)
        block(s, (76, 143, 157), 162, 391, 17, 33)
        block(s, (255, 212, 148), 159, 389, 3, 36)
        # Stationed fire engine.
        block(s, (40, 37, 52), 206, 421, 89, 7)
        block(s, FIRE, 216, 404, 72, 22)
        block(s, (255, 107, 70), 225, 397, 44, 12)
        block(s, (167, 223, 237), 255, 400, 13, 8)
        block(s, (255, 236, 175), 216, 420, 72, 4)
        for cx in (229, 273):
            pygame.draw.circle(s, (22, 25, 41), (cx, 426), 8)
            pygame.draw.circle(s, (144, 149, 151), (cx, 426), 4)
        block(s, BLUE if int(clock*6)%2 else FIRE, 238, 393, 9, 5)

    def draw_hud(self, screen, play, score, notice):
        block(screen, INK, 0, 0, WIDTH, 55)
        block(screen, (69, 79, 110), 0, 53, WIDTH, 3)
        text(screen, self.font_xs, "SCORE", 10, 4, BLUE)
        text(screen, self.font_md, f"{score.score:06d}", 10, 19)
        text(screen, self.font_xs, "TIME", 133, 4, BLUE)
        secs = int(play.elapsed)
        text(screen, self.font_md, f"{secs//60:02}:{secs%60:02}", 130, 19)
        text(screen, self.font_xs, f"HEAT {play.threat:02}", 224, 4, GOLD)
        for i in range(3):
            draw_heart(screen, 218+i*29, 29, i < play.player.lives)
        block(screen, INK, 0, 449, WIDTH, 31)
        fires = sum(room.fire > 0 for room in play.rooms)
        people = sum(room.needs_rescue for room in play.rooms)
        text(screen, self.font_xs, f"FIRE {fires:02}", 7, 457, ORANGE)
        text(screen, self.font_xs, f"HELP {people:02}", 88, 457, MINT)
        text(screen, self.font_xs, f"BEST {score.best:06}", 181, 457, GOLD)
        if notice.timer > 0:
            block(screen, (31, 36, 66), 30, 57, 260, 19)
            text(screen, self.font_xs, notice.message, 160, 66, GOLD, center=True)

    def draw_overlay(self, screen, title, lines, button):
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((8, 13, 35, 205))
        screen.blit(dim, (0, 0))
        block(screen, (17, 24, 53), 20, 125, 280, 264)
        pygame.draw.rect(screen, BLUE, (20, 125, 280, 264), 3)
        block(screen, FIRE, 25, 130, 270, 5)
        text(screen, self.font_lg, title, 160, 165, GOLD, center=True)
        for i, line in enumerate(lines):
            text(screen, self.font_sm, line, 160, 210+i*23, WHITE, center=True)
        block(screen, (197, 64, 54), 60, 329, 200, 41)
        block(screen, FIRE, 63, 332, 194, 34)
        text(screen, self.font_md, button, 160, 349, WHITE, center=True)


# ======================================================================
# GAME STATES (original: core/states.py)
# ======================================================================

class GameState(ABC):
    """Contract for screens: all states handle events, update and draw."""

    def __init__(self, game):
        self.game = game

    def enter(self):
        pass

    def exit(self):
        pass

    @abstractmethod
    def handle_event(self, event):
        pass

    @abstractmethod
    def update(self, dt):
        pass

    @abstractmethod
    def draw(self, screen):
        pass


class MenuState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.time = 0.0
        self.sprites = pygame.sprite.Group()
        for row in range(ROWS):
            for col in range(COLS):
                room = Room(col, row)
                if (col*3+row) % 5 == 0:
                    room.ignite(1)
                if (col+row*2) % 7 == 0:
                    room.add_victim()
                self.sprites.add(room)
        self.sprites.add(FireDemon())

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.game.change_state(PlayState(self.game))
            elif event.key == pygame.K_ESCAPE:
                self.game.running = False

    def update(self, dt):
        self.time += dt
        self.sprites.update(dt)

    def draw(self, screen):
        self.game.scene.draw_building(screen, self.time)
        self.sprites.draw(screen)
        self.game.scene.draw_overlay(screen, "FIRE RESCUE", [
            "ENDLESS INFERNO / OOP EDITION",
            "FIRE DEMON ATTACKS THE TOWER",
            "MOVE: ARROWS / WASD",
            "HOLD SPACE: WATER / RESCUE",
            "DODGE FIREBALLS AND DEBRIS",
        ], "PRESS ENTER")
        text(screen, self.game.scene.font_xs,
             f"HIGH SCORE  {self.game.score.best:06d}", 160, 411,
             center=True)


class PlayState(GameState):
    """Endless game world. Group.update() dispatches to every different sprite."""

    def __init__(self, game):
        super().__init__(game)
        self.rng = random.Random()
        self.rooms = [Room(c, r) for r in range(ROWS) for c in range(COLS)]
        self.player = Firefighter()
        self.demon = FireDemon()
        self.all_sprites = pygame.sprite.Group(*self.rooms, self.demon, self.player)
        self.players = pygame.sprite.GroupSingle(self.player)
        self.hazards = pygame.sprite.Group()
        self.fireballs = pygame.sprite.Group()
        self.rocks = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.elapsed = 0.0
        self.bonus_timer = 0.0
        self.fireball_timer = 2.6
        self.debris_timer = 2.4
        self.spread_timer = 7.5
        self.victim_timer = 8.5
        self.heat_timer = 0.0
        for room in self.rng.sample(self.rooms, 5):
            room.ignite(self.rng.uniform(.6, 1.1))
        for room in self.rng.sample(self.rooms, 3):
            room.add_victim()

    def enter(self):
        self.game.score.reset()
        self.game.notice.reset()

    @property
    def threat(self):
        """Difficulty increases every 35 seconds; never reaches an end level."""
        return min(10, 1+int(self.elapsed // 35))

    def room_at_player(self):
        return self.rooms[self.player.row*COLS+self.player.col]

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        moves = {
            pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
            pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
            pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
            pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
        }
        if event.key == pygame.K_p:
            self.game.push_state(PauseState(self.game))
        elif event.key == pygame.K_ESCAPE:
            self.game.score.save()
            self.game.change_state(MenuState(self.game))
        elif event.key in moves:
            self.player.move(*moves[event.key])
            self.heat_timer = 0.0

    def _new_hazard(self, hazard, group):
        self.hazards.add(hazard)
        group.add(hazard)
        self.all_sprites.add(hazard)

    def _scatter(self, x, y, color, count=10):
        for _ in range(count):
            p = Particle(x, y, self.rng.uniform(-60, 60),
                         self.rng.uniform(-80, -10),
                         self.rng.uniform(.2, .6), color)
            self.particles.add(p)
            self.all_sprites.add(p)
        # Avoid an endlessly growing number of particles.
        if len(self.particles) > 130:
            for p in self.particles.sprites()[:len(self.particles)-130]:
                p.kill()

    def _spawn_fireball(self):
        col = self.player.col if self.rng.random() < .46 else self.rng.randrange(COLS)
        row = self.player.row if self.rng.random() < .43 else self.rng.randrange(ROWS)
        room = self.rooms[row*COLS+col]
        self._new_hazard(self.demon.throw_fire(room, self.threat), self.fireballs)

    def _spawn_debris(self):
        col = self.player.col if self.rng.random() < .55 else self.rng.randrange(COLS)
        speed = 115+15*self.threat+self.rng.randrange(35)
        self._new_hazard(Debris(ROOM_X[col], speed), self.rocks)

    def _spread_fire(self):
        burning = [room for room in self.rooms if room.fire > 0]
        self.rng.shuffle(burning)
        for source in burning:
            neighbors = [room for room in self.rooms
                         if room.fire == 0
                         and abs(room.col-source.col)+abs(room.row-source.row) == 1]
            if neighbors and self.rng.random() < .4:
                room = self.rng.choice(neighbors)
                room.ignite(.65)
                self._scatter(room.x, room.y, FIRE)
                return

    def _spawn_victim(self):
        if sum(room.needs_rescue for room in self.rooms) >= 6:
            return
        choices = [room for room in self.rooms if not room.needs_rescue]
        if choices:
            self.rng.choice(choices).add_victim()

    def _action(self, dt):
        keys = pygame.key.get_pressed()
        use_water = keys[pygame.K_SPACE] or keys[pygame.K_j]
        help_person = keys[pygame.K_e]
        room = self.room_at_player()
        self.player.action = False
        self.player.action_progress = 0
        if not self.player.arrived:
            return
        if use_water and room.fire > 0:
            self.player.action = True
            if room.spray(dt):
                announce(FIRE_OUT, points=100)
                self._scatter(room.x, room.y, BLUE, 18)
            self.player.action_progress = 1-room.fire/1.7
        elif (use_water or help_person) and room.needs_rescue and room.fire == 0:
            self.player.action = True
            if room.rescue(dt):
                announce(PERSON_SAVED, points=250)
                self._scatter(room.x, room.y, MINT, 20)
            self.player.action_progress = min(1, room.rescue_progress/.85)
        else:
            room.rescue_progress = max(0, room.rescue_progress-dt*.5)
        # Remaining inside a burning room is dangerous, even without projectiles.
        if room.fire > 0:
            self.heat_timer += dt
            if self.heat_timer > 3.7:
                self.heat_timer = 0
                self._damage_player()
        else:
            self.heat_timer = 0

    def _damage_player(self):
        if self.player.take_damage():
            announce(PLAYER_HIT)
            self._scatter(self.player.x, self.player.feet_y-18, ORANGE, 18)
            if self.player.lives == 0:
                self.game.score.save()
                self.game.change_state(GameOverState(self.game, self.elapsed))

    def _collisions(self):
        # Week 10 + 12: collision between groups, NOT an isinstance() chain.
        # Two swept rectangles detect hits *during* a fall or player movement.
        def collided(player, hazard):
            return player.swept_hitbox.colliderect(hazard.swept_hitbox)

        hits = pygame.sprite.groupcollide(
            self.players, self.hazards, False, True, collided=collided)
        if hits:
            self._damage_player()  # invincible period prevents duplicate damage

        # Projectiles that were not intercepted can ignite their target room.
        for ball in self.fireballs.sprites():
            if ball.landed:
                ball.target_room.ignite(.78)
                self._scatter(ball.target_room.x, ball.target_room.y, FIRE, 12)
                if (ball.target_room.col == self.player.col and
                        ball.target_room.row == self.player.row):
                    self._damage_player()
                ball.kill()
        for rock in self.rocks.sprites():
            if rock.landed:
                rock.kill()

    def update(self, dt):
        self.elapsed += dt
        self.bonus_timer += dt
        if self.bonus_timer >= 10:
            self.bonus_timer -= 10
            announce(SURVIVAL_BONUS, points=20)
        self._action(dt)
        if self.game.state_stack[-1] is not self:
            return  # The last heart was lost during the action.
        # Week 10: unified polymorphic update() — every sprite chooses its behavior.
        self.all_sprites.update(dt)
        self.game.notice.update(dt)

        self.fireball_timer -= dt
        if self.fireball_timer <= 0:
            self._spawn_fireball()
            self.fireball_timer = max(.85, 3-.22*(self.threat-1)) * self.rng.uniform(.84, 1.20)
        self.debris_timer -= dt
        if self.debris_timer <= 0:
            self._spawn_debris()
            self.debris_timer = max(.75, 2.6-.17*(self.threat-1))*self.rng.uniform(.8, 1.2)
        self.spread_timer -= dt
        if self.spread_timer <= 0:
            self._spread_fire()
            self.spread_timer = max(3.4, 8-.52*(self.threat-1))
        self.victim_timer -= dt
        if self.victim_timer <= 0:
            self._spawn_victim()
            self.victim_timer = max(4.5, 10.5-.5*(self.threat-1))
        self._collisions()

    def draw(self, screen):
        self.game.scene.draw_building(screen, self.elapsed)
        # Attack warnings are visible before a fireball reaches a room.
        for ball in self.fireballs:
            x, y = ball.target_room.x, ball.target_room.y
            if int(self.elapsed*9) % 2:
                pygame.draw.rect(screen, ORANGE, (x-20, y-28, 40, 49), 2)
        self.all_sprites.draw(screen)
        self.game.scene.draw_hud(screen, self, self.game.score, self.game.notice)


class PauseState(GameState):
    """Push/pop pauses PlayState without destroying its score or sprites."""

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_p, pygame.K_ESCAPE):
            self.game.pop_state()

    def update(self, dt):
        pass  # The PlayState underneath is frozen while this state is on top.

    def draw(self, screen):
        self.game.scene.draw_overlay(screen, "PAUSED", [
            "THE FIRE DEMON IS WAITING...",
            "SCORE AND POSITIONS ARE SAVED",
            "PRESS P OR ESC TO RESUME",
        ], "RESUME [P]")


class GameOverState(GameState):
    def __init__(self, game, elapsed):
        super().__init__(game)
        self.elapsed = elapsed
        self.clock = 0.0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_r, pygame.K_RETURN):
                self.game.change_state(PlayState(self.game))
            elif event.key in (pygame.K_m, pygame.K_ESCAPE):
                self.game.change_state(MenuState(self.game))

    def update(self, dt):
        self.clock += dt

    def draw(self, screen):
        self.game.scene.draw_building(screen, self.clock)
        seconds = int(self.elapsed)
        self.game.scene.draw_overlay(screen, "GAME OVER", [
            f"SCORE       {self.game.score.score:06d}",
            f"HIGH SCORE  {self.game.score.best:06d}",
            f"SURVIVED    {seconds//60:02}:{seconds%60:02}",
            "R = REPLAY   M = MENU",
        ], "REPLAY [ENTER]")


# ======================================================================
# GAME CONTEXT (original: core/game.py)
# ======================================================================

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Fire Rescue - Endless Inferno [SF211 OOP]")
        self.screen = pygame.display.set_mode((WIDTH*SCALE, HEIGHT*SCALE))
        self.canvas = pygame.Surface((WIDTH, HEIGHT)).convert()
        self.clock = pygame.time.Clock()
        self.scene = Scene()
        self.score = ScoreManager()
        self.notice = NoticeManager()
        self.observers = [self.score, self.notice]
        self.state_stack = []
        self.running = True
        self.change_state(MenuState(self))
        pygame.key.set_repeat(170, 120)

    def change_state(self, state):
        while self.state_stack:
            self.state_stack.pop().exit()
        self.state_stack.append(state)
        state.enter()

    def push_state(self, state):
        self.state_stack.append(state)
        state.enter()

    def pop_state(self):
        if len(self.state_stack) > 1:
            return self.state_stack.pop().exit()
        return None

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS)/1000.0, .05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                # Week 12: all observers receive the same event.
                for observer in self.observers:
                    observer.handle_event(event)
                # Week 13: only the TOP state receives keyboard/mouse input.
                self.state_stack[-1].handle_event(event)
            if not self.running:
                break
            # Polymorphism: no menu/playing/paused flags in the main loop.
            self.state_stack[-1].update(dt)
            for state in self.state_stack:
                state.draw(self.canvas)
            pygame.transform.scale(self.canvas,
                                   (WIDTH*SCALE, HEIGHT*SCALE), self.screen)
            pygame.display.flip()
        self.score.save()
        pygame.quit()


# ======================================================================
# OPTIONAL SELF-CHECKS: test OOP, gameplay and High Score without files
# ======================================================================

def run_checks():
    """Run a few lightweight checks in the SAME Python file."""

    class FireRescueChecks(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            pygame.init()
            pygame.display.set_mode((1, 1))

        @classmethod
        def tearDownClass(cls):
            pygame.quit()

        def test_abc_contract(self):
            class Incomplete(GameObject):
                def update(self, dt):
                    pass
            with self.assertRaises(TypeError):
                Incomplete((5, 5), (0, 0))

        def test_encapsulation(self):
            room = Room(0, 0)
            room.fire = -10
            self.assertEqual(room.fire, 0)
            room.fire = 20
            self.assertEqual(room.fire, 1.7)
            person = Firefighter()
            person.lives = 50
            self.assertEqual(person.lives, 3)
            person.lives = -2
            self.assertEqual(person.lives, 0)

        def test_rescue(self):
            room = Room(2, 2)
            room.add_victim()
            room.ignite(.5)
            self.assertFalse(room.rescue(1))
            self.assertTrue(room.spray(.5))
            self.assertTrue(room.rescue(1))
            self.assertFalse(room.needs_rescue)

        def test_fireball(self):
            demon = FireDemon()
            room = Room(1, 1)
            ball = demon.throw_fire(room, 2)
            ball.update(3)
            self.assertTrue(ball.landed)
            self.assertAlmostEqual(ball.x, room.x)

        def test_debris_midair_collision(self):
            game = Game()
            play = PlayState(game)
            game.change_state(play)
            play.player.invincible = 0
            rock = Debris(play.player.x, 160)
            play._new_hazard(rock, play.rocks)
            rock.update(1.5)
            self.assertFalse(rock.landed)
            play._collisions()
            self.assertEqual(play.player.lives, 2)
            self.assertEqual(len(play.rocks), 0)

        def test_pause_keeps_progress(self):
            game = Game()
            play = PlayState(game)
            game.change_state(play)
            play.player.move(-1, 0)
            game.push_state(PauseState(game))
            game.state_stack[-1].update(1)
            self.assertEqual(play.elapsed, 0)
            game.pop_state()
            self.assertIs(game.state_stack[-1], play)
            self.assertEqual(play.player.col, 1)

        def test_high_score(self):
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'score.json'
                manager = ScoreManager(path)
                manager.handle_event(pygame.event.Event(FIRE_OUT, {'points': 100}))
                manager.handle_event(pygame.event.Event(PERSON_SAVED, {'points': 250}))
                self.assertEqual(manager.score, 350)
                self.assertEqual(ScoreManager(path).best, 350)
                manager.reset()
                self.assertEqual(manager.score, 0)
                self.assertEqual(manager.best, 350)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(FireRescueChecks)
    )
    return result.wasSuccessful()


if __name__ == "__main__":
    if "--check" in sys.argv:
        raise SystemExit(0 if run_checks() else 1)
    Game().run()

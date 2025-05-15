import pygame
import sys
import math
import os
from pygame.locals import *

pygame.init()
pygame.mixer.init()

# Load sound
try:
    TOUCH_SOUND = pygame.mixer.Sound("touch.wav")
except pygame.error:
    TOUCH_SOUND = None
    print("⚠️ Could not load 'touch.wav'. Please place it in the same folder.")

# Display setup
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("Skeletal Reptile")

# Colors
COLORS = [(180, 180, 180), (0, 255, 0), (255, 100, 100), (100, 255, 255), (255, 255, 0)]
color_index = 0
BONE_COLOR = COLORS[color_index]

class SkeletalReptile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.speed = 3
        self.max_speed = 8
        self.movement_lag = 15

        self.base_segment_size = 5
        self.head_base_size = 8
        self.head_grow = False
        self.sound_played = False

        self.num_segments = 30
        self.segments = []
        self.segment_spacing = 10

        for i in range(self.num_segments):
            self.segments.append({
                'x': x - i * self.segment_spacing,
                'y': y,
                'size': self.base_segment_size - min(2, i * 0.08)
            })

        self.leg_count = 10
        self.leg_length = 20
        self.leg_angles = []
        self.leg_animation_speeds = []
        for i in range(self.leg_count):
            angle = 0.6 if i % 2 == 0 else -0.6
            self.leg_angles.append(angle)
            self.leg_animation_speeds.append(0.12 + (i * 0.005))

        # --- NEW FEATURE: Tail sway phase for animation ---
        self.tail_wave_phase = 0

    def update(self, mouse_pos):
        dx = mouse_pos[0] - self.x
        dy = mouse_pos[1] - self.y
        distance = max(1, math.hypot(dx, dy))

        current_speed = min(self.max_speed, self.speed + (distance / 80))

        if distance > self.movement_lag:
            self.target_x = mouse_pos[0] - (dx / distance) * self.movement_lag
            self.target_y = mouse_pos[1] - (dy / distance) * self.movement_lag
        else:
            self.target_x, self.target_y = mouse_pos

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance_to_target = max(1, math.hypot(dx, dy))

        if distance_to_target > 1:
            self.x += (dx / distance_to_target) * current_speed
            self.y += (dy / distance_to_target) * current_speed

        prev_x, prev_y = self.x, self.y
        for i, segment in enumerate(self.segments):
            dx = prev_x - segment['x']
            dy = prev_y - segment['y']
            distance = max(1, math.hypot(dx, dy))
            if distance > self.segment_spacing:
                segment_speed = current_speed * (0.95 - (i * 0.01))
                segment['x'] += (dx / distance) * segment_speed
                segment['y'] += (dy / distance) * segment_speed

            # --- NEW FEATURE: Tail animation using sine wave ---
            if i >= 20:
                sway = math.sin(self.tail_wave_phase + i * 0.3) * 2
                segment['y'] += sway

            prev_x, prev_y = segment['x'], segment['y']

        self.tail_wave_phase += 0.12

        # Leg animation
        is_moving = distance_to_target > 2
        for i in range(self.leg_count):
            if is_moving:
                self.leg_angles[i] += self.leg_animation_speeds[i] * (1 if i % 2 == 0 else -1)
                if abs(self.leg_angles[i]) > 0.8:
                    self.leg_angles[i] = 0.8 if self.leg_angles[i] > 0 else -0.8
                    self.leg_animation_speeds[i] *= -1
            else:
                self.leg_angles[i] *= 0.9

        # --- NEW FEATURE: Sound FX on touch ---
        is_touching = math.hypot(mouse_pos[0] - self.x, mouse_pos[1] - self.y) < 30
        self.head_grow = is_touching
        if is_touching and not self.sound_played and TOUCH_SOUND:
            TOUCH_SOUND.play()
            self.sound_played = True
        elif not is_touching:
            self.sound_played = False

    def draw(self, screen, bone_color, mouse_pos):
        head_size = self.head_base_size * (1.5 if self.head_grow else 1)

        # --- NEW FEATURE: Glow effect ---
        glow_color = (*bone_color, 40)  # RGBA for transparent glow
        glow_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        for i, segment in enumerate(self.segments):
            pos = (int(segment['x']), int(segment['y']))
            pygame.draw.circle(screen, bone_color, pos, int(segment['size']))
            if i > 0:
                prev = self.segments[i - 1]
                pygame.draw.line(screen, bone_color, (int(prev['x']), int(prev['y'])),
                                 pos, 2)
            # Glow aura
            pygame.draw.circle(glow_surface, glow_color, pos, 20)

        # Draw the glow layer
        screen.blit(glow_surface, (0, 0))

        # Legs
        leg_spacing = self.num_segments // (self.leg_count + 1)
        for i, segment in enumerate(self.segments):
            if (i + 1) % leg_spacing == 0 and (i + 1) // leg_spacing <= self.leg_count:
                leg_idx = (i + 1) // leg_spacing - 1
                if i > 0:
                    prev = self.segments[i - 1]
                    dx = segment['x'] - prev['x']
                    dy = segment['y'] - prev['y']
                    spine_angle = math.atan2(dy, dx)
                else:
                    spine_angle = 0
                for side in [-1, 1]:
                    leg_angle = spine_angle + (math.pi/2 * side) + side * self.leg_angles[leg_idx]
                    x1, y1 = segment['x'], segment['y']
                    upper_x = x1 + math.cos(leg_angle) * self.leg_length * 0.6
                    upper_y = y1 + math.sin(leg_angle) * self.leg_length * 0.6
                    foot_angle = leg_angle + (0.7 if leg_idx % 2 == 0 else -0.3) * side
                    foot_x = upper_x + math.cos(foot_angle) * self.leg_length * 0.4
                    foot_y = upper_y + math.sin(foot_angle) * self.leg_length * 0.4
                    pygame.draw.line(screen, bone_color, (int(x1), int(y1)), (int(upper_x), int(upper_y)), 2)
                    pygame.draw.line(screen, bone_color, (int(upper_x), int(upper_y)), (int(foot_x), int(foot_y)), 2)
                    for toe in range(3):
                        toe_angle = foot_angle + (toe - 1) * 0.4 * side
                        toe_x = foot_x + math.cos(toe_angle) * 5
                        toe_y = foot_y + math.sin(toe_angle) * 5
                        pygame.draw.line(screen, bone_color, (int(foot_x), int(foot_y)), (int(toe_x), int(toe_y)), 1)

        # Head
        pygame.draw.circle(screen, bone_color, (int(self.x), int(self.y)), int(head_size))
        pygame.draw.circle(screen, (0, 0, 0), (int(self.x - 3), int(self.y - 2)), 2)
        pygame.draw.circle(screen, (0, 0, 0), (int(self.x + 3), int(self.y - 2)), 2)

# Game Loop
reptile = SkeletalReptile(WIDTH // 2, HEIGHT // 2)
clock = pygame.time.Clock()

running = True
while running:
    screen.fill((0, 0, 0))
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            running = False
        if event.type == KEYDOWN:
            if event.key == K_c:
                color_index = (color_index + 1) % len(COLORS)
                BONE_COLOR = COLORS[color_index]
            if event.key == K_UP:
                reptile.speed = min(10, reptile.speed + 0.5)
            if event.key == K_DOWN:
                reptile.speed = max(1, reptile.speed - 0.5)

    reptile.update(mouse_pos)
    reptile.draw(screen, BONE_COLOR, mouse_pos)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()


import pygame
import sys
import math
import os
from pygame.locals import *

pygame.init()
pygame.mixer.init()

# Load sound (optional)
try:
    TOUCH_SOUND = pygame.mixer.Sound("touch.wav")
except pygame.error:
    TOUCH_SOUND = None
    print("⚠️ Could not load 'touch.wav'. Please place it in the same folder.")

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("Skeletal Reptile")

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

        self.base_segment_size = 7
        self.head_base_size = 16
        self.head_grow = False
        self.sound_played = False

        self.num_segments = 24
        self.segments = []
        self.segment_spacing = 14

        for i in range(self.num_segments):
            self.segments.append({
                'x': x - i * self.segment_spacing,
                'y': y,
                'size': self.base_segment_size - min(2, i * 0.08)
            })

        self.leg_length = 48
        self.leg_phase = [0, 0, 0, 0]
        self.leg_anim_speeds = [0.13, -0.13, 0.14, -0.14]

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
                segment_speed = current_speed * (0.97 - (i * 0.015))
                segment['x'] += (dx / distance) * segment_speed
                segment['y'] += (dy / distance) * segment_speed
            # Tail sway
            if i >= self.num_segments - 5:
                sway = math.sin(self.tail_wave_phase + i * 0.32) * 2
                segment['y'] += sway
            prev_x, prev_y = segment['x'], segment['y']

        self.tail_wave_phase += 0.09

        # Leg walk cycle
        is_moving = distance_to_target > 2
        for i in range(4):
            if is_moving:
                self.leg_phase[i] += self.leg_anim_speeds[i]
            else:
                self.leg_phase[i] *= 0.8

        # Sound FX on touch
        is_touching = math.hypot(mouse_pos[0] - self.x, mouse_pos[1] - self.y) < 40
        self.head_grow = is_touching
        if is_touching and not self.sound_played and TOUCH_SOUND:
            TOUCH_SOUND.play()
            self.sound_played = True
        elif not is_touching:
            self.sound_played = False

    def draw(self, screen, bone_color, mouse_pos):
        # --- Spine ---
        for i, segment in enumerate(self.segments):
            pos = (int(segment['x']), int(segment['y']))
            pygame.draw.circle(screen, bone_color, pos, int(segment['size']))
            if i > 0:
                prev = self.segments[i - 1]
                pygame.draw.line(screen, bone_color, (int(prev['x']), int(prev['y'])), pos, 5 if i<4 else 3)
        # --- Ribs (fan shape) ---
        rib_count = 7
        for i in range(4, 4 + rib_count):
            seg = self.segments[i]
            base = (seg['x'], seg['y'])
            frac = (i-4)/(rib_count-1) - 0.5
            angle = math.pi/2 + frac*math.pi/2
            length = 40 - abs(frac)*18
            for s in [-1, 1]:
                rib_ang = angle * s
                rx = base[0] + math.cos(rib_ang) * length
                ry = base[1] + math.sin(rib_ang) * length
                pygame.draw.line(screen, bone_color, base, (rx, ry), 2)

        # === LIMBS PROPERLY ATTACHED USING SPINE NORMALS ===

        def normal_at(idx):
            if 1 < idx < len(self.segments) - 2:
                x0, y0 = self.segments[idx-2]['x'], self.segments[idx-2]['y']
                x1, y1 = self.segments[idx+2]['x'], self.segments[idx+2]['y']
                dx, dy = x1 - x0, y1 - y0
            elif idx > 0:
                x0, y0 = self.segments[idx-1]['x'], self.segments[idx-1]['y']
                x1, y1 = self.segments[idx]['x'], self.segments[idx]['y']
                dx, dy = x1 - x0, y1 - y0
            else:
                dx, dy = 1, 0
            length = math.hypot(dx, dy)
            return -dy/length, dx/length  # Unit normal

        arm_idx = 6
        leg_idx = 16

        # ARMS
        arm_x, arm_y = self.segments[arm_idx]['x'], self.segments[arm_idx]['y']
        nx, ny = normal_at(arm_idx)
        for i, side in enumerate([-1, 1]):
            dir_x, dir_y = nx*side, ny*side
            upper_len = self.leg_length * 0.8
            lower_len = self.leg_length * 0.7
            # Walk cycle "wiggle":
            wiggle = math.sin(self.leg_phase[i]) * 0.5
            limb_angle = math.atan2(dir_y, dir_x) + wiggle
            mid_x = arm_x + math.cos(limb_angle) * upper_len
            mid_y = arm_y + math.sin(limb_angle) * upper_len
            elbow_angle = limb_angle + 0.5 * side
            foot_x = mid_x + math.cos(elbow_angle) * lower_len
            foot_y = mid_y + math.sin(elbow_angle) * lower_len
            pygame.draw.line(screen, bone_color, (arm_x, arm_y), (mid_x, mid_y), 7)
            pygame.draw.line(screen, bone_color, (mid_x, mid_y), (foot_x, foot_y), 6)
            for t in range(-2, 3):
                toe_ang = elbow_angle + t * 0.18
                toe_x = foot_x + math.cos(toe_ang) * 13
                toe_y = foot_y + math.sin(toe_ang) * 13
                pygame.draw.line(screen, bone_color, (foot_x, foot_y), (toe_x, toe_y), 2)

        # LEGS
        leg_x, leg_y = self.segments[leg_idx]['x'], self.segments[leg_idx]['y']
        nx, ny = normal_at(leg_idx)
        for i, side in enumerate([-1, 1]):
            dir_x, dir_y = nx*side, ny*side
            upper_len = self.leg_length
            lower_len = self.leg_length * 0.9
            wiggle = math.sin(self.leg_phase[2+i]) * 0.5
            limb_angle = math.atan2(dir_y, dir_x) + wiggle
            mid_x = leg_x + math.cos(limb_angle) * upper_len
            mid_y = leg_y + math.sin(limb_angle) * upper_len
            knee_angle = limb_angle + 0.5 * side
            foot_x = mid_x + math.cos(knee_angle) * lower_len
            foot_y = mid_y + math.sin(knee_angle) * lower_len
            pygame.draw.line(screen, bone_color, (leg_x, leg_y), (mid_x, mid_y), 8)
            pygame.draw.line(screen, bone_color, (mid_x, mid_y), (foot_x, foot_y), 7)
            for t in range(-2, 3):
                toe_ang = knee_angle + t * 0.18
                toe_x = foot_x + math.cos(toe_ang) * 14
                toe_y = foot_y + math.sin(toe_ang) * 14
                pygame.draw.line(screen, bone_color, (foot_x, foot_y), (toe_x, toe_y), 2)

        # --- Head (big oval) ---
        head_size = self.head_base_size * (1.5 if self.head_grow else 1)
        pygame.draw.ellipse(screen, bone_color, (int(self.x-head_size*1.3), int(self.y-head_size*1.1), int(head_size*2.6), int(head_size*2.1)))
        # Eyes
        pygame.draw.ellipse(screen, (0, 0, 0), (int(self.x-head_size*0.7), int(self.y-head_size*0.3), int(head_size*0.7), int(head_size*0.9)), 2)
        pygame.draw.ellipse(screen, (0, 0, 0), (int(self.x+head_size*0.2), int(self.y-head_size*0.3), int(head_size*0.7), int(head_size*0.9)), 2)

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


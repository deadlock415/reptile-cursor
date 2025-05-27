import pygame
import math
import sys
import random
import time

# Initialize Pygame
pygame.init()

# Get screen dimensions for fullscreen
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

# Constants
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (255, 0, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)

COLORS = [WHITE, GREEN, RED, BLUE, YELLOW, PURPLE, CYAN, ORANGE]
COLOR_NAMES = ["White", "Green", "Red", "Blue", "Yellow", "Purple", "Cyan", "Orange"]

FPS = 60

class ReptileSkeleton:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.ground_y = SCREEN_HEIGHT - 100  # Ground level
        self.spine_segments = 20
        self.tail_segments = 15
        self.spine_length = 15
        self.tail_length = 12
        
        # Movement properties
        self.speed = 0.08
        self.walk_cycle = 0
        self.step_height = 8
        self.body_bob = 0
        
        # Store positions for smooth movement
        self.spine_positions = [(x, y) for _ in range(self.spine_segments)]
        self.tail_positions = [(x, y) for _ in range(self.tail_segments)]
        
        # Head properties
        self.head_size = 30
        self.eye_size = 8
        
        # Limb properties
        self.limb_length = 40
        self.foot_size = 20
        
        # Color
        self.color_index = 0
        self.current_color = COLORS[self.color_index]
        
        # Walking animation
        self.is_moving = False
        self.last_x = x
        self.last_y = y
        
        # Realistic behavior
        self.idle_timer = 0
        self.idle_head_sway = 0
        self.breathing_cycle = 0
        
    def update_speed(self, delta):
        self.speed = max(0.02, min(0.3, self.speed + delta))
    
    def change_color(self):
        self.color_index = (self.color_index + 1) % len(COLORS)
        self.current_color = COLORS[self.color_index]
        return COLOR_NAMES[self.color_index]
    
    def update(self, target_x, target_y):
        self.target_x = target_x
        self.target_y = target_y
        
        # Calculate movement
        old_x, old_y = self.x, self.y
        self.x += (self.target_x - self.x) * self.speed
        self.y += (self.target_y - self.y) * self.speed
        
        # Check if moving
        distance_moved = math.sqrt((self.x - old_x)**2 + (self.y - old_y)**2)
        self.is_moving = distance_moved > 0.5
        
        if self.is_moving:
            self.walk_cycle += 0.3
            self.idle_timer = 0
            # Add body bobbing while walking
            self.body_bob = math.sin(self.walk_cycle) * 3
        else:
            self.idle_timer += 1
            self.body_bob *= 0.95  # Gradually stop bobbing
            # Add subtle idle animations
            self.idle_head_sway = math.sin(self.idle_timer * 0.02) * 2
            
        # Breathing animation
        self.breathing_cycle += 0.05
        breathing_offset = math.sin(self.breathing_cycle) * 1
        
        # Apply body movement
        final_y = self.y + self.body_bob + breathing_offset
        
        # Update spine positions (follow the head)
        self.spine_positions[0] = (self.x + self.idle_head_sway, final_y)
        
        for i in range(1, len(self.spine_positions)):
            prev_x, prev_y = self.spine_positions[i-1]
            curr_x, curr_y = self.spine_positions[i]
            
            # Calculate direction and distance
            dx = prev_x - curr_x
            dy = prev_y - curr_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > self.spine_length:
                # Normalize and set to correct distance
                dx = dx / distance * self.spine_length
                dy = dy / distance * self.spine_length
                self.spine_positions[i] = (prev_x - dx, prev_y - dy)
        
        # Update tail positions (follow the last spine segment)
        if self.spine_positions:
            last_spine_x, last_spine_y = self.spine_positions[-1]
            self.tail_positions[0] = (last_spine_x, last_spine_y)
            
            for i in range(1, len(self.tail_positions)):
                prev_x, prev_y = self.tail_positions[i-1]
                curr_x, curr_y = self.tail_positions[i]
                
                dx = prev_x - curr_x
                dy = prev_y - curr_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance > self.tail_length:
                    dx = dx / distance * self.tail_length
                    dy = dy / distance * self.tail_length
                    # Tail can lift slightly but should generally stay low
                    new_y = prev_y - dy
                    self.tail_positions[i] = (prev_x - dx, new_y)
    
    def draw_ground(self, screen):
        # Draw ground line
        pygame.draw.line(screen, self.current_color, (0, self.ground_y), (SCREEN_WIDTH, self.ground_y), 2)
        
        # Draw some ground texture
        for i in range(0, SCREEN_WIDTH, 50):
            if random.random() > 0.7:
                # Small rocks or debris
                rock_size = random.randint(2, 4)
                rock_x = i + random.randint(-10, 10)
                rock_y = self.ground_y + random.randint(0, 5)
                color = tuple(max(0, c - 100) for c in self.current_color)
                pygame.draw.circle(screen, color, (rock_x, rock_y), rock_size)
    
    def draw_head(self, screen):
        # Draw skull outline
        head_x, head_y = self.spine_positions[0]
        
        # Add slight head movement based on breathing
        head_y += math.sin(self.breathing_cycle) * 0.5
        
        # Main skull shape (elongated oval)
        skull_points = []
        for angle in range(0, 360, 15):
            rad = math.radians(angle)
            if angle < 90 or angle > 270:  # Front part (snout)
                radius_x = self.head_size * 1.2
                radius_y = self.head_size * 0.6
            else:  # Back part (wider skull)
                radius_x = self.head_size * 0.8
                radius_y = self.head_size * 0.8
            
            x = head_x + radius_x * math.cos(rad)
            y = head_y + radius_y * math.sin(rad)
            skull_points.append((x, y))
        
        pygame.draw.polygon(screen, self.current_color, skull_points, 2)
        
        # Draw eye sockets with blinking
        blink = math.sin(self.idle_timer * 0.1) < -0.9 if not self.is_moving else False
        eye_size = 2 if blink else self.eye_size
        
        eye1_x = head_x - self.head_size * 0.3
        eye1_y = head_y - self.head_size * 0.2
        eye2_x = head_x - self.head_size * 0.3
        eye2_y = head_y + self.head_size * 0.2
        
        pygame.draw.circle(screen, self.current_color, (int(eye1_x), int(eye1_y)), eye_size, 2)
        pygame.draw.circle(screen, self.current_color, (int(eye2_x), int(eye2_y)), eye_size, 2)
        
        # Draw nasal cavity
        nose_x = head_x + self.head_size * 0.8
        nose_y = head_y
        pygame.draw.circle(screen, self.current_color, (int(nose_x), int(nose_y)), 4, 2)
    
    def draw_spine_and_ribs(self, screen):
        # Draw spine
        if len(self.spine_positions) > 1:
            pygame.draw.lines(screen, self.current_color, False, self.spine_positions, 3)
        
        # Draw ribs
        for i, (x, y) in enumerate(self.spine_positions[2:], 2):
            if i < len(self.spine_positions) - 3:  # Don't draw ribs too close to tail
                rib_length = 25 - (i * 1.5)  # Ribs get smaller towards tail
                if rib_length > 5:
                    # Add breathing movement to ribs
                    breath_expand = math.sin(self.breathing_cycle) * 2
                    
                    # Left rib
                    rib1_end = (x - rib_length - breath_expand, y + rib_length * 0.8)
                    pygame.draw.line(screen, self.current_color, (x, y), rib1_end, 2)
                    
                    # Right rib
                    rib2_end = (x + rib_length + breath_expand, y + rib_length * 0.8)
                    pygame.draw.line(screen, self.current_color, (x, y), rib2_end, 2)
    
    def draw_tail(self, screen):
        if len(self.tail_positions) > 1:
            # Draw tail spine
            pygame.draw.lines(screen, self.current_color, False, self.tail_positions, 2)
            
            # Draw tail vertebrae marks
            for i, (x, y) in enumerate(self.tail_positions[::2]):
                size = max(1, 4 - i // 2)
                pygame.draw.circle(screen, self.current_color, (int(x), int(y)), size, 1)
    
    def draw_limbs(self, screen):
        if len(self.spine_positions) >= 6:
            # Walking animation for limbs
            front_lift_left = math.sin(self.walk_cycle) * self.step_height if self.is_moving else 0
            front_lift_right = math.sin(self.walk_cycle + math.pi) * self.step_height if self.is_moving else 0
            
            # Front limbs (attached to 3rd spine segment)
            front_x, front_y = self.spine_positions[3]
            
            # Left front limb
            upper_arm_end = (front_x - 25, front_y + 15 - front_lift_left * 0.3)
            forearm_end = (front_x - 40, front_y + 35 - front_lift_left)
            pygame.draw.line(screen, self.current_color, (front_x, front_y), upper_arm_end, 2)
            pygame.draw.line(screen, self.current_color, upper_arm_end, forearm_end, 2)
            
            # Left front foot
            self.draw_foot(screen, forearm_end[0], forearm_end[1], -1)
            
            # Right front limb
            upper_arm_end = (front_x + 25, front_y + 15 - front_lift_right * 0.3)
            forearm_end = (front_x + 40, front_y + 35 - front_lift_right)
            pygame.draw.line(screen, self.current_color, (front_x, front_y), upper_arm_end, 2)
            pygame.draw.line(screen, self.current_color, upper_arm_end, forearm_end, 2)
            
            # Right front foot
            self.draw_foot(screen, forearm_end[0], forearm_end[1], 1)
        
        if len(self.spine_positions) >= 12:
            # Back limbs with opposite walking cycle
            back_lift_left = math.sin(self.walk_cycle + math.pi) * self.step_height if self.is_moving else 0
            back_lift_right = math.sin(self.walk_cycle) * self.step_height if self.is_moving else 0
            
            # Back limbs (attached to spine segment further back)
            back_x, back_y = self.spine_positions[11]
            
            # Left back limb
            upper_leg_end = (back_x - 30, back_y + 20 - back_lift_left * 0.3)
            lower_leg_end = (back_x - 45, back_y + 45 - back_lift_left)
            pygame.draw.line(screen, self.current_color, (back_x, back_y), upper_leg_end, 2)
            pygame.draw.line(screen, self.current_color, upper_leg_end, lower_leg_end, 2)
            
            # Left back foot
            self.draw_foot(screen, lower_leg_end[0], lower_leg_end[1], -1)
            
            # Right back limb
            upper_leg_end = (back_x + 30, back_y + 20 - back_lift_right * 0.3)
            lower_leg_end = (back_x + 45, back_y + 45 - back_lift_right)
            pygame.draw.line(screen, self.current_color, (back_x, back_y), upper_leg_end, 2)
            pygame.draw.line(screen, self.current_color, upper_leg_end, lower_leg_end, 2)
            
            # Right back foot
            self.draw_foot(screen, lower_leg_end[0], lower_leg_end[1], 1)
    
    def draw_foot(self, screen, x, y, direction):
        # Draw toes
        for i in range(5):
            toe_angle = math.radians(-30 + i * 15) if direction == -1 else math.radians(210 + i * 15)
            toe_length = 8 + i * 2 if i < 3 else 10 - (i - 2) * 2
            toe_end_x = x + toe_length * math.cos(toe_angle)
            toe_end_y = y + toe_length * math.sin(toe_angle)
            pygame.draw.line(screen, self.current_color, (x, y), (toe_end_x, toe_end_y), 1)
    
    def draw(self, screen):
        self.draw_ground(screen)
        self.draw_spine_and_ribs(screen)
        self.draw_tail(screen)
        self.draw_limbs(screen)
        self.draw_head(screen)

def draw_ui(screen, reptile, font):
    # Draw UI information
    ui_texts = [
        f"Speed: {reptile.speed:.2f} (↑/↓ to adjust)",
        f"Color: {COLOR_NAMES[reptile.color_index]} (C to change)",
        "ESC to exit, F11 to toggle fullscreen",
        f"Status: {'Walking' if reptile.is_moving else 'Idle'}"
    ]
    
    for i, text in enumerate(ui_texts):
        text_surface = font.render(text, True, reptile.current_color)
        screen.blit(text_surface, (10, 10 + i * 25))

def main():
    # Create fullscreen display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("Advanced Reptile Skeleton - Realistic Walking Simulation")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    
    # Create reptile at center of screen
    reptile = ReptileSkeleton(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    
    fullscreen = True
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_F11:
                    # Toggle fullscreen
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((1200, 800))
                elif event.key == pygame.K_UP:
                    reptile.update_speed(0.02)
                elif event.key == pygame.K_DOWN:
                    reptile.update_speed(-0.02)
                elif event.key == pygame.K_c:
                    color_name = reptile.change_color()
                    print(f"Color changed to: {color_name}")
        
        # Get cursor position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # Update reptile position to follow cursor
        reptile.update(mouse_x, mouse_y)
        
        # Clear screen
        screen.fill(BLACK)
        
        # Draw reptile
        reptile.draw(screen)
        
        # Draw cursor position indicator
        pygame.draw.circle(screen, reptile.current_color, (mouse_x, mouse_y), 5, 2)
        
        # Draw UI
        draw_ui(screen, reptile, font)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

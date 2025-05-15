import pygame
import sys
import math
from pygame.locals import *

# Initialize pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Skeletal Reptile Cursor")

# Colors
BLACK = (0, 0, 0)
BONE_COLOR = (180, 180, 180)
WHITE = (255, 255, 255)

class SkeletalReptile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.speed = 3
        self.max_speed = 8
        self.movement_lag = 15
        
        # Spine segments
        self.num_segments = 30
        self.segments = []
        self.segment_spacing = 10
        self.segment_size = 5
        
        # Initialize spine segments
        for i in range(self.num_segments):
            self.segments.append({
                'x': x - i * self.segment_spacing,
                'y': y,
                'size': self.segment_size - min(2, i * 0.08)  # Segments get smaller toward tail
            })
        
        # Leg properties
        self.leg_count = 10
        self.leg_length = 20
        self.leg_angles = []
        self.leg_animation_speeds = []
        
        # Initialize leg animation values
        for i in range(self.leg_count):
            # Alternate initial angles for walking effect
            angle = 0.6 if i % 2 == 0 else -0.6
            self.leg_angles.append(angle)
            # Vary animation speed slightly for each leg
            self.leg_animation_speeds.append(0.12 + (i * 0.005))
        
        # Head properties
        self.head_size = 8
        self.eye_size = 2
        
    def update(self, mouse_pos):
        # Calculate direction to mouse
        dx = mouse_pos[0] - self.x
        dy = mouse_pos[1] - self.y
        distance = max(1, math.sqrt(dx * dx + dy * dy))
        
        # Adjust speed based on distance from cursor
        current_speed = min(self.max_speed, self.speed + (distance / 80))
        
        # Set target position with lag
        if distance > self.movement_lag:
            self.target_x = mouse_pos[0] - (dx / distance) * self.movement_lag
            self.target_y = mouse_pos[1] - (dy / distance) * self.movement_lag
        else:
            self.target_x, self.target_y = mouse_pos
            
        # Move head toward target
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance_to_target = max(1, math.sqrt(dx * dx + dy * dy))
        
        if distance_to_target > 1:
            self.x += (dx / distance_to_target) * current_speed
            self.y += (dy / distance_to_target) * current_speed
            
        # Update spine segments
        prev_x, prev_y = self.x, self.y
        for i, segment in enumerate(self.segments):
            # Calculate direction to previous segment
            dx = prev_x - segment['x']
            dy = prev_y - segment['y']
            distance = max(1, math.sqrt(dx * dx + dy * dy))
            
            # Move segment if it's too far from the previous one
            if distance > self.segment_spacing:
                segment_speed = current_speed * (0.95 - (i * 0.01))  # Segments get slower toward tail
                segment['x'] += (dx / distance) * segment_speed
                segment['y'] += (dy / distance) * segment_speed
                
            prev_x, prev_y = segment['x'], segment['y']
            
        # Update leg animations
        is_moving = distance_to_target > 2
        for i in range(self.leg_count):
            if is_moving:
                # Animate legs when moving
                self.leg_angles[i] += self.leg_animation_speeds[i] * (1 if i % 2 == 0 else -1)
                if abs(self.leg_angles[i]) > 0.8:
                    self.leg_angles[i] = 0.8 if self.leg_angles[i] > 0 else -0.8
                    self.leg_animation_speeds[i] *= -1
            else:
                # Return legs to neutral position when stationary
                self.leg_angles[i] *= 0.9
    
    def draw(self, screen):
        # Draw the spine segments
        for i, segment in enumerate(self.segments):
            # Draw spine segment
            pygame.draw.circle(screen, BONE_COLOR, (int(segment['x']), int(segment['y'])), int(segment['size']))
            
            # Draw connections between spine segments
            if i > 0:
                prev_segment = self.segments[i-1]
                pygame.draw.line(screen, BONE_COLOR, 
                                (int(prev_segment['x']), int(prev_segment['y'])),
                                (int(segment['x']), int(segment['y'])), 2)
            
            # Draw legs at specific spine segments
            leg_spacing = self.num_segments // (self.leg_count + 1)
            if (i + 1) % leg_spacing == 0 and (i + 1) // leg_spacing <= self.leg_count:
                leg_idx = (i + 1) // leg_spacing - 1
                
                # Calculate leg angles based on spine direction
                if i > 0:
                    prev_segment = self.segments[i-1]
                    dx = segment['x'] - prev_segment['x']
                    dy = segment['y'] - prev_segment['y']
                    spine_angle = math.atan2(dy, dx)
                else:
                    dx = segment['x'] - self.x
                    dy = segment['y'] - self.y
                    spine_angle = math.atan2(dy, dx)
                
                # Left leg
                left_leg_angle = spine_angle + (math.pi/2) + self.leg_angles[leg_idx]
                left_leg_x1 = segment['x']
                left_leg_y1 = segment['y']
                
                # Upper segment of leg
                left_upper_x = left_leg_x1 + math.cos(left_leg_angle) * (self.leg_length * 0.6)
                left_upper_y = left_leg_y1 + math.sin(left_leg_angle) * (self.leg_length * 0.6)
                
                # Lower segment (foot)
                left_foot_angle = left_leg_angle + (0.7 if leg_idx % 2 == 0 else -0.3)
                left_foot_x = left_upper_x + math.cos(left_foot_angle) * (self.leg_length * 0.4)
                left_foot_y = left_upper_y + math.sin(left_foot_angle) * (self.leg_length * 0.4)
                
                # Draw left leg bones
                pygame.draw.line(screen, BONE_COLOR, 
                                (int(left_leg_x1), int(left_leg_y1)),
                                (int(left_upper_x), int(left_upper_y)), 2)
                pygame.draw.line(screen, BONE_COLOR,
                                (int(left_upper_x), int(left_upper_y)),
                                (int(left_foot_x), int(left_foot_y)), 2)
                
                # Draw foot with small lines
                toes_angle_spread = 0.8
                toe_length = 5
                for toe in range(3):
                    toe_angle = left_foot_angle + ((toe - 1) * toes_angle_spread/2)
                    toe_x = left_foot_x + math.cos(toe_angle) * toe_length
                    toe_y = left_foot_y + math.sin(toe_angle) * toe_length
                    pygame.draw.line(screen, BONE_COLOR,
                                    (int(left_foot_x), int(left_foot_y)),
                                    (int(toe_x), int(toe_y)), 1)
                
                # Right leg
                right_leg_angle = spine_angle - (math.pi/2) - self.leg_angles[leg_idx]
                right_leg_x1 = segment['x']
                right_leg_y1 = segment['y'] 
                
                # Upper segment of leg
                right_upper_x = right_leg_x1 + math.cos(right_leg_angle) * (self.leg_length * 0.6)
                right_upper_y = right_leg_y1 + math.sin(right_leg_angle) * (self.leg_length * 0.6)
                
                # Lower segment (foot)
                right_foot_angle = right_leg_angle - (0.7 if leg_idx % 2 == 0 else -0.3)
                right_foot_x = right_upper_x + math.cos(right_foot_angle) * (self.leg_length * 0.4)
                right_foot_y = right_upper_y + math.sin(right_foot_angle) * (self.leg_length * 0.4)
                
                # Draw right leg bones
                pygame.draw.line(screen, BONE_COLOR, 
                                (int(right_leg_x1), int(right_leg_y1)),
                                (int(right_upper_x), int(right_upper_y)), 2)
                pygame.draw.line(screen, BONE_COLOR,
                                (int(right_upper_x), int(right_upper_y)),
                                (int(right_foot_x), int(right_foot_y)), 2)
                
                # Draw toes
                for toe in range(3):
                    toe_angle = right_foot_angle - ((toe - 1) * toes_angle_spread/2)
                    toe_x = right_foot_x + math.cos(toe_angle) * toe_length
                    toe_y = right_foot_y + math.sin(toe_angle) * toe_length
                    pygame.draw.line(screen, BONE_COLOR,
                                    (int(right_foot_x), int(right_foot_y)),
                                    (int(toe_x), int(toe_y)), 1)
        
        # Draw head (skull)
        # Calculate direction for head orientation
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        head_angle = math.atan2(dy, dx)
        
        # Draw skull outline
        skull_length = self.head_size * 2
        skull_width = self.head_size * 1.5
        
        # Calculate skull points
        skull_front_x = self.x + math.cos(head_angle) * skull_length
        skull_front_y = self.y + math.sin(head_angle) * skull_length
        
        skull_left_x = self.x + math.cos(head_angle + math.pi/2) * (skull_width/2)
        skull_left_y = self.y + math.sin(head_angle + math.pi/2) * (skull_width/2)
        
        skull_right_x = self.x + math.cos(head_angle - math.pi/2) * (skull_width/2)
        skull_right_y = self.y + math.sin(head_angle - math.pi/2) * (skull_width/2)
        
        # Draw skull
        pygame.draw.circle(screen, BONE_COLOR, (int(self.x), int(self.y)), self.head_size)
        pygame.draw.polygon(screen, BONE_COLOR, [
            (int(skull_front_x), int(skull_front_y)),
            (int(skull_left_x), int(skull_left_y)),
            (int(skull_right_x), int(skull_right_y))
        ])
        
        # Draw eye sockets
        eye_offset = self.head_size * 0.6
        eye_left_x = self.x + math.cos(head_angle + math.pi/4) * eye_offset
        eye_left_y = self.y + math.sin(head_angle + math.pi/4) * eye_offset
        
        eye_right_x = self.x + math.cos(head_angle - math.pi/4) * eye_offset
        eye_right_y = self.y + math.sin(head_angle - math.pi/4) * eye_offset
        
        pygame.draw.circle(screen, BLACK, (int(eye_left_x), int(eye_left_y)), self.eye_size)
        pygame.draw.circle(screen, BLACK, (int(eye_right_x), int(eye_right_y)), self.eye_size)

def main():
    clock = pygame.time.Clock()
    
    # Create the reptile at the center of the screen
    reptile = SkeletalReptile(WIDTH // 2, HEIGHT // 2)
    
    # Keep actual mouse cursor visible
    pygame.mouse.set_visible(True)
    
    # Main game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
        
        # Get mouse position
        mouse_pos = pygame.mouse.get_pos()
        
        # Update reptile
        reptile.update(mouse_pos)
        
        # Draw everything
        screen.fill(BLACK)
        reptile.draw(screen)
        
        # Update the display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

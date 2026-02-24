import pygame
import math
import random
import os

# Set window position before initializing Pygame
os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'

# Initialize Pygame
print("Initializing Pygame...")
try:
    pygame.init()
    print("Pygame initialized successfully")
except Exception as e:
    print(f"Error initializing Pygame: {e}")
    exit(1)

# Initialize Pygame mixer
print("Initializing Pygame mixer...")
try:
    pygame.mixer.init()
    print("Pygame mixer initialized successfully")
except Exception as e:
    print(f"Error initializing Pygame mixer: {e}")

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
GRAVITY = 0.8
JUMP_STRENGTH = -15
DOUBLE_JUMP_STRENGTH = -12
PLAYER_SPEED = 5
DASH_SPEED = 15
DASH_DURATION = 10
DASH_COOLDOWN = 30
ENEMY_SPEED = 2
CHASING_ENEMY_SPEED = 3
FLYING_ENEMY_SPEED = 2
PROJECTILE_SPEED = 8
BOSS_PROJECTILE_SPEED = 6
SHOOT_COOLDOWN = 10
BOSS_SHOOT_COOLDOWN = 60
SHIELD_DURATION = 300

# Colors
WHITE = (255, 255, 255)
BLACK = (20, 20, 30)
RED = (220, 80, 80)
BLUE = (80, 150, 220)
GREEN = (100, 200, 100)
YELLOW = (255, 220, 100)
GRAY = (120, 120, 120)
DARK_GRAY = (60, 60, 60)
PURPLE = (150, 100, 200)
CYAN = (100, 200, 200)
NEON_PINK = (255, 105, 180)
NEON_BLUE = (0, 255, 255)
ORANGE = (255, 165, 0)

class Particle:
    def __init__(self, x, y, vel_x, vel_y, color, life):
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.color = color
        self.life = life
        self.max_life = life
    
    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_y += 0.2  # Gravity on particles
        self.life -= 1
    
    def draw(self, screen):
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))
            size = int(4 * (self.life / self.max_life))
            if size > 0:
                surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                color = (*self.color[:3], alpha)
                pygame.draw.circle(surface, color, (size, size), size)
                screen.blit(surface, (int(self.x) - size, int(self.y) - size))

class Projectile:
    def __init__(self, x, y, direction, color=CYAN):
        self.x = x
        self.y = y
        self.width = 8
        self.height = 4
        self.vel_x = (PROJECTILE_SPEED if color == CYAN else BOSS_PROJECTILE_SPEED) * direction
        self.color = color
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def update(self):
        self.x += self.vel_x
        self.rect.x = self.x
    
    def draw(self, screen, camera_x, camera_y):
        pygame.draw.rect(screen, self.color, 
                        (self.x - camera_x, self.y - camera_y, 
                         self.width, self.height))
        # Add glow effect
        glow_color = (*self.color[:3], 100)
        glow_surface = pygame.Surface((self.width + 4, self.height + 4), pygame.SRCALPHA)
        pygame.draw.rect(glow_surface, glow_color, (0, 0, self.width + 4, self.height + 4))
        screen.blit(glow_surface, (self.x - camera_x - 2, self.y - camera_y - 2))

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.double_jump_available = True
        self.dashing = 0
        self.dash_cooldown = 0
        self.speed_boost = 0
        self.shield = 0
        self.shoot_cooldown = 0
        self.facing_right = True
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.invincible = 0
    
    def update(self, platforms, game):
        keys = pygame.key.get_pressed()
        speed = PLAYER_SPEED * 2 if self.speed_boost > 0 else PLAYER_SPEED
        
        # Dash mechanic
        if self.dashing > 0:
            self.vel_x = DASH_SPEED * (1 if self.facing_right else -1)
            self.dashing -= 1
            # Dash particles
            if game.frame_count % 2 == 0:
                game.particles.append(Particle(
                    self.x + self.width // 2, self.y + self.height // 2,
                    -self.vel_x * 0.3 + random.uniform(-1, 1),
                    random.uniform(-2, 2),
                    NEON_BLUE, 20
                ))
        else:
            # Movement
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vel_x = max(self.vel_x - 1, -speed)
                self.facing_right = False
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vel_x = min(self.vel_x + 1, speed)
                self.facing_right = True
            else:
                self.vel_x *= 0.8
                if abs(self.vel_x) < 0.5:
                    self.vel_x = 0
        
        # Dash input
        if keys[pygame.K_LSHIFT] and self.dash_cooldown == 0 and self.dashing == 0 and abs(self.vel_x) > 0:
            self.dashing = DASH_DURATION
            self.dash_cooldown = DASH_COOLDOWN
            for _ in range(10):
                game.particles.append(Particle(
                    self.x + self.width // 2, self.y + self.height // 2,
                    -self.vel_x * 0.2 + random.uniform(-2, 2),
                    random.uniform(-3, 3),
                    NEON_BLUE, 25
                ))
        
        # Shooting
        if keys[pygame.K_LCTRL] and self.shoot_cooldown == 0:
            direction = 1 if self.facing_right else -1
            game.projectiles.append(Projectile(
                self.x + self.width // 2, self.y + self.height // 2 - 2,
                direction
            ))
            self.shoot_cooldown = SHOOT_COOLDOWN
            for _ in range(5):
                game.particles.append(Particle(
                    self.x + self.width // 2, self.y + self.height // 2,
                    direction * random.uniform(2, 4), random.uniform(-1, 1),
                    CYAN, 15
                ))
        
        # Gravity
        self.vel_y += GRAVITY
        if self.vel_y > 15:
            self.vel_y = 15
        
        # Horizontal collision
        self.x += self.vel_x
        self.rect.x = self.x
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vel_x > 0:
                    self.rect.right = platform.left
                    self.x = self.rect.x
                elif self.vel_x < 0:
                    self.rect.left = platform.right
                    self.x = self.rect.x
                self.vel_x = 0
        
        # Vertical collision
        self.y += self.vel_y
        self.rect.y = self.y
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vel_y > 0:
                    self.rect.bottom = platform.top
                    self.y = self.rect.y
                    self.on_ground = True
                    self.double_jump_available = True
                    self.vel_y = 0
                elif self.vel_y < 0:
                    self.rect.top = platform.bottom
                    self.y = self.rect.y
                    self.vel_y = 0
        
        # Update cooldowns
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.speed_boost > 0:
            self.speed_boost -= 1
        if self.shield > 0:
            self.shield -= 1
        if self.invincible > 0:
            self.invincible -= 1
    
    def jump(self):
        if self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False
        elif self.double_jump_available:
            self.vel_y = DOUBLE_JUMP_STRENGTH
            self.double_jump_available = False
    
    def draw(self, screen, camera_x, camera_y):
        x = self.x - camera_x
        y = self.y - camera_y
        
        # Shield effect
        if self.shield > 0:
            shield_alpha = int(150 + math.sin(pygame.time.get_ticks() * 0.01) * 50)
            shield_surface = pygame.Surface((self.width + 8, self.height + 8), pygame.SRCALPHA)
            pygame.draw.circle(shield_surface, (*CYAN, shield_alpha), 
                             (self.width // 2 + 4, self.height // 2 + 4), 
                             self.width // 2 + 4)
            screen.blit(shield_surface, (x - 4, y - 4))
        
        # Invincibility flash
        if self.invincible > 0 and self.invincible % 10 < 5:
            return
        
        # Player body
        color = BLUE if not self.speed_boost else ORANGE
        pygame.draw.rect(screen, color, (x, y, self.width, self.height))
        
        # Eyes
        eye_y = y + 6
        if self.facing_right:
            pygame.draw.circle(screen, WHITE, (x + 14, eye_y), 2)
        else:
            pygame.draw.circle(screen, WHITE, (x + 6, eye_y), 2)
        
        # Trail effect when dashing or speed boosted
        if self.dashing > 0 or self.speed_boost > 0:
            trail_alpha = 100 if self.dashing > 0 else 50
            trail_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.rect(trail_surface, (*color, trail_alpha), (0, 0, self.width, self.height))
            screen.blit(trail_surface, (x - self.vel_x * 2, y))

class Enemy:
    def __init__(self, x, y, patrol_start, patrol_end):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.vel_x = ENEMY_SPEED
        self.patrol_start = patrol_start
        self.patrol_end = patrol_end
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def update(self, platforms):
        self.x += self.vel_x
        if self.x <= self.patrol_start or self.x >= self.patrol_end:
            self.vel_x *= -1
        self.rect.x = self.x
    
    def draw(self, screen, camera_x, camera_y):
        x = self.x - camera_x
        y = self.y - camera_y
        pygame.draw.rect(screen, RED, (x, y, self.width, self.height))
        # Eyes
        pygame.draw.circle(screen, WHITE, (x + 6, y + 7), 2)
        pygame.draw.circle(screen, WHITE, (x + 14, y + 7), 2)

class ChasingEnemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.vel_y = 0
        self.on_ground = False
    
    def update(self, player, platforms):
        # Chase player
        if abs(player.x - self.x) < 400:
            if player.x > self.x:
                self.x += CHASING_ENEMY_SPEED
            else:
                self.x -= CHASING_ENEMY_SPEED
        
        # Gravity
        self.vel_y += GRAVITY
        if self.vel_y > 15:
            self.vel_y = 15
        
        self.y += self.vel_y
        self.rect.x = self.x
        self.rect.y = self.y
        
        # Platform collision
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vel_y > 0:
                    self.rect.bottom = platform.top
                    self.y = self.rect.y
                    self.on_ground = True
                    self.vel_y = 0
                elif self.vel_y < 0:
                    self.rect.top = platform.bottom
                    self.y = self.rect.y
                    self.vel_y = 0
    
    def draw(self, screen, camera_x, camera_y):
        x = self.x - camera_x
        y = self.y - camera_y
        pygame.draw.rect(screen, PURPLE, (x, y, self.width, self.height))
        # Angry eyes
        pygame.draw.circle(screen, WHITE, (x + 6, y + 7), 3)
        pygame.draw.circle(screen, WHITE, (x + 14, y + 7), 3)
        pygame.draw.circle(screen, RED, (x + 7, y + 7), 1)
        pygame.draw.circle(screen, RED, (x + 15, y + 7), 1)

class FlyingEnemy:
    def __init__(self, x, y, patrol_start_y, patrol_end_y):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.vel_y = FLYING_ENEMY_SPEED
        self.patrol_start_y = patrol_start_y
        self.patrol_end_y = patrol_end_y
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def update(self):
        self.y += self.vel_y
        if self.y <= self.patrol_start_y or self.y >= self.patrol_end_y:
            self.vel_y *= -1
        self.rect.y = self.y
    
    def draw(self, screen, camera_x, camera_y):
        x = self.x - camera_x
        y = self.y - camera_y
        pygame.draw.circle(screen, GREEN, (x + self.width // 2, y + self.height // 2), self.width // 2)
        # Wings
        wing_offset = int(math.sin(pygame.time.get_ticks() * 0.01) * 3)
        pygame.draw.circle(screen, (150, 255, 150), (x - 3, y + self.height // 2 + wing_offset), 4)
        pygame.draw.circle(screen, (150, 255, 150), (x + self.width + 3, y + self.height // 2 - wing_offset), 4)
        # Eyes
        pygame.draw.circle(screen, WHITE, (x + 8, y + 8), 2)
        pygame.draw.circle(screen, WHITE, (x + 12, y + 8), 2)

class Boss:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 60
        self.health = 30
        self.max_health = 30
        self.shoot_cooldown = 0
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.phase = 1
    
    def update(self, platforms, player, game):
        # Shoot at player
        if self.shoot_cooldown == 0:
            # Calculate direction to player
            dx = player.x - self.x
            dy = player.y - self.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance > 0:
                direction = 1 if dx > 0 else -1
                game.projectiles.append(Projectile(
                    self.x + self.width // 2, self.y + self.height // 2,
                    direction, NEON_PINK
                ))
                self.shoot_cooldown = BOSS_SHOOT_COOLDOWN
                
                # Phase 2: Shoot more projectiles
                if self.health < self.max_health // 2:
                    self.phase = 2
                    for angle in [-15, 15]:
                        offset_x = math.cos(math.radians(angle)) * 10
                        offset_y = math.sin(math.radians(angle)) * 10
                        game.projectiles.append(Projectile(
                            self.x + self.width // 2 + offset_x, 
                            self.y + self.height // 2 + offset_y,
                            direction, NEON_PINK
                        ))
        
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
    
    def draw(self, screen, camera_x, camera_y):
        x = self.x - camera_x
        y = self.y - camera_y
        
        # Boss body
        color = RED if self.phase == 1 else NEON_PINK
        pygame.draw.rect(screen, color, (x, y, self.width, self.height))
        
        # Angry face
        pygame.draw.rect(screen, WHITE, (x + 10, y + 15, 15, 10))
        pygame.draw.rect(screen, WHITE, (x + 35, y + 15, 15, 10))
        pygame.draw.rect(screen, BLACK, (x + 15, y + 40, 30, 5))
        
        # Health bar
        bar_width = self.width
        bar_height = 5
        health_percent = self.health / self.max_health
        pygame.draw.rect(screen, RED, (x, y - 10, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (x, y - 10, bar_width * health_percent, bar_height))
        
        # Phase 2 glow
        if self.phase == 2:
            glow_alpha = int(100 + math.sin(pygame.time.get_ticks() * 0.01) * 50)
            glow_surface = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*NEON_PINK, glow_alpha), (0, 0, self.width + 20, self.height + 20))
            screen.blit(glow_surface, (x - 10, y - 10))

class PowerUp:
    def __init__(self, x, y, power_type):
        self.x = x
        self.y = y
        self.width = 16
        self.height = 16
        self.power_type = power_type  # 'speed', 'shield', 'health'
        self.collected = False
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.float_offset = 0
    
    def update(self):
        self.float_offset = math.sin(pygame.time.get_ticks() * 0.005) * 5
    
    def draw(self, screen, camera_x, camera_y):
        if not self.collected:
            x = self.x - camera_x
            y = self.y - camera_y + self.float_offset
            
            color = YELLOW if self.power_type == 'speed' else CYAN if self.power_type == 'shield' else GREEN
            
            # Glow effect
            glow_alpha = int(100 + math.sin(pygame.time.get_ticks() * 0.01) * 50)
            glow_surface = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*color, glow_alpha), 
                             (self.width // 2 + 5, self.height // 2 + 5), self.width // 2 + 5)
            screen.blit(glow_surface, (x - 5, y - 5))
            
            # Power-up
            pygame.draw.circle(screen, color, (x + self.width // 2, y + self.height // 2), self.width // 2)
            
            # Symbol
            if self.power_type == 'speed':
                pygame.draw.polygon(screen, WHITE, [
                    (x + 4, y + 8), (x + 12, y + 4), (x + 12, y + 12)
                ])
            elif self.power_type == 'shield':
                pygame.draw.circle(screen, WHITE, (x + self.width // 2, y + self.height // 2), 4, 2)
            else:  # health
                pygame.draw.rect(screen, WHITE, (x + 6, y + 4, 2, 8))
                pygame.draw.rect(screen, WHITE, (x + 4, y + 6, 6, 2))

class Key:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 16
        self.height = 16
        self.collected = False
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.float_offset = 0
    
    def update(self):
        self.float_offset = math.sin(pygame.time.get_ticks() * 0.005) * 5
    
    def draw(self, screen, camera_x, camera_y):
        if not self.collected:
            x = self.x - camera_x
            y = self.y - camera_y + self.float_offset
            
            # Glow
            glow_alpha = int(150 + math.sin(pygame.time.get_ticks() * 0.01) * 100)
            glow_surface = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*YELLOW, glow_alpha), 
                             (self.width // 2 + 5, self.height // 2 + 5), self.width // 2 + 5)
            screen.blit(glow_surface, (x - 5, y - 5))
            
            # Key
            pygame.draw.circle(screen, YELLOW, (x + 4, y + 4), 3)
            pygame.draw.rect(screen, YELLOW, (x + 4, y + 7, 2, 8))
            pygame.draw.rect(screen, YELLOW, (x + 6, y + 11, 3, 2))
            pygame.draw.rect(screen, YELLOW, (x + 6, y + 13, 3, 2))

class Door:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 50
        self.locked = True
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def draw(self, screen, camera_x, camera_y):
        x = self.x - camera_x
        y = self.y - camera_y
        
        color = GRAY if self.locked else GREEN
        pygame.draw.rect(screen, color, (x, y, self.width, self.height))
        pygame.draw.rect(screen, DARK_GRAY, (x + 2, y + 2, self.width - 4, self.height - 4))
        
        # Lock/unlock indicator
        if self.locked:
            pygame.draw.circle(screen, RED, (x + self.width // 2, y + self.height // 2), 5)
        else:
            # Glow when unlocked
            glow_alpha = int(100 + math.sin(pygame.time.get_ticks() * 0.01) * 50)
            glow_surface = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*GREEN, glow_alpha), (0, 0, self.width + 10, self.height + 10))
            screen.blit(glow_surface, (x - 5, y - 5))

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Cyber Platformer 2X - Enhanced Edition")
        self.clock = pygame.time.Clock()
        self.frame_count = 0
        
        # Game state
        self.state = 'menu'  # 'menu', 'playing', 'tutorial', 'victory', 'game_over'
        self.selected_option = 0
        self.current_level = 0
        self.score = 0
        self.high_score = 0
        
        # Game objects
        self.player = None
        self.platforms = []
        self.enemies = []
        self.projectiles = []
        self.power_ups = []
        self.particles = []
        self.key = None
        self.door = None
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        
        # Tutorial
        self.tutorial_step = 0
        self.tutorial_messages = [
            "Use A/D or Arrow Keys to move",
            "Press SPACE to jump (double jump available!)",
            "Press SHIFT while moving to dash",
            "Press CTRL to shoot projectiles",
            "Collect power-ups for abilities",
            "Defeat the boss to get the key",
            "Unlock the door to complete the level!"
        ]
        
        # Level definitions
        self.levels = [
            self.create_level_1(),
            self.create_level_2(),
            self.create_level_3(),
        ]
        
        self.load_level(0)
    
    def create_level_1(self):
        """Tutorial level - basic mechanics"""
        return {
            'name': 'Level 1: The Beginning',
            'spawn': (100, 500),
            'platforms': [
                pygame.Rect(0, 600, 400, 40),
                pygame.Rect(500, 550, 200, 40),
                pygame.Rect(800, 500, 200, 40),
                pygame.Rect(1100, 450, 200, 40),
                pygame.Rect(1400, 400, 400, 40),
                pygame.Rect(0, 700, SCREEN_WIDTH * 3, 100),  # Floor
            ],
            'enemies': [
                ('enemy', 600, 530, 500, 700),
                ('flying', 900, 300, 250, 450),
            ],
            'power_ups': [
                ('speed', 550, 520),
                ('shield', 1450, 370),
            ],
            'boss': None,
            'door': (1700, 350),
        }
    
    def create_level_2(self):
        """Intermediate level - more enemies"""
        return {
            'name': 'Level 2: The Gauntlet',
            'spawn': (100, 500),
            'platforms': [
                pygame.Rect(0, 600, 300, 40),
                pygame.Rect(400, 550, 150, 40),
                pygame.Rect(650, 500, 150, 40),
                pygame.Rect(900, 450, 150, 40),
                pygame.Rect(1150, 400, 300, 40),
                pygame.Rect(1550, 350, 300, 40),
                pygame.Rect(0, 700, SCREEN_WIDTH * 3, 100),  # Floor
            ],
            'enemies': [
                ('enemy', 450, 530, 400, 550),
                ('enemy', 950, 430, 900, 1050),
                ('chasing', 700, 480),
                ('flying', 800, 200, 150, 400),
                ('flying', 1300, 200, 150, 400),
            ],
            'power_ups': [
                ('shield', 420, 520),
                ('speed', 920, 420),
            ],
            'boss': None,
            'door': (1800, 300),
        }
    
    def create_level_3(self):
        """Boss level"""
        return {
            'name': 'Level 3: The Boss',
            'spawn': (100, 500),
            'platforms': [
                pygame.Rect(0, 600, 400, 40),
                pygame.Rect(500, 600, 300, 40),
                pygame.Rect(900, 600, 400, 40),
                pygame.Rect(1400, 550, 300, 40),
                pygame.Rect(250, 450, 150, 40),
                pygame.Rect(650, 450, 150, 40),
                pygame.Rect(1050, 450, 150, 40),
                pygame.Rect(0, 700, SCREEN_WIDTH * 3, 100),  # Floor
            ],
            'enemies': [],
            'power_ups': [
                ('shield', 270, 420),
                ('speed', 670, 420),
                ('shield', 1070, 420),
            ],
            'boss': (1450, 500),
            'door': (1600, 500),
        }
    
    def load_level(self, level_index):
        """Load a level"""
        if level_index >= len(self.levels):
            self.state = 'victory'
            return
        
        level = self.levels[level_index]
        self.current_level = level_index
        
        # Reset player
        spawn_x, spawn_y = level['spawn']
        self.player = Player(spawn_x, spawn_y)
        
        # Load platforms
        self.platforms = level['platforms']
        
        # Load enemies
        self.enemies = []
        for enemy_data in level['enemies']:
            if enemy_data[0] == 'enemy':
                _, x, y, start, end = enemy_data
                self.enemies.append(Enemy(x, y, start, end))
            elif enemy_data[0] == 'chasing':
                _, x, y = enemy_data
                self.enemies.append(ChasingEnemy(x, y))
            elif enemy_data[0] == 'flying':
                _, x, y, start_y, end_y = enemy_data
                self.enemies.append(FlyingEnemy(x, y, start_y, end_y))
        
        # Load boss
        if level['boss']:
            boss_x, boss_y = level['boss']
            self.enemies.append(Boss(boss_x, boss_y))
        
        # Load power-ups
        self.power_ups = []
        for power_type, x, y in level['power_ups']:
            self.power_ups.append(PowerUp(x, y, power_type))
        
        # Load door
        door_x, door_y = level['door']
        self.door = Door(door_x, door_y)
        
        # Reset key
        self.key = None
        
        # Clear projectiles and particles
        self.projectiles = []
        self.particles = []
        
        # Reset camera
        self.camera_x = 0
        self.camera_y = 0
    
    def update_camera(self):
        """Update camera to follow player"""
        target_x = self.player.x - SCREEN_WIDTH // 3
        target_y = self.player.y - SCREEN_HEIGHT // 2
        
        self.camera_x += (target_x - self.camera_x) * 0.1
        self.camera_y += (target_y - self.camera_y) * 0.1
        
        # Keep camera in bounds
        self.camera_x = max(0, self.camera_x)
        self.camera_y = max(0, min(self.camera_y, 200))
    
    def handle_collisions(self):
        """Handle all game collisions"""
        # Player-enemy collision
        for enemy in self.enemies:
            if self.player.rect.colliderect(enemy.rect) and self.player.invincible == 0:
                if self.player.shield > 0:
                    self.player.shield = 0
                    self.player.invincible = 60
                    for _ in range(15):
                        self.particles.append(Particle(
                            self.player.x + self.player.width // 2, 
                            self.player.y + self.player.height // 2,
                            random.uniform(-3, 3), random.uniform(-3, 3),
                            CYAN, 25
                        ))
                else:
                    self.respawn_player()
        
        # Projectile collisions
        for projectile in self.projectiles[:]:
            # Projectile out of bounds
            if projectile.x < self.camera_x - 100 or projectile.x > self.camera_x + SCREEN_WIDTH + 100:
                self.projectiles.remove(projectile)
                continue
            
            # Player projectile hits enemy
            if projectile.color == CYAN:
                for enemy in self.enemies[:]:
                    if projectile.rect.colliderect(enemy.rect):
                        if isinstance(enemy, Boss):
                            enemy.health -= 1
                            for _ in range(10):
                                self.particles.append(Particle(
                                    enemy.x + enemy.width // 2, enemy.y + enemy.height // 2,
                                    random.uniform(-3, 3), random.uniform(-3, 3),
                                    NEON_PINK, 25
                                ))
                            if enemy.health <= 0:
                                self.enemies.remove(enemy)
                                self.score += 1000
                                for _ in range(30):
                                    self.particles.append(Particle(
                                        enemy.x + enemy.width // 2, enemy.y + enemy.height // 2,
                                        random.uniform(-5, 5), random.uniform(-5, 5),
                                        NEON_PINK, 40
                                    ))
                                # Drop key
                                self.key = Key(enemy.x + enemy.width // 2 - 8, enemy.y + enemy.height // 2 - 8)
                        else:
                            self.enemies.remove(enemy)
                            self.score += 100
                            for _ in range(8):
                                color = RED if isinstance(enemy, Enemy) else GREEN if isinstance(enemy, FlyingEnemy) else PURPLE
                                self.particles.append(Particle(
                                    enemy.x + enemy.width // 2, enemy.y + enemy.height // 2,
                                    random.uniform(-3, 3), random.uniform(-3, 3),
                                    color, 25
                                ))
                        if projectile in self.projectiles:
                            self.projectiles.remove(projectile)
                        break
            
            # Enemy projectile hits player
            elif projectile.color == NEON_PINK:
                if projectile.rect.colliderect(self.player.rect) and self.player.invincible == 0:
                    if self.player.shield > 0:
                        self.player.shield = 0
                        self.player.invincible = 60
                        for _ in range(15):
                            self.particles.append(Particle(
                                self.player.x + self.player.width // 2, 
                                self.player.y + self.player.height // 2,
                                random.uniform(-3, 3), random.uniform(-3, 3),
                                CYAN, 25
                            ))
                    else:
                        self.respawn_player()
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)
        
        # Power-up collection
        for power_up in self.power_ups:
            if not power_up.collected and self.player.rect.colliderect(power_up.rect):
                power_up.collected = True
                self.score += 50
                if power_up.power_type == 'speed':
                    self.player.speed_boost = 300
                elif power_up.power_type == 'shield':
                    self.player.shield = SHIELD_DURATION
                
                for _ in range(15):
                    color = YELLOW if power_up.power_type == 'speed' else CYAN
                    self.particles.append(Particle(
                        power_up.x + power_up.width // 2, power_up.y + power_up.height // 2,
                        random.uniform(-3, 3), random.uniform(-3, 3),
                        color, 30
                    ))
        
        # Key collection
        if self.key and not self.key.collected and self.player.rect.colliderect(self.key.rect):
            self.key.collected = True
            self.door.locked = False
            self.score += 500
            for _ in range(20):
                self.particles.append(Particle(
                    self.key.x + self.key.width // 2, self.key.y + self.key.height // 2,
                    random.uniform(-4, 4), random.uniform(-4, 4),
                    YELLOW, 35
                ))
        
        # Door entry
        if not self.door.locked and self.player.rect.colliderect(self.door.rect):
            self.current_level += 1
            if self.current_level >= len(self.levels):
                self.state = 'victory'
                if self.score > self.high_score:
                    self.high_score = self.score
            else:
                self.load_level(self.current_level)
    
    def respawn_player(self):
        """Respawn player at level start"""
        level = self.levels[self.current_level]
        spawn_x, spawn_y = level['spawn']
        self.player.x = spawn_x
        self.player.y = spawn_y
        self.player.vel_x = 0
        self.player.vel_y = 0
        self.player.invincible = 120
        self.score = max(0, self.score - 100)
        
        for _ in range(20):
            self.particles.append(Particle(
                self.player.x + self.player.width // 2, 
                self.player.y + self.player.height // 2,
                random.uniform(-4, 4), random.uniform(-4, 4),
                BLUE, 30
            ))
    
    def draw_menu(self):
        """Draw main menu"""
        self.screen.fill(BLACK)
        
        # Title with glow
        title_font = pygame.font.Font(None, 72)
        title = title_font.render("CYBER PLATFORMER 2X", True, NEON_BLUE)
        title_glow = title_font.render("CYBER PLATFORMER 2X", True, (*NEON_BLUE, 100))
        
        glow_x = SCREEN_WIDTH // 2 - title.get_width() // 2
        glow_y = 100
        self.screen.blit(title_glow, (glow_x - 2, glow_y - 2))
        self.screen.blit(title_glow, (glow_x + 2, glow_y + 2))
        self.screen.blit(title, (glow_x, glow_y))
        
        # Subtitle
        subtitle_font = pygame.font.Font(None, 32)
        subtitle = subtitle_font.render("Enhanced Edition", True, CYAN)
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 170))
        
        # Menu options
        menu_font = pygame.font.Font(None, 48)
        options = ["Start Game", "Quit"]
        
        for i, option in enumerate(options):
            color = YELLOW if i == self.selected_option else WHITE
            text = menu_font.render(option, True, color)
            y = 300 + i * 60
            x = SCREEN_WIDTH // 2 - text.get_width() // 2
            
            if i == self.selected_option:
                # Selection indicator
                pygame.draw.polygon(self.screen, YELLOW, [
                    (x - 30, y + 20), (x - 20, y + 15), (x - 20, y + 25)
                ])
            
            self.screen.blit(text, (x, y))
        
        # High score
        if self.high_score > 0:
            score_font = pygame.font.Font(None, 36)
            score_text = score_font.render(f"High Score: {self.high_score}", True, GREEN)
            self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 500))
        
        # Controls
        controls_font = pygame.font.Font(None, 24)
        controls = [
            "Controls:",
            "Arrow Keys/WASD - Move",
            "SPACE - Jump",
            "SHIFT - Dash",
            "CTRL - Shoot",
        ]
        
        y_offset = 580
        for line in controls:
            text = controls_font.render(line, True, GRAY)
            self.screen.blit(text, (20, y_offset))
            y_offset += 25
        
        # Animated background particles
        for _ in range(2):
            self.particles.append(Particle(
                random.randint(0, SCREEN_WIDTH), 0,
                random.uniform(-0.5, 0.5), random.uniform(1, 3),
                random.choice([NEON_BLUE, CYAN, PURPLE]), 100
            ))
        
        for particle in self.particles[:]:
            particle.update()
            particle.draw(self.screen)
            if particle.life <= 0 or particle.y > SCREEN_HEIGHT:
                self.particles.remove(particle)
    
    def draw_game(self):
        """Draw game scene"""
        self.screen.fill(BLACK)
        
        # Draw platforms
        for platform in self.platforms:
            pygame.draw.rect(self.screen, GRAY, 
                           (platform.x - self.camera_x, platform.y - self.camera_y, 
                            platform.width, platform.height))
            pygame.draw.rect(self.screen, DARK_GRAY, 
                           (platform.x - self.camera_x, platform.y - self.camera_y, 
                            platform.width, platform.height), 2)
        
        # Draw door
        self.door.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw key
        if self.key:
            self.key.update()
            self.key.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw power-ups
        for power_up in self.power_ups:
            power_up.update()
            power_up.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw projectiles
        for projectile in self.projectiles:
            projectile.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw player
        self.player.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw particles
        for particle in self.particles[:]:
            particle.update()
            particle.draw(self.screen)
            if particle.life <= 0:
                self.particles.remove(particle)
        
        # Draw HUD
        hud_font = pygame.font.Font(None, 32)
        
        # Score
        score_text = hud_font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Level name
        level_text = hud_font.render(self.levels[self.current_level]['name'], True, CYAN)
        self.screen.blit(level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2, 10))
        
        # Abilities status
        y_offset = 50
        if self.player.shield > 0:
            shield_text = hud_font.render(f"Shield: {self.player.shield // 60}s", True, CYAN)
            self.screen.blit(shield_text, (10, y_offset))
            y_offset += 30
        
        if self.player.speed_boost > 0:
            speed_text = hud_font.render(f"Speed: {self.player.speed_boost // 60}s", True, YELLOW)
            self.screen.blit(speed_text, (10, y_offset))
            y_offset += 30
        
        # Dash cooldown indicator
        if self.player.dash_cooldown > 0:
            cooldown_percent = self.player.dash_cooldown / DASH_COOLDOWN
            bar_width = 100
            pygame.draw.rect(self.screen, DARK_GRAY, (10, SCREEN_HEIGHT - 30, bar_width, 20))
            pygame.draw.rect(self.screen, NEON_BLUE, (10, SCREEN_HEIGHT - 30, bar_width * (1 - cooldown_percent), 20))
            dash_text = pygame.font.Font(None, 20).render("Dash", True, WHITE)
            self.screen.blit(dash_text, (15, SCREEN_HEIGHT - 28))
    
    def draw_victory(self):
        """Draw victory screen"""
        self.screen.fill(BLACK)
        
        # Victory title
        title_font = pygame.font.Font(None, 72)
        title = title_font.render("VICTORY!", True, YELLOW)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 200))
        
        # Final score
        score_font = pygame.font.Font(None, 48)
        score_text = score_font.render(f"Final Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 300))
        
        if self.score > self.high_score:
            new_high = score_font.render("NEW HIGH SCORE!", True, GREEN)
            self.screen.blit(new_high, (SCREEN_WIDTH // 2 - new_high.get_width() // 2, 360))
        
        # Return prompt
        prompt_font = pygame.font.Font(None, 32)
        prompt = prompt_font.render("Press ESC to return to menu", True, GRAY)
        self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 500))
        
        # Celebration particles
        for _ in range(3):
            self.particles.append(Particle(
                random.randint(0, SCREEN_WIDTH), 0,
                random.uniform(-2, 2), random.uniform(2, 5),
                random.choice([YELLOW, GREEN, CYAN, NEON_BLUE]), 80
            ))
        
        for particle in self.particles[:]:
            particle.update()
            particle.draw(self.screen)
            if particle.life <= 0:
                self.particles.remove(particle)
    
    def run(self):
        """Main game loop"""
        running = True
        while running:
            self.frame_count += 1
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if self.state == 'menu':
                        if event.key == pygame.K_UP:
                            self.selected_option = (self.selected_option - 1) % 2
                        elif event.key == pygame.K_DOWN:
                            self.selected_option = (self.selected_option + 1) % 2
                        elif event.key == pygame.K_RETURN:
                            if self.selected_option == 0:
                                self.score = 0
                                self.load_level(0)
                                self.state = 'playing'
                            elif self.selected_option == 1:
                                running = False
                    
                    elif self.state == 'playing':
                        if event.key == pygame.K_SPACE:
                            self.player.jump()
                        elif event.key == pygame.K_ESCAPE:
                            self.state = 'menu'
                            self.particles = []
                    
                    elif self.state == 'victory':
                        if event.key == pygame.K_ESCAPE:
                            self.state = 'menu'
                            self.particles = []
            
            # Game logic
            if self.state == 'menu':
                self.draw_menu()
            
            elif self.state == 'playing':
                # Update game objects
                self.player.update(self.platforms, self)
                
                for enemy in self.enemies:
                    if isinstance(enemy, Boss):
                        enemy.update(self.platforms, self.player, self)
                    elif isinstance(enemy, ChasingEnemy):
                        enemy.update(self.player, self.platforms)
                    elif isinstance(enemy, FlyingEnemy):
                        enemy.update()
                    else:
                        enemy.update(self.platforms)
                
                for projectile in self.projectiles:
                    projectile.update()
                
                self.handle_collisions()
                self.update_camera()
                self.draw_game()
            
            elif self.state == 'victory':
                self.draw_victory()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    print("Starting Cyber Platformer 2X...")
    game = Game()
    game.run()
    print("Game ended. Thanks for playing!")
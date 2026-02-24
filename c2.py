import pygame
import math
import random

# Initialize Pygame
print("Initializing game...")
pygame.init()

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
FLYING_ENEMY_SPEED = 2
PROJECTILE_SPEED = 8
BOSS_PROJECTILE_SPEED = 6
SHOOT_COOLDOWN = 10
BOSS_SHOOT_COOLDOWN = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (30, 30, 30)
RED = (220, 80, 80)
BLUE = (80, 150, 220)
GREEN = (100, 200, 100)
YELLOW = (255, 220, 100)
GRAY = (120, 120, 120)
DARK_GRAY = (60, 60, 60)
PURPLE = (150, 100, 200)
CYAN = (100, 200, 200)
NEON_PINK = (255, 105, 180)
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
        self.vel_y += 0.2  # Gravity
        self.life -= 1
    
    def draw(self, screen):
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))
            size = max(1, int(3 * (self.life / self.max_life)))
            surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            color = (*self.color[:3], alpha)
            pygame.draw.circle(surface, color, (size, size), size)
            screen.blit(surface, (int(self.x) - size, int(self.y) - size))

class Projectile:
    def __init__(self, x, y, direction, color=CYAN):
        self.x = x
        self.y = y
        self.width = 10
        self.height = 5
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
        # Glow effect
        glow_surface = pygame.Surface((self.width + 6, self.height + 6), pygame.SRCALPHA)
        glow_color = (*self.color[:3], 80)
        pygame.draw.rect(glow_surface, glow_color, (0, 0, self.width + 6, self.height + 6))
        screen.blit(glow_surface, (self.x - camera_x - 3, self.y - camera_y - 3))

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
        self.shoot_cooldown = 0
        self.facing_right = True
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.invincible_timer = 0
    
    def update(self, platforms, game):
        keys = pygame.key.get_pressed()
        speed = PLAYER_SPEED * 2 if self.speed_boost > 0 else PLAYER_SPEED
        
        # Dash
        if self.dashing > 0:
            self.vel_x = DASH_SPEED * (1 if self.facing_right else -1)
            self.dashing -= 1
            if game.frame_count % 3 == 0:
                game.particles.append(Particle(
                    self.x + self.width // 2, self.y + self.height // 2,
                    -self.vel_x * 0.3 + random.uniform(-1, 1),
                    random.uniform(-2, 2),
                    CYAN, 20
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
        if keys[pygame.K_LSHIFT] and self.dash_cooldown == 0 and self.dashing == 0:
            self.dashing = DASH_DURATION
            self.dash_cooldown = DASH_COOLDOWN
            for _ in range(8):
                game.particles.append(Particle(
                    self.x + self.width // 2, self.y + self.height // 2,
                    random.uniform(-3, 3), random.uniform(-3, 3),
                    CYAN, 25
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
        self.vel_y = min(self.vel_y, 15)
        
        # Horizontal movement
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
        
        # Vertical movement
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
        
        # Update timers
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.speed_boost > 0:
            self.speed_boost -= 1
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
    
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
        
        # Invincibility flash
        if self.invincible_timer > 0 and self.invincible_timer % 10 < 5:
            return
        
        # Bounce animation
        bounce = abs(math.sin(pygame.time.get_ticks() * 0.01)) * 2
        
        # Player body
        color = ORANGE if self.speed_boost > 0 else BLUE
        pygame.draw.rect(screen, color, (x, y + bounce, self.width, self.height))
        
        # Eyes
        eye_y = y + 6 + bounce
        if self.facing_right:
            pygame.draw.circle(screen, WHITE, (x + 14, eye_y), 2)
        else:
            pygame.draw.circle(screen, WHITE, (x + 6, eye_y), 2)
        
        # Gun
        gun_x = (x + self.width) if self.facing_right else (x - 4)
        pygame.draw.rect(screen, GRAY, (gun_x, y + bounce + 6, 4, 4))
        
        # Dash trail
        if self.dashing > 0:
            pygame.draw.line(screen, CYAN, 
                           (x, y + self.height // 2 + bounce),
                           (x - self.vel_x, y + self.height // 2 + bounce), 3)

class Enemy:
    def __init__(self, x, y, patrol_distance):
        self.start_x = x
        self.x = x
        self.y = y
        self.width = 18
        self.height = 18
        self.patrol_distance = patrol_distance
        self.direction = 1
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def update(self, platforms):
        self.x += ENEMY_SPEED * self.direction
        if abs(self.x - self.start_x) >= self.patrol_distance:
            self.direction *= -1
        self.rect.x = self.x
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.direction > 0:
                    self.rect.right = platform.left
                    self.x = self.rect.x
                else:
                    self.rect.left = platform.right
                    self.x = self.rect.x
                self.direction *= -1
    
    def draw(self, screen, camera_x, camera_y):
        wobble = math.sin(pygame.time.get_ticks() * 0.02) * 1
        pygame.draw.rect(screen, RED, 
                        (self.x - camera_x, self.y - camera_y + wobble, 
                         self.width, self.height))
        # Eyes
        pygame.draw.circle(screen, YELLOW, 
                          (int(self.x - camera_x + 5), int(self.y - camera_y + 5 + wobble)), 2)
        pygame.draw.circle(screen, YELLOW, 
                          (int(self.x - camera_x + 13), int(self.y - camera_y + 5 + wobble)), 2)

class FlyingEnemy:
    def __init__(self, x, y, patrol_height):
        self.start_y = y
        self.x = x
        self.y = y
        self.width = 18
        self.height = 18
        self.patrol_height = patrol_height
        self.direction = 1
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def update(self, platforms=None):
        self.y += FLYING_ENEMY_SPEED * self.direction
        if abs(self.y - self.start_y) >= self.patrol_height:
            self.direction *= -1
        self.rect.y = self.y
    
    def draw(self, screen, camera_x, camera_y):
        wobble = math.sin(pygame.time.get_ticks() * 0.03) * 2
        pygame.draw.circle(screen, GREEN, 
                          (int(self.x - camera_x + self.width // 2), 
                           int(self.y - camera_y + self.height // 2 + wobble)), 
                          self.width // 2)
        # Eyes
        pygame.draw.circle(screen, WHITE, 
                          (int(self.x - camera_x + 6), int(self.y - camera_y + 7 + wobble)), 2)
        pygame.draw.circle(screen, WHITE, 
                          (int(self.x - camera_x + 12), int(self.y - camera_y + 7 + wobble)), 2)

class Boss:
    def __init__(self, x, y, patrol_distance):
        self.start_x = x
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.patrol_distance = patrol_distance
        self.direction = 1
        self.health = 20
        self.max_health = 20
        self.shoot_cooldown = BOSS_SHOOT_COOLDOWN
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.name = "BOSS"
    
    def update(self, platforms, player, game):
        # Movement
        self.x += ENEMY_SPEED * self.direction
        if abs(self.x - self.start_x) >= self.patrol_distance:
            self.direction *= -1
        self.rect.x = self.x
        
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.direction > 0:
                    self.rect.right = platform.left
                    self.x = self.rect.x
                else:
                    self.rect.left = platform.right
                    self.x = self.rect.x
                self.direction *= -1
        
        # Shooting
        if self.shoot_cooldown <= 0:
            player_center_x = player.x + player.width // 2
            direction = 1 if player_center_x > self.x else -1
            game.projectiles.append(Projectile(
                self.x + self.width // 2, self.y + self.height // 2 - 2,
                direction, color=RED
            ))
            self.shoot_cooldown = BOSS_SHOOT_COOLDOWN
            for _ in range(5):
                game.particles.append(Particle(
                    self.x + self.width // 2, self.y + self.height // 2,
                    direction * random.uniform(1, 3), random.uniform(-1, 1),
                    RED, 20
                ))
        else:
            self.shoot_cooldown -= 1
    
    def draw(self, screen, camera_x, camera_y):
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.01)) * 2
        
        # Boss body
        pygame.draw.rect(screen, RED, 
                        (self.x - camera_x, self.y - camera_y, 
                         self.width + pulse, self.height + pulse))
        
        # Eyes
        pygame.draw.circle(screen, YELLOW, 
                          (int(self.x - camera_x + 10), int(self.y - camera_y + 10)), 4)
        pygame.draw.circle(screen, YELLOW, 
                          (int(self.x - camera_x + 30), int(self.y - camera_y + 10)), 4)
        
        # Health bar
        bar_width = self.width
        bar_height = 5
        health_ratio = self.health / self.max_health
        pygame.draw.rect(screen, DARK_GRAY, 
                        (self.x - camera_x, self.y - camera_y - 10, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, 
                        (self.x - camera_x, self.y - camera_y - 10, 
                         bar_width * health_ratio, bar_height))

class PowerUp:
    def __init__(self, x, y, type="speed"):
        self.x = x
        self.y = y
        self.width = 16
        self.height = 16
        self.type = type
        self.collected = False
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def draw(self, screen, camera_x, camera_y):
        if not self.collected:
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.01)) * 4 + 8
            float_y = math.sin(pygame.time.get_ticks() * 0.005) * 3
            pygame.draw.circle(screen, PURPLE, 
                              (int(self.x - camera_x + self.width // 2), 
                               int(self.y - camera_y + self.height // 2 + float_y)), int(pulse))
            pygame.draw.circle(screen, WHITE, 
                              (int(self.x - camera_x + self.width // 2), 
                               int(self.y - camera_y + self.height // 2 + float_y)), 5)

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 16
        self.height = 16
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.collected = False
    
    def draw(self, screen, camera_x, camera_y):
        if not self.collected:
            time = pygame.time.get_ticks()
            scale = abs(math.sin(time * 0.01))
            width = int(self.width * scale)
            if width > 2:
                pygame.draw.ellipse(screen, YELLOW, 
                                   (self.x - camera_x + (self.width - width) // 2, 
                                    self.y - camera_y, width, self.height))

class Spike:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def draw(self, screen, camera_x, camera_y):
        points = [
            (self.x - camera_x, self.y + self.height - camera_y),
            (self.x + self.width // 2 - camera_x, self.y - camera_y),
            (self.x + self.width - camera_x, self.y + self.height - camera_y)
        ]
        pygame.draw.polygon(screen, GRAY, points)
        pygame.draw.polygon(screen, WHITE, points, 2)

class Key:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 16
        self.height = 16
        self.collected = False
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def draw(self, screen, camera_x, camera_y):
        if not self.collected:
            float_y = math.sin(pygame.time.get_ticks() * 0.005) * 5
            # Glow
            glow_alpha = int(150 + math.sin(pygame.time.get_ticks() * 0.01) * 100)
            glow_surface = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*YELLOW, glow_alpha), 
                             (self.width // 2 + 5, self.height // 2 + 5), 
                             self.width // 2 + 5)
            screen.blit(glow_surface, (self.x - camera_x - 5, self.y - camera_y + float_y - 5))
            
            # Key shape
            pygame.draw.circle(screen, YELLOW, 
                             (self.x - camera_x + 4, self.y - camera_y + 4 + float_y), 3)
            pygame.draw.rect(screen, YELLOW, 
                           (self.x - camera_x + 4, self.y - camera_y + 7 + float_y, 2, 8))

class Door:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 50
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def draw(self, screen, camera_x, camera_y):
        # Glow effect
        glow_alpha = int(100 + math.sin(pygame.time.get_ticks() * 0.01) * 50)
        glow_surface = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
        pygame.draw.rect(glow_surface, (*GREEN, glow_alpha), 
                        (0, 0, self.width + 10, self.height + 10))
        screen.blit(glow_surface, (self.x - camera_x - 5, self.y - camera_y - 5))
        
        # Door
        pygame.draw.rect(screen, GREEN, 
                        (self.x - camera_x, self.y - camera_y, self.width, self.height))
        pygame.draw.rect(screen, DARK_GRAY, 
                        (self.x - camera_x + 2, self.y - camera_y + 2, 
                         self.width - 4, self.height - 4))

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Cyber Platformer - Your Epic Game!")
        self.clock = pygame.time.Clock()
        self.frame_count = 0
        
        # Game state
        self.state = 'menu'  # menu, playing, game_over, victory
        self.current_level = 0
        self.coins_collected = 0
        self.total_coins = 0
        
        # Game objects
        self.player = None
        self.platforms = []
        self.enemies = []
        self.projectiles = []
        self.power_ups = []
        self.coins = []
        self.spikes = []
        self.particles = []
        self.key = None
        self.door = None
        self.exit_rect = None
        self.boss_defeated = False
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        
        # Menu
        self.selected_option = 0
        
        # Create levels
        self.levels = self.create_levels()
    
    def create_levels(self):
        levels = []
        
        # Level 1 - Tutorial
        levels.append({
            'name': 'Level 1: The Beginning',
            'spawn': (100, 500),
            'platforms': [
                pygame.Rect(0, 600, 400, 40),
                pygame.Rect(500, 550, 200, 40),
                pygame.Rect(800, 500, 300, 40),
                pygame.Rect(1200, 450, 300, 40),
                pygame.Rect(0, 700, 2000, 100),
            ],
            'enemies': [
                ('enemy', 600, 532, 100),
            ],
            'flying_enemies': [],
            'power_ups': [
                PowerUp(550, 520, 'speed'),
            ],
            'coins': [
                Coin(250, 550),
                Coin(650, 500),
                Coin(950, 450),
            ],
            'spikes': [],
            'boss': None,
            'exit': pygame.Rect(1450, 400, 30, 50),
        })
        
        # Level 2 - More enemies
        levels.append({
            'name': 'Level 2: The Challenge',
            'spawn': (100, 500),
            'platforms': [
                pygame.Rect(0, 600, 300, 40),
                pygame.Rect(400, 550, 150, 40),
                pygame.Rect(650, 500, 150, 40),
                pygame.Rect(900, 450, 150, 40),
                pygame.Rect(1150, 400, 300, 40),
                pygame.Rect(0, 700, 2000, 100),
            ],
            'enemies': [
                ('enemy', 450, 532, 100),
                ('enemy', 950, 432, 100),
            ],
            'flying_enemies': [
                ('flying', 750, 300, 150),
            ],
            'power_ups': [
                PowerUp(420, 520, 'speed'),
            ],
            'coins': [
                Coin(200, 550),
                Coin(475, 500),
                Coin(725, 450),
                Coin(1000, 400),
            ],
            'spikes': [
                Spike(550, 580),
                Spike(800, 530),
            ],
            'boss': None,
            'exit': pygame.Rect(1400, 350, 30, 50),
        })
        
        # Level 3 - Boss level
        levels.append({
            'name': 'Level 3: The Boss',
            'spawn': (100, 500),
            'platforms': [
                pygame.Rect(0, 600, 400, 40),
                pygame.Rect(500, 600, 300, 40),
                pygame.Rect(900, 600, 400, 40),
                pygame.Rect(250, 450, 150, 40),
                pygame.Rect(650, 450, 150, 40),
                pygame.Rect(1050, 450, 150, 40),
                pygame.Rect(0, 700, 2000, 100),
            ],
            'enemies': [],
            'flying_enemies': [],
            'power_ups': [
                PowerUp(270, 420, 'speed'),
                PowerUp(670, 420, 'speed'),
            ],
            'coins': [
                Coin(150, 550),
                Coin(350, 400),
                Coin(700, 400),
                Coin(1100, 400),
            ],
            'spikes': [],
            'boss': ('boss', 1100, 560, 150),
            'exit': pygame.Rect(1250, 560, 30, 50),
        })
        
        # Level 4 - Sky Jumps
        levels.append({
            'name': 'Level 4: Sky Jumps',
            'spawn': (100, 600),
            'platforms': [
                pygame.Rect(0, 650, 200, 40),
                pygame.Rect(300, 600, 150, 40),
                pygame.Rect(550, 550, 150, 40),
                pygame.Rect(800, 500, 150, 40),
                pygame.Rect(1050, 450, 150, 40),
                pygame.Rect(1300, 400, 200, 40),
                pygame.Rect(1600, 500, 200, 40),
                pygame.Rect(1900, 550, 300, 40),
                pygame.Rect(0, 700, 2500, 100),
            ],
            'enemies': [
                ('enemy', 1650, 482, 150),
            ],
            'flying_enemies': [
                ('flying', 400, 400, 200),
                ('flying', 900, 350, 200),
                ('flying', 1450, 300, 150),
            ],
            'power_ups': [
                PowerUp(575, 520, 'speed'),
                PowerUp(1325, 370, 'speed'),
            ],
            'coins': [
                Coin(325, 550),
                Coin(575, 500),
                Coin(825, 450),
                Coin(1075, 400),
                Coin(1950, 500),
            ],
            'spikes': [
                Spike(450, 630),
                Spike(950, 530),
                Spike(1750, 530),
            ],
            'boss': None,
            'exit': pygame.Rect(2100, 500, 30, 50),
        })
        
        # Level 5 - Final Boss
        levels.append({
            'name': 'Level 5: Final Showdown',
            'spawn': (100, 550),
            'platforms': [
                pygame.Rect(0, 600, 300, 40),
                pygame.Rect(400, 550, 120, 40),
                pygame.Rect(620, 500, 120, 40),
                pygame.Rect(840, 450, 120, 40),
                pygame.Rect(1060, 400, 120, 40),
                pygame.Rect(1280, 350, 200, 40),
                pygame.Rect(1580, 400, 150, 40),
                pygame.Rect(1830, 450, 150, 40),
                pygame.Rect(2080, 500, 500, 40),
                pygame.Rect(0, 700, 3000, 100),
            ],
            'enemies': [
                ('enemy', 450, 532, 100),
            ],
            'flying_enemies': [
                ('flying', 1000, 250, 150),
                ('flying', 1900, 300, 200),
            ],
            'power_ups': [
                PowerUp(440, 520, 'speed'),
                PowerUp(1305, 320, 'speed'),
                PowerUp(1855, 420, 'speed'),
            ],
            'coins': [
                Coin(150, 550),
                Coin(645, 450),
                Coin(1085, 350),
                Coin(1605, 350),
                Coin(2300, 450),
            ],
            'spikes': [
                Spike(560, 580),
                Spike(760, 530),
            ],
            'boss': ('boss', 2300, 460, 200),
            'exit': pygame.Rect(2500, 450, 30, 50),
        })
        
        return levels
    
    def load_level(self, level_index):
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
                _, x, y, patrol_dist = enemy_data
                self.enemies.append(Enemy(x, y, patrol_dist))
        
        for enemy_data in level['flying_enemies']:
            if enemy_data[0] == 'flying':
                _, x, y, patrol_height = enemy_data
                self.enemies.append(FlyingEnemy(x, y, patrol_height))
        
        # Load boss
        if level['boss']:
            boss_type, x, y, patrol_dist = level['boss']
            self.enemies.append(Boss(x, y, patrol_dist))
        
        # Load power-ups
        self.power_ups = level['power_ups']
        
        # Load coins
        self.coins = level['coins']
        self.coins_collected = 0
        self.total_coins = len(self.coins)
        
        # Load spikes
        self.spikes = level['spikes']
        
        # Exit
        self.exit_rect = level['exit']
        
        # Reset state
        self.projectiles = []
        self.particles = []
        self.key = None
        self.door = None
        self.boss_defeated = False
        self.camera_x = 0
        self.camera_y = 0
    
    def update_camera(self):
        target_x = self.player.x - SCREEN_WIDTH // 3
        target_y = self.player.y - SCREEN_HEIGHT // 2
        
        self.camera_x += (target_x - self.camera_x) * 0.1
        self.camera_y += (target_y - self.camera_y) * 0.1
        
        self.camera_x = max(0, self.camera_x)
        self.camera_y = max(0, min(self.camera_y, 100))
    
    def respawn_player(self):
        level = self.levels[self.current_level]
        spawn_x, spawn_y = level['spawn']
        self.player.x = spawn_x
        self.player.y = spawn_y
        self.player.vel_x = 0
        self.player.vel_y = 0
        self.player.invincible_timer = 120
        
        for _ in range(20):
            self.particles.append(Particle(
                self.player.x + self.player.width // 2, 
                self.player.y + self.player.height // 2,
                random.uniform(-4, 4), random.uniform(-4, 4),
                BLUE, 30
            ))
    
    def draw_background(self):
        # Gradient background
        for i in range(SCREEN_HEIGHT):
            color_value = int(30 + (i / SCREEN_HEIGHT) * 20)
            pygame.draw.line(self.screen, (color_value, color_value, color_value + 10), 
                           (0, i), (SCREEN_WIDTH, i))
    
    def draw_menu(self):
        self.screen.fill(BLACK)
        
        # Title
        title_font = pygame.font.Font(None, 64)
        title = title_font.render("CYBER PLATFORMER", True, CYAN)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))
        
        # Menu options
        menu_font = pygame.font.Font(None, 48)
        options = ["Start Game", "Quit"]
        
        for i, option in enumerate(options):
            color = YELLOW if i == self.selected_option else WHITE
            text = menu_font.render(option, True, color)
            y = 350 + i * 60
            x = SCREEN_WIDTH // 2 - text.get_width() // 2
            
            if i == self.selected_option:
                pygame.draw.polygon(self.screen, YELLOW, [
                    (x - 30, y + 20), (x - 20, y + 15), (x - 20, y + 25)
                ])
            
            self.screen.blit(text, (x, y))
        
        # Controls
        controls_font = pygame.font.Font(None, 24)
        controls = [
            "Controls:",
            "Arrow Keys / WASD - Move",
            "SPACE - Jump (double jump available!)",
            "SHIFT - Dash",
            "CTRL - Shoot",
        ]
        
        y = 550
        for line in controls:
            text = controls_font.render(line, True, GRAY)
            self.screen.blit(text, (20, y))
            y += 25
        
        # Particles
        if self.frame_count % 10 == 0:
            self.particles.append(Particle(
                random.randint(0, SCREEN_WIDTH), 0,
                random.uniform(-0.5, 0.5), random.uniform(1, 3),
                random.choice([CYAN, PURPLE, BLUE]), 100
            ))
        
        for particle in self.particles[:]:
            particle.update()
            particle.draw(self.screen)
            if particle.life <= 0 or particle.y > SCREEN_HEIGHT:
                self.particles.remove(particle)
    
    def draw_game(self):
        self.draw_background()
        
        # Platforms
        for platform in self.platforms:
            pygame.draw.rect(self.screen, WHITE, 
                           (platform.x - self.camera_x, platform.y - self.camera_y, 
                            platform.width, platform.height))
            pygame.draw.rect(self.screen, GRAY, 
                           (platform.x - self.camera_x, platform.y - self.camera_y, 
                            platform.width, platform.height), 2)
        
        # Exit (if not boss level or boss defeated)
        if self.current_level != len(self.levels) - 1 or self.boss_defeated:
            pygame.draw.rect(self.screen, GREEN, 
                           (self.exit_rect.x - self.camera_x, self.exit_rect.y - self.camera_y, 
                            self.exit_rect.width, self.exit_rect.height))
        
        # Door
        if self.door:
            self.door.draw(self.screen, self.camera_x, self.camera_y)
        
        # Key
        if self.key:
            self.key.draw(self.screen, self.camera_x, self.camera_y)
        
        # Power-ups
        for power_up in self.power_ups:
            power_up.draw(self.screen, self.camera_x, self.camera_y)
        
        # Coins
        for coin in self.coins:
            coin.draw(self.screen, self.camera_x, self.camera_y)
        
        # Spikes
        for spike in self.spikes:
            spike.draw(self.screen, self.camera_x, self.camera_y)
        
        # Enemies
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera_x, self.camera_y)
        
        # Projectiles
        for projectile in self.projectiles:
            projectile.draw(self.screen, self.camera_x, self.camera_y)
        
        # Player
        self.player.draw(self.screen, self.camera_x, self.camera_y)
        
        # Particles
        for particle in self.particles[:]:
            particle.update()
            particle.draw(self.screen)
            if particle.life <= 0:
                self.particles.remove(particle)
        
        # HUD
        hud_font = pygame.font.Font(None, 32)
        
        # Level name
        level_text = hud_font.render(self.levels[self.current_level]['name'], True, CYAN)
        self.screen.blit(level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2, 10))
        
        # Coins
        coin_text = hud_font.render(f"Coins: {self.coins_collected}/{self.total_coins}", True, YELLOW)
        self.screen.blit(coin_text, (10, 10))
        
        # Speed boost indicator
        if self.player.speed_boost > 0:
            speed_text = hud_font.render(f"Speed: {self.player.speed_boost // 60}s", True, ORANGE)
            self.screen.blit(speed_text, (10, 50))
        
        # Dash cooldown bar
        if self.player.dash_cooldown > 0:
            bar_width = 100
            cooldown_ratio = self.player.dash_cooldown / DASH_COOLDOWN
            pygame.draw.rect(self.screen, DARK_GRAY, (10, SCREEN_HEIGHT - 30, bar_width, 20))
            pygame.draw.rect(self.screen, CYAN, 
                           (10, SCREEN_HEIGHT - 30, bar_width * (1 - cooldown_ratio), 20))
            dash_text = pygame.font.Font(None, 20).render("Dash", True, WHITE)
            self.screen.blit(dash_text, (15, SCREEN_HEIGHT - 28))
    
    def draw_victory(self):
        self.screen.fill(BLACK)
        
        # Victory text
        victory_font = pygame.font.Font(None, 72)
        victory_text = victory_font.render("VICTORY!", True, YELLOW)
        self.screen.blit(victory_text, (SCREEN_WIDTH // 2 - victory_text.get_width() // 2, 250))
        
        # Score
        score_font = pygame.font.Font(None, 48)
        score_text = score_font.render(f"Coins Collected: {self.coins_collected}/{self.total_coins}", True, WHITE)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 350))
        
        # Return prompt
        prompt_font = pygame.font.Font(None, 32)
        prompt = prompt_font.render("Press ESC to return to menu", True, GRAY)
        self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 450))
        
        # Celebration particles
        if self.frame_count % 5 == 0:
            self.particles.append(Particle(
                random.randint(0, SCREEN_WIDTH), 0,
                random.uniform(-2, 2), random.uniform(2, 5),
                random.choice([YELLOW, GREEN, CYAN, PURPLE]), 80
            ))
        
        for particle in self.particles[:]:
            particle.update()
            particle.draw(self.screen)
            if particle.life <= 0:
                self.particles.remove(particle)
    
    def handle_collisions(self):
        # Player-enemy collision
        for enemy in self.enemies:
            if self.player.rect.colliderect(enemy.rect) and self.player.invincible_timer == 0:
                self.respawn_player()
        
        # Projectile collisions
        for projectile in self.projectiles[:]:
            # Out of bounds
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
                                    RED, 25
                                ))
                            if enemy.health <= 0:
                                self.enemies.remove(enemy)
                                self.boss_defeated = True
                                for _ in range(30):
                                    self.particles.append(Particle(
                                        enemy.x + enemy.width // 2, enemy.y + enemy.height // 2,
                                        random.uniform(-5, 5), random.uniform(-5, 5),
                                        RED, 40
                                    ))
                                # Drop key
                                self.key = Key(enemy.x + enemy.width // 2 - 8, 
                                             enemy.y + enemy.height // 2 - 8)
                        else:
                            self.enemies.remove(enemy)
                            for _ in range(8):
                                color = RED if isinstance(enemy, Enemy) else GREEN
                                self.particles.append(Particle(
                                    enemy.x + enemy.width // 2, enemy.y + enemy.height // 2,
                                    random.uniform(-3, 3), random.uniform(-3, 3),
                                    color, 25
                                ))
                        if projectile in self.projectiles:
                            self.projectiles.remove(projectile)
                        break
            
            # Enemy projectile hits player
            elif projectile.color == RED:
                if projectile.rect.colliderect(self.player.rect) and self.player.invincible_timer == 0:
                    self.respawn_player()
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)
        
        # Power-up collection
        for power_up in self.power_ups:
            if not power_up.collected and self.player.rect.colliderect(power_up.rect):
                power_up.collected = True
                if power_up.type == "speed":
                    self.player.speed_boost = 300
                for _ in range(15):
                    self.particles.append(Particle(
                        power_up.x + power_up.width // 2, power_up.y + power_up.height // 2,
                        random.uniform(-3, 3), random.uniform(-3, 3),
                        PURPLE, 30
                    ))
        
        # Coin collection
        for coin in self.coins:
            if not coin.collected and self.player.rect.colliderect(coin.rect):
                coin.collected = True
                self.coins_collected += 1
                for _ in range(10):
                    self.particles.append(Particle(
                        coin.x + coin.width // 2, coin.y + coin.height // 2,
                        random.uniform(-2, 2), random.uniform(-2, 2),
                        YELLOW, 20
                    ))
        
        # Spike collision
        for spike in self.spikes:
            if self.player.rect.colliderect(spike.rect) and self.player.invincible_timer == 0:
                self.respawn_player()
        
        # Key collection
        if self.key and not self.key.collected and self.player.rect.colliderect(self.key.rect):
            self.key.collected = True
            self.door = Door(self.exit_rect.x, self.exit_rect.y - 10)
            for _ in range(20):
                self.particles.append(Particle(
                    self.key.x + self.key.width // 2, self.key.y + self.key.height // 2,
                    random.uniform(-4, 4), random.uniform(-4, 4),
                    YELLOW, 35
                ))
        
        # Door entry
        if self.door and self.player.rect.colliderect(self.door.rect):
            self.current_level += 1
            if self.current_level >= len(self.levels):
                self.state = 'victory'
            else:
                self.load_level(self.current_level)
        
        # Normal exit
        elif self.current_level != len(self.levels) - 1 and self.player.rect.colliderect(self.exit_rect):
            self.current_level += 1
            if self.current_level >= len(self.levels):
                self.state = 'victory'
            else:
                self.load_level(self.current_level)
        
        # Fall off map
        if self.player.y > 1000:
            self.respawn_player()
    
    def run(self):
        print("Game started!")
        running = True
        
        while running:
            self.frame_count += 1
            
            # Events
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
                                self.load_level(0)
                                self.state = 'playing'
                            else:
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
            
            # Update and draw
            if self.state == 'menu':
                self.draw_menu()
            
            elif self.state == 'playing':
                # Update
                self.player.update(self.platforms, self)
                
                for enemy in self.enemies:
                    if isinstance(enemy, Boss):
                        enemy.update(self.platforms, self.player, self)
                    elif isinstance(enemy, FlyingEnemy):
                        enemy.update()
                    else:
                        enemy.update(self.platforms)
                
                for projectile in self.projectiles:
                    projectile.update()
                
                self.handle_collisions()
                self.update_camera()
                
                # Draw
                self.draw_game()
            
            elif self.state == 'victory':
                self.draw_victory()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        print("Thanks for playing!")

if __name__ == "__main__":
    game = Game()
    game.run()
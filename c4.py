import pygame
import math
import random
import json
import os

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
GRAVITY = 0.8
JUMP_STRENGTH = -15
DOUBLE_JUMP_STRENGTH = -12
PLAYER_SPEED = 5
ENEMY_SPEED = 2
BOSS_SPEED = 1.5
PROJECTILE_SPEED = 5

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
CYAN = (100, 220, 220)  # For player bullets!
ORANGE = (240, 140, 40)
BROWN = (140, 80, 40)
PLATFORM_COLOR = BLACK  # Platforms are BLACK!

class MovingPlatform:
    def __init__(self, x, y, width, height, move_x_range=0, move_y_range=0, speed=2):
        self.start_x = x
        self.start_y = y
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.move_x_range = move_x_range  # How far to move horizontally
        self.move_y_range = move_y_range  # How far to move vertically
        self.speed = speed
        self.direction_x = 1
        self.direction_y = 1
        self.rect = pygame.Rect(x, y, width, height)
    
    # Properties to make it work like a Rect
    @property
    def top(self):
        return self.rect.top
    
    @property
    def bottom(self):
        return self.rect.bottom
    
    @property
    def left(self):
        return self.rect.left
    
    @property
    def right(self):
        return self.rect.right
    
    def update(self):
        # Move horizontally
        if self.move_x_range > 0:
            self.x += self.speed * self.direction_x
            if abs(self.x - self.start_x) >= self.move_x_range:
                self.direction_x *= -1
        
        # Move vertically
        if self.move_y_range > 0:
            self.y += self.speed * self.direction_y
            if abs(self.y - self.start_y) >= self.move_y_range:
                self.direction_y *= -1
        
        self.rect.x = self.x
        self.rect.y = self.y
    
    def draw(self, screen, camera_x, camera_y):
        pygame.draw.rect(screen, PLATFORM_COLOR, 
                        (self.x - camera_x, self.y - camera_y, 
                         self.width, self.height))
        pygame.draw.rect(screen, GRAY, 
                        (self.x - camera_x, self.y - camera_y, 
                         self.width, self.height), 2)

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
        self.life -= 1
    
    def draw(self, screen):
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))
            color = (*self.color[:3], alpha)
            surface = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(surface, color, (2, 2), 2)
            screen.blit(surface, (int(self.x), int(self.y)))

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
        self.rect = pygame.Rect(x, y, self.width, self.height)
        # Power-up timers!
        self.speed_boost = 0
        self.invincible = 0
        self.mega_jump = 0
        self.shoot_cooldown = 0  # For the GUN!
        self.facing_right = True  # Track which way player is facing
        
    def update(self, platforms, projectiles=None):
        # Decrement power-up timers
        if self.speed_boost > 0:
            self.speed_boost -= 1
        if self.invincible > 0:
            self.invincible -= 1
        if self.mega_jump > 0:
            self.mega_jump -= 1
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        
        keys = pygame.key.get_pressed()
        
        # GUN! Shoot with CTRL in the direction you're moving/facing!
        if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
            if self.shoot_cooldown == 0 and projectiles is not None:
                # Determine shoot direction based on movement or facing
                shoot_vel_x = 0
                shoot_vel_y = 0
                
                if keys[pygame.K_UP] or keys[pygame.K_w]:
                    shoot_vel_y = -PROJECTILE_SPEED
                elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    shoot_vel_y = PROJECTILE_SPEED
                elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    shoot_vel_x = -PROJECTILE_SPEED
                    self.facing_right = False
                elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    shoot_vel_x = PROJECTILE_SPEED
                    self.facing_right = True
                else:
                    # No direction key, shoot in facing direction
                    shoot_vel_x = PROJECTILE_SPEED if self.facing_right else -PROJECTILE_SPEED
                
                # Create player bullet!
                projectiles.append(Projectile(
                    self.x + self.width // 2, 
                    self.y + self.height // 2,
                    shoot_vel_x, shoot_vel_y,
                    is_player_bullet=True  # CYAN bullets!
                ))
                self.shoot_cooldown = 15  # Cooldown frames
        
        # Speed boost power-up!
        speed = PLAYER_SPEED * 2 if self.speed_boost > 0 else PLAYER_SPEED
        
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
        self.vel_y += GRAVITY
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
        self.y += self.vel_y
        self.rect.y = self.y
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vel_y > 0:
                    self.rect.bottom = platform.top
                    self.y = self.rect.y
                    self.vel_y = 0
                    self.on_ground = True
                    self.double_jump_available = True
                elif self.vel_y < 0:
                    self.rect.top = platform.bottom
                    self.y = self.rect.y
                    self.vel_y = 0
    
    def jump(self):
        # Mega jump power-up makes jumps HUGE!
        jump_power = JUMP_STRENGTH * 1.5 if self.mega_jump > 0 else JUMP_STRENGTH
        double_jump_power = DOUBLE_JUMP_STRENGTH * 1.5 if self.mega_jump > 0 else DOUBLE_JUMP_STRENGTH
        
        if self.on_ground:
            self.vel_y = jump_power
        elif self.double_jump_available:
            self.vel_y = double_jump_power
            self.double_jump_available = False
    
    def draw(self, screen, camera_x, camera_y):
        t = pygame.time.get_ticks() * 0.01
        bounce = math.sin(t) * 2 if self.on_ground else 0
        # Walking leg animation
        walk_cycle = math.sin(t * 3) if abs(self.vel_x) > 0.5 else 0
        col = getattr(self, 'color', BLUE)
        px = self.x - camera_x
        py = self.y - camera_y + bounce
        # Shadow
        pygame.draw.ellipse(screen, (0,0,0,0), (px-2, py+self.height-2, self.width+4, 8))
        # Body
        pygame.draw.rect(screen, col, (px, py, self.width, self.height), 0, 4)
        # Outline when invincible (flashing)
        if getattr(self, 'invincible', 0) > 0 and int(t*4)%2==0:
            pygame.draw.rect(screen, WHITE, (px-1, py-1, self.width+2, self.height+2), 2, 4)
        # Eyes
        ex = px + 13 if self.facing_right else px + 4
        pygame.draw.circle(screen, WHITE, (int(ex), int(py+6)), 4)
        pygame.draw.circle(screen, BLACK, (int(ex + (1 if self.facing_right else -1)), int(py+7)), 2)
        # Legs
        if abs(self.vel_x) > 0.5:
            pygame.draw.rect(screen, tuple(max(0,c-40) for c in col),
                (px+3, py+self.height, 7, 5+int(walk_cycle*3)))
            pygame.draw.rect(screen, tuple(max(0,c-40) for c in col),
                (px+10, py+self.height, 7, 5-int(walk_cycle*3)))
        else:
            pygame.draw.rect(screen, tuple(max(0,c-40) for c in col), (px+3, py+self.height, 7, 5))
            pygame.draw.rect(screen, tuple(max(0,c-40) for c in col), (px+10, py+self.height, 7, 5))
        # Gun arm
        if self.facing_right:
            pygame.draw.rect(screen, GRAY, (px+self.width, py+8, 10, 5))
        else:
            pygame.draw.rect(screen, GRAY, (px-10, py+8, 10, 5))
        # Speed boost trail
        if getattr(self, 'speed_boost', 0) > 0:
            for i in range(3):
                tx2 = px - (i+1)*8*(1 if self.facing_right else -1)
                alpha = 180 - i*50
                ts2 = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                ts2.fill((*col, alpha//3))
                screen.blit(ts2, (tx2, py))

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
        pygame.draw.circle(screen, YELLOW, 
                          (int(self.x - camera_x + 5), int(self.y - camera_y + 5 + wobble)), 2)
        pygame.draw.circle(screen, YELLOW, 
                          (int(self.x - camera_x + 13), int(self.y - camera_y + 5 + wobble)), 2)

class FastEnemy:
    """Runs twice as fast, smaller, orange coloured."""
    def __init__(self, x, y, patrol_distance):
        self.start_x = x; self.x = x; self.y = y
        self.width = 14; self.height = 14
        self.patrol_distance = patrol_distance
        self.direction = 1
        self.rect = pygame.Rect(x, y, self.width, self.height)
    def update(self, platforms):
        self.x += ENEMY_SPEED * 2.2 * self.direction
        if abs(self.x - self.start_x) >= self.patrol_distance:
            self.direction *= -1
        self.rect.x = int(self.x)
        for p in platforms:
            if self.rect.colliderect(p):
                self.direction *= -1; break
    def draw(self, screen, camera_x, camera_y):
        t = pygame.time.get_ticks() * 0.03
        wobble = math.sin(t) * 2
        pygame.draw.rect(screen, ORANGE,
            (self.x-camera_x, self.y-camera_y+wobble, self.width, self.height), 0, 3)
        for ex2 in [self.x-camera_x+3, self.x-camera_x+9]:
            pygame.draw.circle(screen, WHITE, (int(ex2), int(self.y-camera_y+4+wobble)), 2)
        # Speed lines
        pygame.draw.line(screen, (255,180,80),
            (int(self.x-camera_x-6), int(self.y-camera_y+7)),
            (int(self.x-camera_x-1), int(self.y-camera_y+7)), 2)

class ShieldEnemy:
    """Takes 2 hits to kill, has a visible shield."""
    def __init__(self, x, y, patrol_distance):
        self.start_x = x; self.x = x; self.y = y
        self.width = 20; self.height = 20
        self.patrol_distance = patrol_distance
        self.direction = 1
        self.health = 2
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.hit_flash = 0
    def update(self, platforms):
        self.x += ENEMY_SPEED * 0.8 * self.direction
        if abs(self.x - self.start_x) >= self.patrol_distance:
            self.direction *= -1
        self.rect.x = int(self.x)
        if self.hit_flash > 0: self.hit_flash -= 1
        for p in platforms:
            if self.rect.colliderect(p):
                self.direction *= -1; break
    def draw(self, screen, camera_x, camera_y):
        col = WHITE if self.hit_flash > 0 else (100, 100, 200)
        pygame.draw.rect(screen, col,
            (self.x-camera_x, self.y-camera_y, self.width, self.height), 0, 4)
        # Shield
        shield_col = (150, 200, 255) if self.health == 2 else (100, 100, 100)
        side = self.x - camera_x - 8 if self.direction < 0 else self.x - camera_x + self.width - 2
        pygame.draw.rect(screen, shield_col, (int(side), int(self.y-camera_y-2), 8, 24), 0, 3)
        pygame.draw.rect(screen, WHITE, (int(side), int(self.y-camera_y-2), 8, 24), 1, 3)
        # Eyes
        for ex2 in [self.x-camera_x+5, self.x-camera_x+13]:
            pygame.draw.circle(screen, YELLOW, (int(ex2), int(self.y-camera_y+7)), 2)
        # Health pips
        for i in range(self.health):
            pygame.draw.circle(screen, GREEN, (int(self.x-camera_x+4+i*8), int(self.y-camera_y-7)), 3)

class JumperEnemy:
    """Bounces up and down, harder to hit."""
    def __init__(self, x, y, patrol_distance):
        self.start_x = x; self.x = x; self.y = y; self.base_y = y
        self.width = 16; self.height = 16
        self.patrol_distance = patrol_distance
        self.direction = 1; self.jump_phase = random.uniform(0, math.pi*2)
        self.rect = pygame.Rect(x, y, self.width, self.height)
    def update(self, platforms):
        self.x += ENEMY_SPEED * self.direction
        if abs(self.x - self.start_x) >= self.patrol_distance:
            self.direction *= -1
        self.jump_phase += 0.08
        self.y = self.base_y + math.sin(self.jump_phase) * 22
        self.rect.x = int(self.x); self.rect.y = int(self.y)
    def draw(self, screen, camera_x, camera_y):
        # Squish when landing
        squish = abs(math.sin(self.jump_phase))
        w2 = int(self.width * (1 + (1-squish)*0.3))
        h2 = int(self.height * (1 - (1-squish)*0.2))
        pygame.draw.rect(screen, (180, 60, 180),
            (int(self.x-camera_x), int(self.y-camera_y), w2, h2), 0, 5)
        pygame.draw.circle(screen, WHITE, (int(self.x-camera_x+5), int(self.y-camera_y+5)), 2)
        pygame.draw.circle(screen, WHITE, (int(self.x-camera_x+11), int(self.y-camera_y+5)), 2)

class Gem:
    """Collectible gem worth 5 coins, rare, sparkles blue/purple."""
    GEM_COLORS = [(100,200,255),(180,100,255),(255,100,180),(100,255,180)]
    def __init__(self, x, y, gem_type=0):
        self.x = x; self.y = y
        self.gem_type = gem_type % len(self.GEM_COLORS)
        self.col = self.GEM_COLORS[self.gem_type]
        self.collected = False
        self.rect = pygame.Rect(x, y, 16, 16)
        self.anim = random.uniform(0, math.pi*2)
    def draw(self, screen, camera_x, camera_y):
        if self.collected: return
        self.anim += 0.06
        bob = math.sin(self.anim) * 3
        cx2 = self.x - camera_x + 8
        cy2 = self.y - camera_y + 8 + bob
        # Glow
        for r2,a2 in [(14,30),(10,60),(7,100)]:
            gs = pygame.Surface((r2*2,r2*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*self.col, a2), (r2,r2), r2)
            screen.blit(gs, (cx2-r2, cy2-r2))
        # Diamond shape
        pts = [(cx2, cy2-7),(cx2+5,cy2),(cx2,cy2+7),(cx2-5,cy2)]
        pygame.draw.polygon(screen, self.col, pts)
        pygame.draw.polygon(screen, WHITE, pts, 1)
        # Shine
        pygame.draw.line(screen, WHITE, (int(cx2-2), int(cy2-4)), (int(cx2+1), int(cy2-1)), 2)

class NPC:
    """A friendly NPC that gives tips when player is nearby."""
    TIPS = [
        "Hey! Use CTRL to shoot enemies!",
        "Dash with SHIFT to dodge bullets!",
        "Collect a sticker in every level!",
        "Double jump by pressing SPACE twice!",
        "Red Guy is the final boss. Stay tough!",
        "Gems give +5 coins — don't miss them!",
        "ShieldEnemies (blue) need TWO hits!",
        "Fast orange enemies — keep moving!",
    ]
    def __init__(self, x, y, tip_idx=0):
        self.x = x; self.y = y
        self.tip = self.TIPS[tip_idx % len(self.TIPS)]
        self.rect = pygame.Rect(x, y, 20, 24)
        self.anim = random.uniform(0, math.pi*2)
        self.talking = False
    def update(self, player_rect):
        self.anim += 0.05
        self.talking = abs((self.x+10)-(player_rect.x+10)) < 120
    def draw(self, screen, camera_x, camera_y):
        px = self.x - camera_x; py = self.y - camera_y
        bob = math.sin(self.anim*2)*2
        # Green NPC body
        pygame.draw.rect(screen,(60,180,80),(px,py+bob,20,24),0,5)
        pygame.draw.circle(screen,WHITE,(int(px+14),int(py+8+bob)),3)
        pygame.draw.circle(screen,BLACK,(int(px+15),int(py+9+bob)),1)
        pygame.draw.rect(screen,(40,120,60),(px+2,py+bob-4,16,6))
        # Exclamation mark above when nearby
        if self.talking:
            ef = pygame.font.Font(None,22)
            es2 = ef.render("!", True, YELLOW)
            screen.blit(es2,(px+6, py+bob-20))
            # Speech bubble
            bx=px-160; by=py-55
            pygame.draw.rect(screen,WHITE,(bx,by,190,44),0,8)
            pygame.draw.rect(screen,(60,180,80),(bx,by,190,44),2,8)
            pygame.draw.polygon(screen,WHITE,[(px+2,py+bob-2),(px+18,py+bob-2),(px+10,py+bob+4)])
            tf=pygame.font.Font(None,17)
            words=self.tip.split(); line2=''; lines2=[]
            for w in words:
                test=line2+w+' '
                if tf.size(test)[0]>178: lines2.append(line2); line2=w+' '
                else: line2=test
            if line2: lines2.append(line2)
            for i,l in enumerate(lines2[:2]):
                screen.blit(tf.render(l.strip(),True,(20,60,20)),(bx+6,by+7+i*16))

class Boss:
    def __init__(self, x, y, health=5):
        self.x = x
        self.y = y
        self.width = 50
        self.height = 50
        self.health = health
        self.direction = 1
        self.patrol_distance = 200
        self.start_x = x
        self.shoot_timer = 0
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def update(self, platforms, player, projectiles):
        self.x += BOSS_SPEED * self.direction
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
        self.shoot_timer += 1
        if self.shoot_timer >= 120:
            dx = player.x - self.x
            dy = player.y - self.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance > 0:
                dx, dy = dx / distance, dy / distance
                projectiles.append(Projectile(self.x + self.width // 2, self.y, 
                                             dx * PROJECTILE_SPEED, dy * PROJECTILE_SPEED))
            self.shoot_timer = 0
    
    def draw(self, screen, camera_x, camera_y):
        wobble = math.sin(pygame.time.get_ticks() * 0.015) * 2
        pygame.draw.rect(screen, PURPLE, 
                        (self.x - camera_x, self.y - camera_y + wobble, 
                         self.width, self.height))
        pygame.draw.circle(screen, YELLOW, 
                          (int(self.x - camera_x + 15), int(self.y - camera_y + 15 + wobble)), 5)
        pygame.draw.circle(screen, YELLOW, 
                          (int(self.x - camera_x + 35), int(self.y - camera_y + 15 + wobble)), 5)
        pygame.draw.rect(screen, RED, 
                        (self.x - camera_x, self.y - camera_y - 10 + wobble, 
                         self.width * (self.health / 5), 5))

class FlyingBoss:
    """Red Guy with WINGS! Flies around and you have to jump on him!"""
    def __init__(self, x, y, health=5):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 60
        self.health = health
        self.max_health = health
        self.direction_x = 1
        self.direction_y = 1
        self.speed = 3
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.wing_flap = 0
    
    def update(self, player):
        # Fly in a pattern
        self.x += self.speed * self.direction_x
        self.y += math.sin(pygame.time.get_ticks() * 0.01) * 2
        
        # Change direction randomly
        if random.random() < 0.02:
            self.direction_x *= -1
        
        # Keep in bounds
        if self.x < 100:
            self.direction_x = 1
        if self.x > 1400:
            self.direction_x = -1
        if self.y < 100:
            self.y = 100
        if self.y > 500:
            self.y = 500
        
        self.rect.x = self.x
        self.rect.y = self.y
        self.wing_flap += 0.3
    
    def draw(self, screen, camera_x, camera_y):
        # Red Guy body
        pygame.draw.rect(screen, RED, 
                        (self.x - camera_x, self.y - camera_y, 
                         self.width, self.height))
        
        # WINGS!
        wing_offset = math.sin(self.wing_flap) * 15
        # Left wing
        wing_points_left = [
            (self.x - camera_x, self.y - camera_y + 30),
            (self.x - camera_x - 30, self.y - camera_y + 20 + wing_offset),
            (self.x - camera_x - 20, self.y - camera_y + 40 + wing_offset)
        ]
        pygame.draw.polygon(screen, (180, 50, 50), wing_points_left)
        
        # Right wing
        wing_points_right = [
            (self.x - camera_x + self.width, self.y - camera_y + 30),
            (self.x - camera_x + self.width + 30, self.y - camera_y + 20 + wing_offset),
            (self.x - camera_x + self.width + 20, self.y - camera_y + 40 + wing_offset)
        ]
        pygame.draw.polygon(screen, (180, 50, 50), wing_points_right)
        
        # Evil eyes
        pygame.draw.circle(screen, YELLOW, 
                          (int(self.x - camera_x + 18), int(self.y - camera_y + 20)), 5)
        pygame.draw.circle(screen, YELLOW, 
                          (int(self.x - camera_x + 42), int(self.y - camera_y + 20)), 5)
        
        # Health bar
        pygame.draw.rect(screen, BLACK, 
                        (self.x - camera_x, self.y - camera_y - 15, self.width, 8))
        pygame.draw.rect(screen, RED, 
                        (self.x - camera_x, self.y - camera_y - 15, 
                         self.width * (self.health / self.max_health), 8))

class Projectile:
    def __init__(self, x, y, vel_x, vel_y, is_player_bullet=False):
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.width = 8
        self.height = 8
        self.is_player_bullet = is_player_bullet  # Player bullets are cyan, enemy bullets are red
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.rect.x = self.x
        self.rect.y = self.y
    
    def draw(self, screen, camera_x, camera_y):
        color = CYAN if self.is_player_bullet else RED
        pygame.draw.circle(screen, color, 
                         (int(self.x - camera_x + self.width // 2), 
                          int(self.y - camera_y + self.height // 2)), 
                         self.width // 2)
    

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
                pygame.draw.ellipse(screen, WHITE, 
                                   (self.x - camera_x + (self.width - width) // 2 + 2, 
                                    self.y - camera_y + 2, max(1, width - 4), self.height - 4))

class PowerUp:
    """Power-ups! Speed boost, invincibility, mega jump!"""
    def __init__(self, x, y, power_type='speed'):
        self.x = x
        self.y = y
        self.width = 24
        self.height = 24
        self.power_type = power_type  # 'speed', 'invincible', 'mega_jump'
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.collected = False
        self.colors = {
            'speed': PURPLE,
            'invincible': YELLOW,
            'mega_jump': GREEN
        }
    
    def draw(self, screen, camera_x, camera_y):
        if not self.collected:
            pulse = math.sin(pygame.time.get_ticks() * 0.01) * 3
            color = self.colors.get(self.power_type, PURPLE)
            # Outer glow
            pygame.draw.rect(screen, color,
                           (self.x - camera_x - 2, self.y - camera_y + pulse - 2, 
                            self.width + 4, self.height + 4))
            # Inner square
            pygame.draw.rect(screen, WHITE,
                           (self.x - camera_x + 6, self.y - camera_y + pulse + 6, 
                            12, 12))
            # Letter indicator
            font = pygame.font.Font(None, 16)
            letter = self.power_type[0].upper() if self.power_type else 'P'
            text = font.render(letter, True, color)
            screen.blit(text, (self.x - camera_x + 8, self.y - camera_y + pulse + 8))

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

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Minimal Platformer 4: The Red Uprising  — by Kyle")
        self.clock = pygame.time.Clock()
        self.camera_x = 0
        self.camera_y = 0
        self.current_level = 0
        self.coins_collected = 0
        self.total_coins = 0
        self.game_completed = False
        self.boss_defeated = False
        self.state = "intro"
        self.intro_timer = 0
        self.levels = self.create_levels()
        self.projectiles = []
        self.tutorial_step = 0
        self.tutorial_level = self.create_tutorial_level()

        # ── COMBO SYSTEM ──────────────────────────────────────────────────
        self.combo = 0           # current kill streak
        self.combo_timer = 0     # frames since last kill
        self.max_combo = 0       # personal best

        # ── SCREEN SHAKE ──────────────────────────────────────────────────
        self.shake_timer = 0
        self.shake_intensity = 0

        # ── DASH ──────────────────────────────────────────────────────────
        # Players press SHIFT to dash - short invincible burst of speed
        self.dash_cd = 0          # cooldown frames
        self.dash_timer = 0       # active dash frames
        self.dash_dir = 1

        # ── LEVEL TIMER ───────────────────────────────────────────────────
        self.level_timer = 0      # frames spent on current level
        self.best_times  = {}     # level_index -> best frame count

        # ── FLOATY SCORE TEXT ─────────────────────────────────────────────
        self.floaty_texts = []    # list of {x,y,vy,text,col,life,maxlife}

        # ── WEATHER / ATMOSPHERE ─────────────────────────────────────────
        self.weather_particles = []
        self.weather_timer = 0

        # ── ACHIEVEMENTS ─────────────────────────────────────────────────
        self.achievements_earned = set()
        self.achievement_popup   = []  # {text, timer, icon}
        # All achievements: id -> (name, description, icon)
        self.ACHIEVEMENTS = {
            'first_blood':    ('First Blood',      'Kill your first enemy',         '🗡️'),
            'combo3':         ('Hat Trick',         'Get a x3 combo',                '🎩'),
            'combo10':        ('UNSTOPPABLE',       'Get a x10 combo',               '💥'),
            'all_coins_1':    ('Coin Collector',    'Grab every coin in a level',    '💰'),
            'speed_run':      ('Speedrunner',       'Beat a level in under 15 sec',  '⚡'),
            'no_damage':      ('Ghost Run',         'Beat a level without dying',    '👻'),
            'sticker_5':      ('Sticker Fan',       'Collect 5 stickers',            '⭐'),
            'sticker_all':    ('Sticker Master',    'Collect all 30 stickers',       '🌟'),
            'shopper':        ('Big Spender',       'Spend 50 coins in the shop',    '🛒'),
            'clicker_100':    ('Clicker Addict',    'Click Blue Guy 100 times',      '👆'),
            'boss1':          ('Boss Slayer',       'Defeat your first boss',        '👑'),
            'boss_all':       ('Champion',          'Defeat all bosses',             '🏆'),
            'dasher':         ('Speed Demon',       'Dash 20 times',                 '💨'),
            'home_owner':     ('Home Owner',        'Visit Blue Guy\'s house',       '🏠'),
            'tv_watcher':     ('Couch Potato',      'Watch all 4 TV channels',       '📺'),
            'level15':        ('Halfway There',     'Beat level 15',                 '🌲'),
            'level30':        ('The End?',          'Beat all 30 levels',            '🎖️'),
            'hat_owner':      ('Fashion Icon',      'Own your first hat',            '🎩'),
            'all_hats':       ('Hat Collector',     'Own all 5 hats',                '👒'),
            'wowy':           ('Wowy',              'Defeat the final boss',          '🤩'),
            '1_sitting':      ('1 Sitting',         'Beat the whole game in one go',  '🪑'),
            'gotta_drink':    ('Gotta Drink',       'Watch the cutscene after level 6', '💧'),
        }
        self.dash_count     = 0   # track for dasher achievement
        self.shop_spent     = 0   # track for shopper achievement
        self.tv_channels_seen = set()
        self.level_no_death  = True  # reset on player death

        # ── CHEAT CODES ───────────────────────────────────────────────────
        self.cheat_buffer   = []    # recent keypresses
        self.cheat_active   = {}    # active cheats: name -> timer
        # KONAMI-style: type these in menu: UUDDLRLR = GODMODE, COINS = +100 coins
        self.CHEATS = {
            'godmode':  [pygame.K_g, pygame.K_o, pygame.K_d],
            'coins100': [pygame.K_c, pygame.K_o, pygame.K_i, pygame.K_n, pygame.K_s],
            'allhats':  [pygame.K_h, pygame.K_a, pygame.K_t, pygame.K_s],
        }

        # ── COIN MAGNET POWERUP ───────────────────────────────────────────
        # Added as a 4th power-up type — coins fly toward player!
        self.coin_magnet = 0  # frames active

        # ── DAILY CHALLENGE ───────────────────────────────────────────────
        import datetime
        today = datetime.date.today()
        self.daily_seed       = today.toordinal()
        self.daily_level      = (self.daily_seed % 30)   # which level
        self.daily_goal       = ['no_damage','speed_run','all_coins'][(self.daily_seed//30)%3]
        self.daily_completed  = False
        self.daily_reward     = 25  # bonus coins

        # ── GAME OVER / DEATH STATS ────────────────────────────────────────
        self.total_deaths    = 0
        self.session_kills   = 0

        # ── GEMS ─────────────────────────────────────────────────────────
        self.gems = []           # current level gems
        self.gems_collected = 0  # lifetime gems

        # ── INVENTORY ────────────────────────────────────────────────────
        # Items player can carry: key, gem, health_potion
        self.inventory = []      # list of item names (max 4)

        # ── JOURNAL ──────────────────────────────────────────────────────
        self.journal_open   = False
        # Entries unlock as you beat levels
        self.JOURNAL_ENTRIES = {
            0:  ("Day 1",          "Setting off on my adventure. Red Guy has caused chaos across the land. I must stop him!"),
            4:  ("Day 5",          "Cleared 5 levels. My legs are tired. Found a gas station — the water was delicious."),
            9:  ("Day 10 - BOSS!", "Fought the first boss. My gun saved me. Red Guy is running scared!"),
            14: ("Entering Woods", "The woods. Dark. Full of eyes. My hat keeps the rain off at least."),
            19: ("Deep Woods",     "20 levels done. Found some amazing stickers. My house misses me."),
            24: ("Getting Closer", "25 levels. Red Guy's fortress is near. I can hear him laughing from here."),
            29: ("VICTORY",        "I DID IT. All 30 levels. Red Guy defeated. Time for a long nap on my sofa."),
        }

        # ── MINI-GAMES (house) ────────────────────────────────────────────
        self.minigame_active   = None   # None, 'shell', 'guess'
        self.shell_cups        = [0,1,2]   # which cup has ball: 0=left 1=mid 2=right
        self.shell_ball        = 1
        self.shell_phase       = 'hide'    # hide, shuffle, pick
        self.shell_timer       = 0
        self.shell_shuffles    = []
        self.shell_result      = None
        self.guess_target      = random.randint(1, 10)
        self.guess_attempts    = 3
        self.guess_input       = ''
        self.guess_result      = None

        # ── LEVEL TRANSITION ─────────────────────────────────────────────
        self.transition_timer  = 0
        self.transition_type   = None   # 'in' or 'out'

        # ── CREDITS ──────────────────────────────────────────────────────
        self.credits_open      = False
        self.credits_scroll    = 0

        # ── CPU RACE ──────────────────────────────────────────────────────
        self.race_open        = False
        self.race_state       = 'ready'
        self.race_timer       = 0
        self.race_countdown   = 180
        self.race_player_x    = 60.0
        self.race_cpu_x       = 60.0
        self.race_finish      = 1060
        self.race_result      = None
        self.race_player_time = 0
        self.race_cpu_time    = 0
        self.race_best        = None
        self.race_cpu_speed   = 4.2
        self.race_player_vel  = 0.0

        # ── ONE SITTING TRACKER ───────────────────────────────────────────
        self.session_started_level = None  # which level this session started on

        # ── PLAYER HEALTH ─────────────────────────────────────────────────
        self.player_health     = 3
        self.player_max_health = 3
        self.health_regen_timer = 0   # slow regen over time
        self.invincibility_frames = 0  # brief invincibility after hit
        self.game_over         = False
        self.game_over_timer   = 0

        # ── SOUND EFFECTS ─────────────────────────────────────────────────
        self.sfx = {}
        try:
            sr = 44100; bits = -16; ch = 1; sz = 512
            pygame.mixer.pre_init(sr, bits, ch, sz)
            def make_tone(freq, dur, vol=0.4, wave='sine', decay=True):
                """Generate a simple tone as a Sound object."""
                frames = int(sr * dur)
                buf = bytearray(frames * 2)
                for i in range(frames):
                    t2 = i / sr
                    if wave == 'sine':
                        s2 = math.sin(2*math.pi*freq*t2)
                    elif wave == 'square':
                        s2 = 1.0 if math.sin(2*math.pi*freq*t2) > 0 else -1.0
                    elif wave == 'noise':
                        s2 = random.uniform(-1,1)
                    else:
                        s2 = math.sin(2*math.pi*freq*t2)
                    if decay: s2 *= max(0, 1 - i/frames)
                    s2 = max(-1, min(1, s2 * vol))
                    v = int(s2 * 32767)
                    buf[i*2]   = v & 0xFF
                    buf[i*2+1] = (v >> 8) & 0xFF
                snd = pygame.sndarray.make_sound(
                    __import__('array').array('h', [
                        int(math.sin(2*math.pi*freq*(i/sr)) * 32767 * vol * max(0, 1-i/frames if decay else 1))
                        for i in range(frames)
                    ])
                )
                return snd
            self.sfx['jump']   = make_tone(440, 0.12, 0.3, 'sine')
            self.sfx['shoot']  = make_tone(880, 0.07, 0.2, 'square')
            self.sfx['coin']   = make_tone(660, 0.10, 0.3, 'sine')
            self.sfx['hit']    = make_tone(150, 0.18, 0.4, 'noise')
            self.sfx['death']  = make_tone(200, 0.35, 0.4, 'sine', decay=True)
            self.sfx['gem']    = make_tone(880, 0.15, 0.3, 'sine')
            self.sfx['powerup']= make_tone(523, 0.20, 0.4, 'sine')
        except Exception as e:
            print(f"SFX init skipped: {e}")

        # ── PAUSE ─────────────────────────────────────────────────────────
        self.paused            = False
        self.pause_option      = 0   # 0=resume 1=menu 2=save

        # ── HIGH SCORE ────────────────────────────────────────────────────
        self.high_score        = 0   # highest single-run coin total
        self.run_coins         = 0   # coins earned this run only
        self.runs_completed    = 0

        # ── LEVEL NAME BANNER ─────────────────────────────────────────────
        self.level_banner_timer = 0
        self.level_banner_name  = ''
        self.LEVEL_NAMES = {
            0:  "Level 1 — First Steps",       1:  "Level 2 — Stairway",
            2:  "Level 3 — The Climb",         3:  "Level 4 — Danger Zone",
            4:  "Level 5 — FLYING BOSS",       5:  "Level 6 — The Long Road",
            6:  "Level 7 — The Pit",           7:  "Level 8 — The Tower",
            8:  "Level 9 — Chaos Bridge",      9:  "Level 10 — BOSS FIGHT",
            10: "Level 11 — The Gauntlet",     11: "Level 12 — The Maze",
            12: "Level 13 — Speed Run",        13: "Level 14 — All In",
            14: "Level 15 — FINAL BOSS",       15: "Level 16 — Into the Woods",
            16: "Level 17 — Dark Trees",       17: "Level 18 — The Deep",
            18: "Level 19 — Lost Path",        19: "Level 20 — Halfway",
            20: "Level 21 — Ancient Grove",    21: "Level 22 — Twisted Roots",
            22: "Level 23 — The Canopy",       23: "Level 24 — Thorns",
            24: "Level 25 — Red Guy Lurks",    25: "Level 26 — Shadow Walk",
            26: "Level 27 — The Fortress",     27: "Level 28 — Almost There",
            28: "Level 29 — Final Approach",   29: "Level 30 — RED GUY'S LAIR",
        }

        # ── PARALLAX CLOUDS ───────────────────────────────────────────────
        self.clouds = [
            {'x': i * 280 + random.randint(0,200), 'y': 80 + random.randint(0,120),
             'w': 80 + random.randint(0,80), 'speed': 0.3 + random.uniform(0,0.3),
             'layer': random.randint(0,2)}
            for i in range(14)
        ]
        self.selected_option = 0
        self.start_level = 1
        self.particles = []
        self.menu_gradient = 0

        # Cutscene tracking
        self.cutscene_mode = None
        self.cutscene_timer = 0
        self.cutscenes_seen = set()

        # ── PERSISTENT BANK (survives level changes) ──────────────────────
        self.bank_coins   = 0      # Total coins ever earned
        self.shop_coins   = 0      # Spendable coins in shop
        self.levels_beaten = set() # Which levels have been completed

        # ── STICKERS (1 hidden per level, 30 total) ───────────────────────
        self.stickers_found = set()   # level indices where sticker was found
        STICKER_EMOJIS = ["⭐","🌟","💎","🔥","❄️","🍄","🎵","🎯","👑","⚡",
                          "🌈","🦋","🐉","🏆","💫","🎪","🎭","🎨","🚀","🌙",
                          "🍀","🦅","💜","🌺","⚔️","🛡️","🎸","🎺","🎻","🥇"]
        self.sticker_names = STICKER_EMOJIS

        # ── CLICKER (Big Blue Guy on menu) ────────────────────────────────
        self.clicker_clicks   = 0
        self.clicker_coins    = 0      # coins from clicker
        self.clicker_cps      = 0      # coins per second (upgrades)
        self.clicker_timer    = 0
        self.clicker_anim     = 0      # squeeze animation
        self.clicker_upgrades = {      # how many of each upgrade bought
            'eyes': 0, 'hat': 0, 'cape': 0, 'shoes': 0, 'auto': 0
        }

        # ── SHOP ──────────────────────────────────────────────────────────
        self.shop_open        = False
        self.shop_tab         = 0      # 0=Upgrades 1=Hats 2=Stickers

        # ── CHARACTER CUSTOMISATION ───────────────────────────────────────
        self.hat_equipped   = None     # None or hat name
        self.color_equipped = BLUE     # player body colour
        self.hats_owned     = set()
        self.colors_owned   = {BLUE}

        # Hat definitions: name, cost, draw-function key
        self.HATS = [
            {'name':'Party Hat',  'cost':30,  'key':'party'},
            {'name':'Crown',      'cost':80,  'key':'crown'},
            {'name':'Wizard Hat', 'cost':60,  'key':'wizard'},
            {'name':'Cowboy',     'cost':50,  'key':'cowboy'},
            {'name':'Halo',       'cost':100, 'key':'halo'},
        ]
        # Colour skins
        self.COLORS = [
            {'name':'Blue (default)', 'cost':0,   'col':BLUE},
            {'name':'Red',            'cost':40,  'col':RED},
            {'name':'Green',          'cost':40,  'col':GREEN},
            {'name':'Purple',         'cost':60,  'col':PURPLE},
            {'name':'Orange',         'cost':60,  'col':ORANGE},
            {'name':'Cyan',           'cost':80,  'col':CYAN},
            {'name':'Gold',           'cost':120, 'col':YELLOW},
        ]

        # ── WORLD MAP ─────────────────────────────────────────────────────
        self.map_open   = False
        self.house_open = False
        self.house_room = 'living'   # living, bedroom, kitchen
        self.tv_on      = False
        self.tv_channel = 0
        self.tv_timer   = 0
        
        # MUSIC! Load music files if they exist
        pygame.mixer.init()
        import os
        
        # Get the directory where the game is running
        game_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"🎵 Looking for music files in: {game_dir}")
        
        self.music_loaded = False
        self.menu_music = None
        self.cutscene1_music = None
        self.cutscene2_music = None
        self.cutscene3_music = None
        
        # Try to load menu/gameplay music
        menu_path = os.path.join(game_dir, "menu_music.mp3")
        try:
            if os.path.exists(menu_path):
                self.menu_music = pygame.mixer.Sound(menu_path)
                self.music_loaded = True
                print(f"✅ Menu music loaded from: {menu_path}")
            else:
                print(f"❌ File not found: {menu_path}")
                print("   Put menu_music.mp3 in the same folder as the game!")
        except Exception as e:
            print(f"❌ Error loading menu music: {e}")
        
        # Try to load cutscene music/voice acting
        cutscene1_path = os.path.join(game_dir, "cutscene1.mp3")
        try:
            if os.path.exists(cutscene1_path):
                self.cutscene1_music = pygame.mixer.Sound(cutscene1_path)
                print(f"✅ Cutscene 1 audio loaded!")
            else:
                print(f"❌ cutscene1.mp3 not found (optional)")
        except Exception as e:
            print(f"❌ Error loading cutscene 1: {e}")
        
        cutscene2_path = os.path.join(game_dir, "cutscene2.mp3")
        try:
            if os.path.exists(cutscene2_path):
                self.cutscene2_music = pygame.mixer.Sound(cutscene2_path)
                print(f"✅ Cutscene 2 audio loaded!")
            else:
                print(f"❌ cutscene2.mp3 not found (optional)")
        except Exception as e:
            print(f"❌ Error loading cutscene 2: {e}")
        
        cutscene3_path = os.path.join(game_dir, "cutscene3.mp3")
        try:
            if os.path.exists(cutscene3_path):
                self.cutscene3_music = pygame.mixer.Sound(cutscene3_path)
                print(f"✅ Cutscene 3 audio loaded!")
            else:
                print(f"❌ cutscene3.mp3 not found (optional)")
        except Exception as e:
            print(f"❌ Error loading cutscene 3: {e}")
        
        # Cutscene 4: Gas Station (after level 5)
        self.cutscene4_music = None
        cutscene4_path = os.path.join(game_dir, "cutscene4.mp3")
        try:
            if os.path.exists(cutscene4_path):
                self.cutscene4_music = pygame.mixer.Sound(cutscene4_path)
                print(f"✅ Cutscene 4 audio loaded!")
            else:
                print(f"❌ cutscene4.mp3 not found (optional)")
        except Exception as e:
            print(f"❌ Error loading cutscene 4: {e}")
        
        # Cutscene 5: Boss Fight (before level 10)
        self.cutscene5_music = None
        cutscene5_path = os.path.join(game_dir, "cutscene5.mp3")
        try:
            if os.path.exists(cutscene5_path):
                self.cutscene5_music = pygame.mixer.Sound(cutscene5_path)
                print(f"✅ Cutscene 5 audio loaded!")
            else:
                print(f"❌ cutscene5.mp3 not found (optional)")
        except Exception as e:
            print(f"❌ Error loading cutscene 5: {e}")
        
        # Cutscene 6: Woods World (after level 15, before 16)
        self.cutscene6_music = None
        cutscene6_path = os.path.join(game_dir, "cutscene6.mp3")
        try:
            if os.path.exists(cutscene6_path):
                self.cutscene6_music = pygame.mixer.Sound(cutscene6_path)
                print(f"✅ Cutscene 6 audio loaded!")
            else:
                print(f"❌ cutscene6.mp3 not found (optional)")
        except Exception as e:
            print(f"❌ Error loading cutscene 6: {e}")
        
        # Cutscene 7: Final Boss (before level 30)
        self.cutscene7_music = None
        cutscene7_path = os.path.join(game_dir, "cutscene7.mp3")
        try:
            if os.path.exists(cutscene7_path):
                self.cutscene7_music = pygame.mixer.Sound(cutscene7_path)
                print(f"✅ Cutscene 7 audio loaded!")
            else:
                print(f"❌ cutscene7.mp3 not found (optional)")
        except Exception as e:
            print(f"❌ Error loading cutscene 7: {e}")
        
        self.current_music = None  # Track what's playing
        print("🎵 Music system ready!")

        # ── AUTO LOAD SAVE ────────────────────────────────────────────────
        self.load_game()
        self.save_notif = 0  # frames to show "SAVED!" notification
        # Now safe to load the starting level — all data dicts are ready
        self.load_level(self.current_level)
        if not self.music_loaded:
            print("⚠️  No music will play - add menu_music.mp3 to enable music!")
    
    def create_tutorial_level(self):
        return {
            'platforms': [
                pygame.Rect(0, 700, 200, 68),
                pygame.Rect(300, 600, 150, 20),
                pygame.Rect(500, 500, 150, 20),
                pygame.Rect(750, 400, 200, 20),
                pygame.Rect(1000, 300, 200, 468),
            ],
            'enemies': [
                Enemy(320, 580, 100),
            ],
            'boss': None,
            'coins': [
                Coin(350, 570), Coin(550, 470), Coin(800, 370)
            ],
            'spikes': [
                Spike(250, 680), Spike(270, 680)
            ],
            'spawn': (50, 650),
            'exit': (1050, 250)
        }
    
    def create_levels(self):
        levels = []
        
        # LEVEL 1 - Tutorial: Learn the basics (SHORT and EASY)
        level1 = {
            'platforms': [
                pygame.Rect(0, 700, 300, 68),
                pygame.Rect(350, 650, 200, 20),
                pygame.Rect(600, 600, 200, 20),
                pygame.Rect(850, 550, 200, 20),
                pygame.Rect(1100, 500, 300, 268),
            ],
            'moving_platforms': [],
            'enemies': [],
            'npcs': [NPC(130, 670, 0), NPC(610, 572, 2)],
            'coins': [Coin(420, 620), Coin(670, 570), Coin(920, 520)],
            'power_ups': [],
            'power_ups': [], 'spikes': [],
            'spawn': (50, 650),
            'exit': (1200, 450),
            'boss': None,
            'flying_boss': None
        }
        levels.append(level1)
        # LEVEL 2 - Easy stairs
        level2 = {
            'platforms': [
                pygame.Rect(0, 700, 250, 68),
                pygame.Rect(300, 650, 150, 20),
                pygame.Rect(500, 600, 150, 20),
                pygame.Rect(700, 550, 150, 20),
                pygame.Rect(900, 500, 200, 268),
            ],
            'moving_platforms': [],
            'enemies': [Enemy(320, 630, 80)],
            'coins': [Coin(350, 620), Coin(550, 570), Coin(750, 520)],
            'power_ups': [],
            'spikes': [],
            'spawn': (50, 650),
            'exit': (1000, 450),
            'boss': None,
            'flying_boss': None,
            'world': 'normal'
        }
        levels.append(level2)
        
        # LEVEL 3
        level3 = {
            'platforms': [
                pygame.Rect(0, 700, 200, 68),
                pygame.Rect(250, 650, 150, 20),
                pygame.Rect(600, 550, 150, 20),
                pygame.Rect(950, 450, 200, 318),
            ],
            'moving_platforms': [MovingPlatform(400, 600, 120, 15, move_x_range=150, speed=2)],
            'enemies': [],
            'coins': [Coin(300, 620), Coin(650, 520), Coin(1000, 420)],
            'power_ups': [PowerUp(450, 570, 'speed')],
            'spikes': [],
            'spawn': (50, 650),
            'exit': (1050, 400),
            'boss': None,
            'flying_boss': None,
            'world': 'normal'
        }
        levels.append(level3)
        
        # LEVEL 4
        level4 = {
            'platforms': [
                pygame.Rect(0, 700, 200, 68),
                pygame.Rect(250, 650, 150, 20),
                pygame.Rect(450, 550, 150, 20),  # Safe platform instead of buggy moving one!
                pygame.Rect(650, 500, 150, 20),
                pygame.Rect(850, 400, 150, 20),  # Extra platform
                pygame.Rect(1050, 350, 250, 418),
            ],
            'moving_platforms': [],  # REMOVED buggy platform!
            'enemies': [Enemy(670, 480, 100)],
            'coins': [Coin(300, 620), Coin(500, 520), Coin(700, 470), Coin(900, 370), Coin(1100, 320)],
            'power_ups': [],
            'spikes': [Spike(550, 680), Spike(570, 680)],
            'spawn': (50, 650),
            'exit': (1150, 300),
            'boss': None,
            'flying_boss': None,
            'world': 'normal'
        }
        levels.append(level4)
        
        # LEVEL 5 - Flying Boss
        level5 = {
            'platforms': [
                pygame.Rect(0, 700, 200, 68),
                pygame.Rect(250, 650, 900, 118),  # Boss arena floor
            ],
            'moving_platforms': [
                MovingPlatform(400, 200, 100, 15, move_y_range=350, speed=3),
                MovingPlatform(650, 250, 100, 15, move_y_range=350, speed=3),
                MovingPlatform(900, 200, 100, 15, move_y_range=350, speed=3),
            ],
            'enemies': [],
            'coins': [Coin(450, 300), Coin(700, 300), Coin(950, 300)],
            'power_ups': [PowerUp(575, 620, 'mega_jump')],  # ABOVE the floor!
            'spikes': [],
            'spawn': (50, 650),
            'exit': (700, 620),  # ABOVE the floor!
            'boss': None,
            'flying_boss': FlyingBoss(650, 300, health=5),
            'world': 'normal'
        }
        levels.append(level5)
        
        # LEVEL 6 - The Long Road: lots of platforms, enemies patrolling
        level6 = {
            'platforms': [
                pygame.Rect(0, 700, 200, 68),
                pygame.Rect(250, 650, 130, 20), pygame.Rect(450, 620, 130, 20),
                pygame.Rect(650, 590, 130, 20), pygame.Rect(850, 560, 130, 20),
                pygame.Rect(1050, 530, 130, 20), pygame.Rect(1250, 500, 130, 20),
                pygame.Rect(1450, 470, 130, 20), pygame.Rect(1650, 440, 130, 20),
                pygame.Rect(1850, 410, 300, 358),
            ],
            'moving_platforms': [],
            'enemies': [Enemy(270, 622, 80), FastEnemy(670, 562, 120), Enemy(1070, 502, 80), FastEnemy(1470, 442, 120)],
            'coins': [Coin(290, 620), Coin(490, 590), Coin(690, 560), Coin(890, 530), Coin(1090, 500), Coin(1290, 470), Coin(1490, 440), Coin(1690, 410)],
            'power_ups': [PowerUp(890, 530, 'speed')],
            'spikes': [Spike(370, 680), Spike(570, 680), Spike(970, 680), Spike(1170, 680), Spike(1570, 680)],
            'spawn': (50, 640), 'exit': (1950, 380),
            'boss': None, 'flying_boss': None, 'world': 'normal'
        }
        levels.append(level6)

        # LEVEL 7 - The Pit: platforms over a deadly spike pit (with safe gaps!)
        level7 = {
            'platforms': [
                pygame.Rect(0, 700, 200, 68),
                pygame.Rect(220, 590, 130, 20),
                pygame.Rect(420, 540, 130, 20),
                pygame.Rect(620, 490, 130, 20),
                pygame.Rect(820, 540, 130, 20),
                pygame.Rect(1020, 490, 130, 20),
                pygame.Rect(1220, 440, 130, 20),
                pygame.Rect(1420, 490, 130, 20),
                pygame.Rect(1620, 350, 300, 418),
            ],
            'moving_platforms': [
                MovingPlatform(320, 460, 110, 15, move_y_range=100, speed=2),
                MovingPlatform(720, 420, 110, 15, move_y_range=100, speed=2),
                MovingPlatform(1120, 380, 110, 15, move_y_range=100, speed=2),
            ],
            'enemies': [Enemy(240, 562, 80), Enemy(640, 462, 80), Enemy(1240, 412, 80)],
            'coins': [Coin(270, 560), Coin(450, 510), Coin(650, 460), Coin(850, 510), Coin(1050, 460), Coin(1250, 410)],
            'power_ups': [PowerUp(650, 460, 'mega_jump')],
            # Spikes with SAFE GAPS under each platform so you can land safely
            'spikes': (
                [Spike(s, 682) for s in range(200, 215, 20)] +   # tiny start
                [Spike(s, 682) for s in range(370, 415, 20)] +   # gap 1
                [Spike(s, 682) for s in range(570, 615, 20)] +   # gap 2
                [Spike(s, 682) for s in range(770, 815, 20)] +   # gap 3
                [Spike(s, 682) for s in range(970, 1015, 20)] +  # gap 4
                [Spike(s, 682) for s in range(1170, 1215, 20)] + # gap 5
                [Spike(s, 682) for s in range(1370, 1415, 20)] + # gap 6
                [Spike(s, 682) for s in range(1570, 1615, 20)]   # end
            ),
            'spawn': (50, 650), 'exit': (1720, 318),
            'boss': None, 'flying_boss': None, 'world': 'normal'
        }
        levels.append(level7)

        # LEVEL 8 - The Tower: climb straight UP, platforms going vertical
        level8 = {
            'platforms': [
                pygame.Rect(0, 700, 300, 68),
                pygame.Rect(40, 620, 180, 20), pygame.Rect(240, 545, 180, 20),
                pygame.Rect(40, 470, 180, 20), pygame.Rect(240, 395, 180, 20),
                pygame.Rect(40, 320, 180, 20), pygame.Rect(240, 245, 180, 20),
                pygame.Rect(40, 170, 180, 20),
                pygame.Rect(350, 100, 150, 20),  # Small top platform — exit is HERE, not blocking
            ],
            'moving_platforms': [
                MovingPlatform(180, 580, 130, 15, move_x_range=100, speed=2),
                MovingPlatform(140, 430, 130, 15, move_x_range=100, speed=2),
                MovingPlatform(180, 275, 130, 15, move_x_range=100, speed=2),
            ],
            'enemies': [Enemy(260, 415, 80), Enemy(60, 190, 80)],
            'coins': [Coin(80, 590), Coin(270, 515), Coin(80, 440), Coin(270, 365), Coin(80, 290), Coin(270, 215), Coin(80, 140)],
            'power_ups': [PowerUp(270, 215, 'invincible'), PowerUp(80, 440, 'mega_jump')],
            'spikes': [Spike(180, 680), Spike(200, 680), Spike(220, 680)],
            'spawn': (50, 640), 'exit': (370, 70),
            'boss': None, 'flying_boss': None, 'world': 'normal'
        }
        levels.append(level8)

        # LEVEL 9 - Chaos Bridge: narrow platforms with enemies AND spikes below
        level9 = {
            'platforms': [
                pygame.Rect(0, 700, 180, 68),
                pygame.Rect(230, 640, 90, 20), pygame.Rect(390, 590, 90, 20),
                pygame.Rect(550, 540, 90, 20), pygame.Rect(710, 590, 90, 20),
                pygame.Rect(870, 540, 90, 20), pygame.Rect(1030, 490, 90, 20),
                pygame.Rect(1190, 540, 90, 20), pygame.Rect(1350, 490, 90, 20),
                pygame.Rect(1510, 440, 90, 20), pygame.Rect(1670, 390, 90, 20),
                pygame.Rect(1830, 340, 280, 428),
            ],
            'moving_platforms': [
                MovingPlatform(460, 400, 90, 15, move_x_range=80, speed=3),
                MovingPlatform(920, 380, 90, 15, move_x_range=80, speed=3),
                MovingPlatform(1380, 360, 90, 15, move_x_range=80, speed=3),
            ],
            'enemies': [Enemy(250, 612, 60), Enemy(570, 512, 60), Enemy(890, 512, 60), Enemy(1210, 512, 60), Enemy(1530, 412, 60)],
            'coins': [Coin(250, 610), Coin(410, 560), Coin(570, 510), Coin(730, 560), Coin(890, 510), Coin(1050, 460), Coin(1210, 510), Coin(1370, 460), Coin(1530, 410)],
            'power_ups': [PowerUp(1050, 460, 'speed')],
            'spikes': [Spike(s, 680) for s in range(180, 1830, 30)],
            'spawn': (50, 640), 'exit': (1920, 310),
            'boss': None, 'flying_boss': None, 'world': 'normal'
        }
        levels.append(level9)

        # LEVEL 10 - BOSS FIGHT: Walking Red Guy
        level10 = {
            'platforms': [
                pygame.Rect(0, 700, 200, 68),
                pygame.Rect(200, 650, 900, 18),  # Arena floor
                pygame.Rect(300, 500, 150, 20), pygame.Rect(650, 420, 150, 20),  # High ground
            ],
            'moving_platforms': [],
            'enemies': [],
            'coins': [Coin(350, 470), Coin(700, 390)],
            'power_ups': [PowerUp(400, 620, 'invincible'), PowerUp(750, 620, 'mega_jump')],
            'spikes': [],
            'spawn': (50, 630), 'exit': (950, 620),
            'boss': Boss(700, 600, health=5), 'flying_boss': None, 'world': 'normal'
        }
        levels.append(level10)

        # LEVEL 11 - The Gauntlet: enemies EVERYWHERE, tight spaces
        level11 = {
            'platforms': [
                pygame.Rect(0, 700, 200, 68),
                pygame.Rect(220, 650, 110, 20), pygame.Rect(400, 600, 110, 20),
                pygame.Rect(580, 550, 110, 20), pygame.Rect(760, 500, 110, 20),
                pygame.Rect(940, 450, 110, 20), pygame.Rect(1120, 400, 110, 20),
                pygame.Rect(1300, 350, 110, 20), pygame.Rect(1480, 300, 110, 20),
                pygame.Rect(1660, 250, 110, 20), pygame.Rect(1840, 200, 280, 568),
            ],
            'moving_platforms': [
                MovingPlatform(490, 350, 100, 15, move_x_range=120, speed=2),
                MovingPlatform(1030, 280, 100, 15, move_x_range=120, speed=2),
            ],
            'enemies': [Enemy(240, 622, 80), FastEnemy(420, 572, 100), ShieldEnemy(600, 522, 80),
                        JumperEnemy(780, 472, 80), Enemy(960, 422, 80), ShieldEnemy(1140, 372, 80),
                        FastEnemy(1320, 322, 100), JumperEnemy(1500, 272, 80)],
            'coins': [Coin(250, 620), Coin(430, 570), Coin(610, 520), Coin(790, 470), Coin(970, 420), Coin(1150, 370), Coin(1330, 320), Coin(1510, 270), Coin(1680, 220)],
            'power_ups': [PowerUp(790, 470, 'invincible')],
            'spikes': [Spike(340, 680), Spike(520, 680), Spike(700, 680), Spike(880, 680), Spike(1060, 680), Spike(1240, 680), Spike(1420, 680), Spike(1600, 680)],
            'spawn': (50, 640), 'exit': (1930, 170),
            'boss': None, 'flying_boss': None, 'world': 'normal'
        }
        levels.append(level11)

        # LEVEL 12 - The Maze: platforms going up AND down, confusing layout
        level12 = {
            'platforms': [
                pygame.Rect(0, 700, 200, 68),
                pygame.Rect(220, 600, 120, 20), pygame.Rect(420, 500, 120, 20),
                pygame.Rect(620, 600, 120, 20), pygame.Rect(820, 500, 120, 20),
                pygame.Rect(1020, 400, 120, 20), pygame.Rect(1220, 500, 120, 20),
                pygame.Rect(1420, 400, 120, 20), pygame.Rect(1620, 300, 120, 20),
                pygame.Rect(1820, 400, 120, 20), pygame.Rect(2020, 300, 280, 468),
            ],
            'moving_platforms': [
                MovingPlatform(320, 350, 100, 15, move_y_range=180, speed=2),
                MovingPlatform(720, 350, 100, 15, move_y_range=180, speed=2),
                MovingPlatform(1120, 280, 100, 15, move_y_range=180, speed=2),
                MovingPlatform(1720, 250, 100, 15, move_y_range=180, speed=2),
            ],
            'enemies': [Enemy(240, 572, 90), Enemy(640, 572, 90), Enemy(1040, 372, 90), Enemy(1640, 272, 90), Enemy(1840, 372, 90)],
            'coins': [Coin(240, 570), Coin(440, 470), Coin(640, 570), Coin(840, 470), Coin(1040, 370), Coin(1240, 470), Coin(1440, 370), Coin(1640, 270), Coin(1840, 370)],
            'power_ups': [PowerUp(1040, 370, 'speed'), PowerUp(1640, 270, 'mega_jump')],
            'spikes': [Spike(360, 680), Spike(760, 680), Spike(1160, 680), Spike(1560, 680), Spike(1960, 680)],
            'spawn': (50, 640), 'exit': (2100, 270),
            'boss': None, 'flying_boss': None, 'world': 'normal'
        }
        levels.append(level12)

        # LEVEL 13 - Speed Run: fast moving platforms, wide gaps, must keep moving
        level13 = {
            'platforms': [
                pygame.Rect(0, 700, 180, 68),
                pygame.Rect(220, 580, 100, 20), pygame.Rect(550, 500, 100, 20),
                pygame.Rect(900, 420, 100, 20), pygame.Rect(1250, 340, 100, 20),
                pygame.Rect(1600, 260, 100, 20), pygame.Rect(1950, 180, 280, 588),
            ],
            'moving_platforms': [
                MovingPlatform(380, 280, 110, 15, move_x_range=140, speed=4),
                MovingPlatform(720, 280, 110, 15, move_x_range=140, speed=4),
                MovingPlatform(1060, 280, 110, 15, move_x_range=140, speed=4),
                MovingPlatform(1400, 280, 110, 15, move_x_range=140, speed=4),
                MovingPlatform(1750, 280, 110, 15, move_y_range=140, speed=4),
            ],
            'enemies': [Enemy(240, 552, 90), Enemy(570, 472, 90), Enemy(920, 392, 90), Enemy(1270, 312, 90), Enemy(1620, 232, 90)],
            'coins': [Coin(240, 550), Coin(430, 380), Coin(570, 470), Coin(770, 380), Coin(920, 390), Coin(1110, 380), Coin(1270, 310), Coin(1620, 230)],
            'power_ups': [PowerUp(770, 360, 'speed'), PowerUp(1110, 360, 'speed')],
            'spikes': [Spike(s, 680) for s in range(180, 1950, 50)],
            'spawn': (50, 640), 'exit': (2040, 150),
            'boss': None, 'flying_boss': None, 'world': 'normal'
        }
        levels.append(level13)

        # LEVEL 14 - Before the Boss: hardest normal level, everything at once
        level14 = {
            'platforms': [
                pygame.Rect(0, 700, 160, 68),
                pygame.Rect(200, 645, 90, 20), pygame.Rect(360, 595, 90, 20),
                pygame.Rect(520, 545, 90, 20), pygame.Rect(680, 495, 90, 20),
                pygame.Rect(840, 445, 90, 20), pygame.Rect(1000, 395, 90, 20),
                pygame.Rect(1160, 345, 90, 20), pygame.Rect(1320, 295, 90, 20),
                pygame.Rect(1480, 245, 90, 20), pygame.Rect(1640, 195, 90, 20),
                pygame.Rect(1800, 145, 280, 623),
            ],
            'moving_platforms': [
                MovingPlatform(290, 380, 80, 15, move_x_range=100, speed=3),
                MovingPlatform(770, 320, 80, 15, move_y_range=160, speed=3),
                MovingPlatform(1250, 250, 80, 15, move_x_range=100, speed=3),
                MovingPlatform(1570, 160, 80, 15, move_y_range=120, speed=3),
            ],
            'enemies': [Enemy(220, 617, 70), Enemy(380, 567, 70), Enemy(540, 517, 70),
                        Enemy(700, 467, 70), Enemy(860, 417, 70), Enemy(1020, 367, 70),
                        Enemy(1180, 317, 70), Enemy(1340, 267, 70), Enemy(1500, 217, 70)],
            'coins': [Coin(220, 615), Coin(380, 565), Coin(540, 515), Coin(700, 465), Coin(860, 415), Coin(1020, 365), Coin(1180, 315), Coin(1340, 265), Coin(1500, 215), Coin(1660, 165)],
            'power_ups': [PowerUp(700, 465, 'speed'), PowerUp(1180, 315, 'invincible')],
            'spikes': [Spike(s, 680) for s in range(160, 1800, 25)],
            'spawn': (50, 640), 'exit': (1880, 115),
            'boss': None, 'flying_boss': None, 'world': 'normal'
        }
        levels.append(level14)
        
        # LEVEL 15 - FINAL BOSS
        level15 = {
            'platforms': [
                pygame.Rect(0, 700, 200, 68),
                pygame.Rect(250, 660, 1000, 108),  # arena floor
            ],
            'moving_platforms': [
                MovingPlatform(400, 200, 100, 15, move_y_range=380, speed=3),
                MovingPlatform(600, 250, 100, 15, move_y_range=380, speed=3),
                MovingPlatform(800, 200, 100, 15, move_y_range=380, speed=3),
                MovingPlatform(1000, 250, 100, 15, move_y_range=380, speed=3),
            ],
            'enemies': [],
            'coins': [Coin(450, 300), Coin(650, 300), Coin(850, 300), Coin(1050, 300)],
            'power_ups': [PowerUp(500, 620, 'mega_jump'), PowerUp(800, 620, 'invincible')],
            'spikes': [],
            'spawn': (50, 630),
            'exit': (1050, 615),
            'boss': None,
            'flying_boss': FlyingBoss(700, 300, health=8),
            'world': 'normal'
        }
        levels.append(level15)
        
        # WOODS WORLD - Levels 16-30 (VERY DIFFERENT!)
        for i in range(16, 31):
            platforms = [pygame.Rect(0, 700, 200, 68)]
            x, y = 250, 650
            num_platforms = 15 + (i - 16)
            
            # Different pattern for each level!
            pattern = (i - 16) % 5
            
            for j in range(num_platforms):
                platform_width = 120 if pattern != 2 else 80  # Narrower platforms on pattern 2
                platforms.append(pygame.Rect(x, y, platform_width, 20))
                
                # Different movement patterns!
                if pattern == 0:  # Stairs up
                    x += 180
                    y -= 60 if j % 2 == 0 else -20
                elif pattern == 1:  # Zigzag
                    x += 200
                    y -= 70 if j % 3 == 0 else (-50 if j % 3 == 1 else 40)
                elif pattern == 2:  # Narrow jumps
                    x += 220
                    y -= 50 if j % 2 == 0 else -30
                elif pattern == 3:  # Wide gaps
                    x += 240
                    y -= 55 if j % 2 == 0 else -35
                else:  # Pattern 4 - mixed
                    x += 190 + (j % 3) * 10
                    y -= 65 if j % 2 == 0 else -25
                
                # Keep in bounds
                if y < 250: y = 350
                if y > 650: y = 550
            
            platforms.append(pygame.Rect(x, y, 300, 768 - y))
            
            # More varied moving platforms!
            moving_plats = []
            if i % 3 == 1:
                moving_plats.append(MovingPlatform(500, 500, 100, 15, move_x_range=150, speed=2))
            if i % 4 == 2:
                moving_plats.append(MovingPlatform(800, 400, 100, 15, move_y_range=200, speed=2))
            
            # More enemies in later levels — mix of types!
            enemies_list = []
            num_enemies = (i - 15) // 2 + 1
            for k in range(num_enemies):
                enemy_x = 300 + k * 350
                enemy_y = 630 - (k % 4) * 80
                # Rotate enemy types based on level and position
                etype = (i + k) % 4
                if etype == 0:   enemies_list.append(Enemy(enemy_x, enemy_y, 80))
                elif etype == 1: enemies_list.append(FastEnemy(enemy_x, enemy_y, 100))
                elif etype == 2: enemies_list.append(ShieldEnemy(enemy_x, enemy_y, 70))
                else:            enemies_list.append(JumperEnemy(enemy_x, enemy_y, 90))
            
            # More coins!
            coins_list = []
            num_coins = min(10, i - 14)
            for j in range(num_coins):
                coin_x = 300 + j * 220
                coin_y = 620 - (j % 5) * 60
                coins_list.append(Coin(coin_x, coin_y))
            
            # Power-ups every 3 levels
            power_ups_list = []
            if i % 3 == 0:
                power_ups_list.append(PowerUp(x - 400, y - 80, ['speed', 'invincible', 'mega_jump'][(i // 3) % 3]))
            
            # More spikes in later levels!
            spikes_list = []
            num_spike_groups = (i - 15) // 3
            for k in range(num_spike_groups):
                spike_x = 400 + k * 400
                spikes_list.append(Spike(spike_x, 680))
                spikes_list.append(Spike(spike_x + 20, 680))
                if i > 25:  # Extra spikes in final levels
                    spikes_list.append(Spike(spike_x + 40, 680))
            
            level = {
                'platforms': platforms,
                'moving_platforms': moving_plats,
                'enemies': enemies_list,
                'coins': coins_list,
                'power_ups': power_ups_list,
                'spikes': spikes_list,
                'spawn': (50, 650),
                'exit': (x + 100, y - 50),
                'boss': None,
                'flying_boss': None,
                'world': 'woods'
            }
            levels.append(level)
        
        return levels
        
        return levels
    
    def load_level(self, level_index):
        if level_index >= len(self.levels):
            self.game_completed = True
            return
        level = self.levels[level_index]
        self.platforms = level['platforms'] + level.get('moving_platforms', [])
        self.moving_platforms = level.get('moving_platforms', [])
        self.enemies = level['enemies'][:]
        self.boss = level.get('boss')
        self.flying_boss = level.get('flying_boss')
        self.coins = level['coins'][:]
        self.power_ups = level.get('power_ups', [])
        self.spikes = level['spikes'][:]
        self.player = Player(*level['spawn'])
        self.player.color = getattr(self, 'color_equipped', BLUE)
        self.exit_rect = pygame.Rect(level['exit'][0], level['exit'][1], 40, 40)
        self.projectiles = []
        self.coins_collected = 0
        self.total_coins = len(self.coins)
        self.boss_defeated = False
        self.npcs = level.get('npcs', [])[:]
        # Level name banner
        self.level_banner_timer = 180
        self.level_banner_name  = self.LEVEL_NAMES.get(level_index, f"Level {level_index+1}")
        # Gentle health regen between levels
        self.player_health = min(self.player_max_health, getattr(self,'player_health',3) + 1)
        self.game_over = False
        self.invincibility_frames = 60  # brief grace period on level start

        # Place sticker ON a real platform so it's always reachable
        self._sticker_anim = 0
        plats = level['platforms']
        seed = level_index * 137 + 42
        pick = (seed % max(1, len(plats) - 1)) + 1
        pick = min(pick, len(plats) - 1)
        p = plats[pick]
        self._sticker_rect = pygame.Rect(
            p.x + p.width // 2 - 12,
            p.y - 30,
            24, 24
        )

        # Spawn gems — 1 or 2 per level at interesting spots
        self.gems = []
        self.gems_collected = 0
        gx = level['exit'][0] - 150; gy = level['exit'][1] - 60
        self.gems.append(Gem(gx, gy, level_index % 4))
        if level_index % 3 == 0 and len(plats) > 3:
            gp = plats[len(plats)//2]
            self.gems.append(Gem(gp.x + gp.width//2 - 8, gp.y - 30, (level_index+2) % 4))
    
    def load_tutorial_level(self):
        level = self.tutorial_level
        self.platforms = level['platforms']
        self.enemies = level['enemies'][:]
        self.boss = level.get('boss')
        self.coins = level['coins'][:]
        self.spikes = level['spikes'][:]
        self.player = Player(*level['spawn'])
        self.exit_rect = pygame.Rect(level['exit'][0], level['exit'][1], 40, 40)
        self.projectiles = []
        self.coins_collected = 0
        self.total_coins = len(self.coins)
    
    def update_camera(self):
        target_x = self.player.x - SCREEN_WIDTH // 2 if self.state in ['playing', 'tutorial'] else self.camera_x
        target_y = self.player.y - SCREEN_HEIGHT // 2 if self.state in ['playing', 'tutorial'] else self.camera_y
        self.camera_x += (target_x - self.camera_x) * 0.1
        self.camera_y += (target_y - self.camera_y) * 0.1
        self.camera_y = max(self.camera_y, -200)
    
    def draw_background(self):
        # Check if we're in grass world!
        is_grass_world = False
        if self.state == 'playing' and self.current_level < len(self.levels):
            is_grass_world = self.levels[self.current_level].get('world') == 'woods'
        
        if is_grass_world:
            # WOODS WORLD - Brown/green forest theme!
            for i in range(SCREEN_HEIGHT):
                progress = i / SCREEN_HEIGHT
                r = int(60 + progress * 30)
                g = int(80 + progress * 60)
                b = int(40 + progress * 20)
                pygame.draw.line(self.screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))
            
            # Tree silhouettes
            for i in range(15):
                x = i * 120 - (self.camera_x * 0.2) % 1800
                y = SCREEN_HEIGHT - 180
                # Tree trunk
                pygame.draw.rect(self.screen, (60, 40, 20), (int(x) + 40, int(y), 20, 180))
                # Tree top (triangle)
                points = [(int(x) + 50, int(y) - 40), (int(x) + 10, int(y)), (int(x) + 90, int(y))]
                pygame.draw.polygon(self.screen, (40, 80, 30), points)
            
            # Falling leaves
            for i in range(30):
                particle_x = (i * 213 - self.camera_x * 0.3) % SCREEN_WIDTH
                particle_y = (i * 137 + pygame.time.get_ticks() * 0.05) % SCREEN_HEIGHT
                pygame.draw.ellipse(self.screen, (150, 100, 50), 
                               (int(particle_x), int(particle_y), 6, 4))
        else:
            # Normal world - Epic gradient sky
            for i in range(SCREEN_HEIGHT):
                progress = i / SCREEN_HEIGHT
                r = int(20 + progress * 20)
                g = int(20 + progress * 30)
                b = int(60 + progress * 80)
                pygame.draw.line(self.screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))
            
            # Distant stars (parallax effect)
            for i in range(50):
                star_x = (i * 157 - self.camera_x * 0.05) % SCREEN_WIDTH
                star_y = (i * 97) % (SCREEN_HEIGHT // 2)
                brightness = 150 + (i * 31) % 105
                pygame.draw.circle(self.screen, (brightness, brightness, brightness), 
                                 (int(star_x), int(star_y)), 1)
            
            # Mountains in the background (parallax)
            mountain_points = []
            for i in range(15):
                x = i * 120 - (self.camera_x * 0.2) % 1800
                y = SCREEN_HEIGHT - 200 + math.sin(i * 0.5) * 50
                mountain_points.append((x, y))
                mountain_points.append((x + 60, SCREEN_HEIGHT - 100))
            
            for i in range(0, len(mountain_points) - 1, 2):
                if i + 3 < len(mountain_points):
                    points = [
                        mountain_points[i],
                        mountain_points[i + 1],
                        (mountain_points[i + 3][0], SCREEN_HEIGHT),
                        (mountain_points[i][0], SCREEN_HEIGHT)
                    ]
                    pygame.draw.polygon(self.screen, (60, 50, 80), points)
            
            # Floating particles/dust
            for i in range(30):
                particle_x = (i * 213 - self.camera_x * 0.3) % SCREEN_WIDTH
                particle_y = (i * 137 - self.camera_y * 0.1) % SCREEN_HEIGHT
                alpha = 100 + (i * 47) % 100
                size = 2 + (i % 3)
                pygame.draw.circle(self.screen, (alpha, alpha, alpha + 20), 
                                 (int(particle_x), int(particle_y)), size)
            self.draw_clouds()
    
    def draw_mini_map(self):
        level = {
            'platforms': self.platforms,
            'enemies': self.enemies,
            'boss': self.boss,
            'coins': self.coins,
            'spikes': self.spikes,
            'spawn': (self.player.x, self.player.y),
            'exit': (self.exit_rect.x, self.exit_rect.y)
        }
        map_width = 200
        map_height = 150
        map_x = SCREEN_WIDTH - map_width - 10
        map_y = SCREEN_HEIGHT - map_height - 10
        
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        if level['platforms']:
            min_x = min(min_x, min(p.x for p in level['platforms']))
            min_y = min(min_y, min(p.y for p in level['platforms']))
            max_x = max(max_x, max(p.x + p.width for p in level['platforms']))
            max_y = max(max_y, max(p.y + p.height for p in level['platforms']))
        for enemy in level['enemies']:
            min_x = min(min_x, enemy.x)
            min_y = min(min_y, enemy.y)
            max_x = max(max_x, enemy.x + enemy.width)
            max_y = max(max_y, enemy.y + enemy.height)
        if level['boss']:
            min_x = min(min_x, level['boss'].x)
            min_y = min(min_y, level['boss'].y)
            max_x = max(max_x, level['boss'].x + level['boss'].width)
            max_y = max(max_y, level['boss'].y + level['boss'].height)
        for coin in level['coins']:
            min_x = min(min_x, coin.x)
            min_y = min(min_y, coin.y)
            max_x = max(max_x, coin.x + coin.width)
            max_y = max(max_y, coin.y + coin.height)
        for spike in level['spikes']:
            min_x = min(min_x, spike.x)
            min_y = min(min_y, spike.y)
            max_x = max(max_x, spike.x + spike.width)
            max_y = max(max_y, spike.y + spike.height)
        min_x = min(min_x, level['spawn'][0], level['exit'][0])
        min_y = min(min_y, level['spawn'][1], level['exit'][1])
        max_x = max(max_x, level['spawn'][0] + 20, level['exit'][0] + 40)
        max_y = max(max_y, level['spawn'][1] + 20, level['exit'][1] + 40)
        
        if min_x == float('inf'):
            min_x, min_y = 0, 0
            max_x, max_y = SCREEN_WIDTH, SCREEN_HEIGHT
        
        padding = 50
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding
        
        level_width = max_x - min_x
        level_height = max_y - min_y
        scale_x = map_width / level_width if level_width > 0 else 0.1
        scale_y = map_height / level_height if level_height > 0 else 0.1
        scale = min(scale_x, scale_y, 0.1)
        
        pygame.draw.rect(self.screen, DARK_GRAY, (map_x, map_y, map_width, map_height))
        pygame.draw.rect(self.screen, WHITE, (map_x, map_y, map_width, map_height), 2)
        for platform in level['platforms']:
            scaled_x = map_x + (platform.x - min_x) * scale
            scaled_y = map_y + (platform.y - min_y) * scale
            scaled_w = platform.width * scale
            scaled_h = platform.height * scale
            pygame.draw.rect(self.screen, WHITE, (scaled_x, scaled_y, scaled_w, scaled_h))
        for enemy in level['enemies']:
            scaled_x = map_x + (enemy.x - min_x) * scale
            scaled_y = map_y + (enemy.y - min_y) * scale
            pygame.draw.rect(self.screen, RED, (scaled_x, scaled_y, enemy.width * scale, enemy.height * scale))
        if level['boss']:
            scaled_x = map_x + (level['boss'].x - min_x) * scale
            scaled_y = map_y + (level['boss'].y - min_y) * scale
            pygame.draw.rect(self.screen, PURPLE, (scaled_x, scaled_y, level['boss'].width * scale, level['boss'].height * scale))
        for coin in level['coins']:
            if not coin.collected:
                scaled_x = map_x + (coin.x - min_x) * scale
                scaled_y = map_y + (coin.y - min_y) * scale
                pygame.draw.rect(self.screen, YELLOW, (scaled_x, scaled_y, coin.width * scale, coin.height * scale))
        for spike in level['spikes']:
            scaled_x = map_x + (spike.x - min_x) * scale
            scaled_y = map_y + (spike.y - min_y) * scale
            pygame.draw.rect(self.screen, GRAY, (scaled_x, scaled_y, spike.width * scale, spike.height * scale))
        scaled_x = map_x + (level['exit'][0] - min_x) * scale
        scaled_y = map_y + (level['exit'][1] - min_y) * scale
        pygame.draw.rect(self.screen, GREEN, (scaled_x, scaled_y, 40 * scale, 40 * scale))
        scaled_x = map_x + (level['spawn'][0] - min_x) * scale
        scaled_y = map_y + (level['spawn'][1] - min_y) * scale
        pygame.draw.rect(self.screen, BLUE, (scaled_x, scaled_y, 20 * scale, 20 * scale))
    
    def draw_ui(self):
        t = pygame.time.get_ticks() * 0.001

        # ── Top-left HUD panel ──────────────────────────────────────────────
        panel = pygame.Surface((260, 90), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 140))
        self.screen.blit(panel, (8, 8))
        pygame.draw.rect(self.screen, (60, 80, 160), (8, 8, 260, 90), 2)

        font_hud = pygame.font.Font(None, 28)
        font_sm  = pygame.font.Font(None, 22)

        world_name = "🌲 WOODS WORLD" if self.current_level >= 15 else "⭐ NORMAL WORLD"
        world_col  = GREEN if self.current_level >= 15 else CYAN
        world_surf = font_hud.render(world_name, True, world_col)
        self.screen.blit(world_surf, (16, 15))

        lv_surf = font_hud.render(f"Level  {self.current_level + 1} / 30", True, WHITE)
        self.screen.blit(lv_surf, (16, 40))

        coin_surf = font_hud.render(f"Coins  {self.coins_collected} / {self.total_coins}", True, YELLOW)
        self.screen.blit(coin_surf, (16, 65))

        # ── Power-up status bars ────────────────────────────────────────────
        active_pups = []
        if getattr(self.player, 'speed_boost',  0) > 0: active_pups.append(('SPEED',  self.player.speed_boost,  300, ORANGE))
        if getattr(self.player, 'invincible',    0) > 0: active_pups.append(('SHIELD', self.player.invincible,   300, PURPLE))
        if getattr(self.player, 'mega_jump',     0) > 0: active_pups.append(('JUMP+',  self.player.mega_jump,    300, GREEN))

        for idx, (label, val, max_val, col) in enumerate(active_pups):
            bar_x, bar_y = 8, 108 + idx * 30
            bar_w = 180
            # Background
            pygame.draw.rect(self.screen, (40, 40, 40), (bar_x, bar_y, bar_w, 22))
            # Fill
            fill = int(bar_w * val / max_val)
            pygame.draw.rect(self.screen, col, (bar_x, bar_y, fill, 22))
            pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_w, 22), 1)
            # Label
            s = font_sm.render(label, True, WHITE)
            self.screen.blit(s, (bar_x + 4, bar_y + 4))

        # ── Controls reminder (bottom right) ───────────────────────────────
        ctrl = font_sm.render("CTRL=Shoot  SPACE=Jump  P=Pause  J=Journal  ESC=Menu", True, (80, 80, 100))
        self.screen.blit(ctrl, (SCREEN_WIDTH - ctrl.get_width() - 10, SCREEN_HEIGHT - 24))

        # ── Coin magnet indicator ────────────────────────────────────────────
        if self.coin_magnet > 0:
            pct = self.coin_magnet / 300
            pygame.draw.rect(self.screen, (20,20,40),(8,200,120,16))
            pygame.draw.rect(self.screen, (100,200,255),(8,200,int(120*pct),16))
            pygame.draw.rect(self.screen, WHITE,(8,200,120,16),1)
            self.screen.blit(font_sm.render("🧲 MAGNET",True,CYAN),(8,182))

        # ── BOSS DEFEATED banner ────────────────────────────────────────────
        if self.boss_defeated:
            pulse = abs(math.sin(t * 4)) * 80 + 175
            big_font = pygame.font.Font(None, 68)
            text = big_font.render("BOSS DEFEATED!", True, (0, int(pulse), 0))
            shadow = big_font.render("BOSS DEFEATED!", True, BLACK)
            cx = SCREEN_WIDTH // 2 - text.get_width() // 2
            self.screen.blit(shadow, (cx + 3, 153))
            self.screen.blit(text,   (cx,     150))
            med_font = pygame.font.Font(None, 36)
            t2 = med_font.render("Head to the GREEN EXIT! ▶", True, YELLOW)
            self.screen.blit(t2, (SCREEN_WIDTH // 2 - t2.get_width() // 2, 225))
    
    def draw_tutorial_ui(self):
        font = pygame.font.Font(None, 36)
        steps = [
            ("Use LEFT/RIGHT or A/D to move", self.player.x > 100),
            ("Press SPACE to jump", self.player.y < 600),
            ("Press SPACE in air for a double jump", not self.player.double_jump_available),
            ("Collect yellow coins", self.coins_collected > 0),
            ("Avoid red enemies and spikes", self.player.x > 300),
            ("Reach the green exit", False)
        ]
        current_step = min(self.tutorial_step, len(steps) - 1)
        instruction, condition = steps[current_step]
        text = font.render(instruction, True, YELLOW)
        pygame.draw.rect(self.screen, BLACK, (SCREEN_WIDTH // 2 - text.get_width() // 2 - 10, 
                                            50 - 10, text.get_width() + 20, text.get_height() + 20))
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 50))
        if condition:
            self.tutorial_step += 1
    
    def draw_intro(self):
        # Epic animated background
        for y in range(SCREEN_HEIGHT):
            p = y / SCREEN_HEIGHT
            r = int(5 + p * 15 + math.sin(self.intro_timer * 0.02 + y * 0.005) * 5)
            g = int(5 + p * 10)
            b = int(20 + p * 40 + math.sin(self.intro_timer * 0.015 + y * 0.008) * 10)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        t = self.intro_timer

        if t < 120:
            # Scene 1: Title drop-in with glow
            drop = max(0, (80 - t) * 3)
            alpha = min(255, t * 4)
            
            # Glowing title
            for glow in range(3, 0, -1):
                font_big = pygame.font.Font(None, 72 + glow * 4)
                glow_surf = font_big.render("MINIMAL PLATFORMER 4", True, (0, 0, min(255, alpha // 2)))
                self.screen.blit(glow_surf, (SCREEN_WIDTH // 2 - glow_surf.get_width() // 2 + glow, 180 - drop + glow))
            
            font_big = pygame.font.Font(None, 72)
            text = font_big.render("MINIMAL PLATFORMER 4", True, (alpha // 2, alpha // 2, alpha))
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 180 - drop))
            
            if t > 30:
                a2 = min(255, (t - 30) * 5)
                font_sub = pygame.font.Font(None, 48)
                subtitle = font_sub.render("T H E   R E D   U P R I S I N G", True, (a2, a2 // 3, a2 // 3))
                self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 270))
            
            if t > 60:
                a3 = min(255, (t - 60) * 4)
                font_tiny = pygame.font.Font(None, 26)
                press = font_tiny.render("press SPACE to skip", True, (a3 // 3, a3 // 3, a3 // 3))
                self.screen.blit(press, (SCREEN_WIDTH // 2 - press.get_width() // 2, SCREEN_HEIGHT - 50))

        elif t < 240:
            # Scene 2: Animated story with characters
            local_t = t - 120
            font = pygame.font.Font(None, 34)
            story_lines = [
                ("Long ago, the world was full of color...", WHITE, 0),
                ("Blue Guy and his friends lived in peace.", (100, 180, 255), 20),
                ("", WHITE, 40),
                ("Then one day...", (200, 200, 200), 55),
                ("RED GUY appeared.", (255, 80, 80), 70),
                ("He STOLE every color from the world.", (220, 60, 60), 85),
                ("Leaving nothing but darkness.", (150, 150, 150), 100),
            ]
            for line, color, start_t in story_lines:
                if line and local_t > start_t:
                    a = min(255, (local_t - start_t) * 8)
                    idx = story_lines.index((line, color, start_t))
                    surf = font.render(line, True, color)
                    self.screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, 100 + idx * 52))
            
            # Animated Blue Guy (sad, walking left)
            if local_t > 50:
                bx = SCREEN_WIDTH // 4 - int(local_t * 0.5) % 200
                by = SCREEN_HEIGHT - 160
                pygame.draw.rect(self.screen, (60, 120, 220), (bx, by, 30, 30))
                pygame.draw.circle(self.screen, WHITE, (bx + 8, by + 10), 3)
                # Sad expression - mouth down
                pygame.draw.arc(self.screen, (80, 80, 80), (bx + 5, by + 18, 14, 8), 0, math.pi, 2)

            # Animated Red Guy (menacing, floating)
            if local_t > 70:
                rx = SCREEN_WIDTH * 3 // 4
                ry = SCREEN_HEIGHT - 200 + math.sin(local_t * 0.08) * 15
                # Shadow
                pygame.draw.ellipse(self.screen, (80, 20, 20), (rx - 5, SCREEN_HEIGHT - 160, 60, 12))
                pygame.draw.rect(self.screen, (200, 40, 40), (rx, ry, 40, 40))
                pygame.draw.circle(self.screen, YELLOW, (rx + 12, ry + 14), 4)
                pygame.draw.circle(self.screen, YELLOW, (rx + 28, ry + 14), 4)
                # Evil grin
                pygame.draw.arc(self.screen, YELLOW, (rx + 8, ry + 22, 20, 10), math.pi, 0, 2)

        else:
            # Scene 3: Epic call to action
            local_t = t - 240
            alpha = min(255, local_t * 6)

            font_big = pygame.font.Font(None, 64)
            text1 = font_big.render("Only BLUE GUY can save the world!", True, (alpha // 2, alpha // 2, alpha))
            self.screen.blit(text1, (SCREEN_WIDTH // 2 - text1.get_width() // 2, 200))

            if local_t > 30:
                a2 = min(255, (local_t - 30) * 6)
                font_med = pygame.font.Font(None, 40)
                text2 = font_med.render("Defeat Red Guy! Restore the colors!", True, (a2, a2 // 3, a2 // 3))
                self.screen.blit(text2, (SCREEN_WIDTH // 2 - text2.get_width() // 2, 280))

            # Heroic Blue Guy pose
            bounce = math.sin(local_t * 0.12) * 6
            bx, by = SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT - 180 + bounce
            # Cape effect
            pygame.draw.polygon(self.screen, (40, 80, 180),
                [(bx - 10, by + 5), (bx - 25, by + 35), (bx + 5, by + 30)])
            pygame.draw.rect(self.screen, (80, 160, 255), (bx, by, 30, 30))
            pygame.draw.circle(self.screen, WHITE, (bx + 20, by + 10), 4)
            pygame.draw.circle(self.screen, BLACK, (bx + 21, by + 11), 2)
            # Gun
            pygame.draw.rect(self.screen, GRAY, (bx + 28, by + 14, 12, 6))

            if local_t > 60:
                a3 = min(255, (local_t - 60) * 8)
                font_big2 = pygame.font.Font(None, 80)
                text3 = font_big2.render("YOUR ADVENTURE BEGINS!", True, (a3, a3, 0))
                self.screen.blit(text3, (SCREEN_WIDTH // 2 - text3.get_width() // 2, 380))

        # Falling star particles
        if t % 4 == 0:
            self.particles.append(Particle(
                random.randint(0, SCREEN_WIDTH), -10,
                random.uniform(-0.5, 0.5), random.uniform(1.5, 3.5),
                (100, 150, 255) if random.random() > 0.4 else (255, 80, 80), 80
            ))
        for particle in self.particles[:]:
            particle.update()
            particle.draw(self.screen)
            if particle.life <= 0:
                self.particles.remove(particle)
    
    def draw_cutscene(self):
        """Draw mid-game cutscenes - fully animated!"""
        t = self.cutscene_timer
        s = self.screen

        def gradient(top_col, bot_col):
            for y in range(SCREEN_HEIGHT):
                p = y / SCREEN_HEIGHT
                r = int(top_col[0] + (bot_col[0]-top_col[0])*p)
                g = int(top_col[1] + (bot_col[1]-top_col[1])*p)
                b = int(top_col[2] + (bot_col[2]-top_col[2])*p)
                pygame.draw.line(s,(r,g,b),(0,y),(SCREEN_WIDTH,y))

        def speech(text, x, y, col, bdr, w=420):
            f = pygame.font.Font(None, 32)
            surf = f.render(text, True, col)
            bx = x - surf.get_width()//2 - 14
            pygame.draw.rect(s, bdr, (bx-2,y-12,surf.get_width()+32,42), 0, 10)
            pygame.draw.rect(s, col,  (bx-2,y-12,surf.get_width()+32,42), 2, 10)
            s.blit(surf, (x - surf.get_width()//2, y))

        def draw_blue_guy(x, y, facing=1, hat=None, anim=0):
            # Shadow
            pygame.draw.ellipse(s, (20,20,40), (x-4, y+38, 48, 12))
            # Body
            col = getattr(self,'color_equipped', BLUE)
            pygame.draw.rect(s, col, (x, y, 40, 40), 0, 6)
            # Eye
            ex = x+28 if facing>0 else x+8
            pygame.draw.circle(s, WHITE, (ex,y+14), 6)
            pygame.draw.circle(s, BLACK,  (ex+(facing),y+15), 3)
            # Legs walk
            leg = int(anim)%2
            pygame.draw.rect(s,(30,80,160),(x+4,y+40,12,8+leg*4))
            pygame.draw.rect(s,(30,80,160),(x+22,y+40,12,8+(1-leg)*4))
            # Gun
            pygame.draw.rect(s,GRAY,(x+38 if facing>0 else x-10,y+18,14,8))
            if hat: self._draw_hat_at(hat, x+10, y-2)

        def draw_red_guy(x, y, size=50, anim=0):
            pygame.draw.ellipse(s,(40,10,10),(x-4,y+size+4,size+8,14))
            pygame.draw.rect(s,RED,(x,y,size,size),0,6)
            pygame.draw.circle(s,YELLOW,(x+12,y+16),5)
            pygame.draw.circle(s,YELLOW,(x+size-12,y+16),5)
            pygame.draw.arc(s,YELLOW,(x+10,y+28,size-20,12),math.pi,0,3)

        # ── CUTSCENE 4: Gas Station Break ─────────────────────────────────
        if self.cutscene_mode == 4:
            # Sky gradient day
            gradient((135,206,250),(255,230,180))
            # Ground
            pygame.draw.rect(s,(200,170,100),(0,560,SCREEN_WIDTH,210))
            pygame.draw.rect(s,(180,150,80),(0,560,SCREEN_WIDTH,8))
            # Sun with rays
            sc = (130,110); pygame.draw.circle(s,(255,220,80),sc,55)
            for i in range(12):
                a = i/12*math.pi*2 + t*0.01
                pygame.draw.line(s,(255,240,120),
                    (sc[0]+int(math.cos(a)*62),sc[1]+int(math.sin(a)*62)),
                    (sc[0]+int(math.cos(a)*80),sc[1]+int(math.sin(a)*80)),3)
            # Cactus
            for cx2,cy2 in [(180,480),(900,490)]:
                pygame.draw.rect(s,(60,140,60),(cx2,cy2,22,80))
                pygame.draw.rect(s,(60,140,60),(cx2-22,cy2+20,22,16))
                pygame.draw.rect(s,(60,140,60),(cx2+22,cy2+30,22,16))
            # Gas station building
            pygame.draw.rect(s,(200,195,185),(380,370,320,200))  # main
            pygame.draw.rect(s,(180,60,60),(370,330,340,48))     # roof sign
            pygame.draw.rect(s,(220,220,220),(440,420,80,100))   # door
            pygame.draw.rect(s,(100,180,255),(560,420,70,70))    # window
            # Window reflection
            pygame.draw.line(s,WHITE,(563,423),(575,435),3)
            pygame.draw.line(s,WHITE,(563,430),(571,438),2)
            fb = pygame.font.Font(None,38)
            rb = fb.render("GAS STOP",True,WHITE)
            s.blit(rb,(SCREEN_WIDTH//2-rb.get_width()//2,341))
            # Blue guy walking in
            walk = min(t*2, 280)
            bob = math.sin(t*0.2)*4
            draw_blue_guy(int(walk)+20, int(530+bob), 1,
                          getattr(self,'hat_equipped',None), t*0.3)
            # Water bottle animation
            if t > 40:
                bx2 = int(walk)+20+18; by2=510
                zoom = 1+math.sin(t*0.08)*0.15
                bh2 = int(50*zoom); bw2=int(18*zoom)
                pygame.draw.rect(s,CYAN,(bx2-bw2//2,by2-bh2,bw2,bh2),0,4)
                pygame.draw.rect(s,(180,240,255),(bx2-bw2//2+2,by2-bh2+2,bw2-4,bh2-4),2,4)
                # Bubbles
                for bi in range(3):
                    ba = (t*0.15+bi*0.8)%1
                    bub_y = int(by2 - bh2*ba)
                    pygame.draw.circle(s,(180,240,255),(bx2,bub_y),2)
            # Text panels
            a0 = min(255,t*5)
            if t>10:
                speech("Blue Guy takes a well-earned rest...",
                       SCREEN_WIDTH//2,90,(a0,a0,255),(20,20,60))
            if t>55:
                a2=min(255,(t-55)*6)
                speech("*gulp* *gulp* *gulp*",
                       SCREEN_WIDTH//2,150,CYAN,(20,40,60))
            if t>90:
                a3=min(255,(t-90)*6)
                speech("Mmmh...  good water.  More please!",
                       SCREEN_WIDTH//2,200,(a3,a3,255),(20,20,60))

        # ── CUTSCENE 8: After Level 6 — The Long Road ──────────────────────
        elif self.cutscene_mode == 8:
            # Evening sky — orange and purple sunset
            gradient((60,20,80),(220,120,40))
            # Ground — dusty road
            pygame.draw.rect(s,(160,130,90),(0,560,SCREEN_WIDTH,210))
            pygame.draw.rect(s,(140,110,70),(0,560,SCREEN_WIDTH,8))
            # Road stripes
            for i in range(8):
                pygame.draw.rect(s,(180,150,100),(i*160,570,100,6))
            # Distant mountains silhouette
            for i in range(12):
                mx2 = i*110; mh = 80+math.sin(i*0.9)*40
                pygame.draw.polygon(s,(50,30,60),[
                    (mx2,560),(mx2+55,int(560-mh)),(mx2+110,560)])
            # Animated clouds drifting right
            for i in range(4):
                cx2 = int((i*320 + t*0.8)%1300)
                cy2 = 80 + i*30
                for bx2,br in [(0,22),(30,28),(60,22),(-20,18)]:
                    pygame.draw.circle(s,(200,160,120),(cx2+bx2,cy2),br)
            # Blue Guy walking — tired, slower pace
            walk_x = min(t*1.4, 500)
            bob = math.sin(t*0.12)*3
            draw_blue_guy(int(walk_x)+40, int(500+bob), 1,
                          getattr(self,'hat_equipped',None), t*0.2)
            # Sweat drop above Blue Guy when tired (after a while)
            if t > 60:
                sx2 = int(walk_x)+40+38; sy2 = int(490+bob)
                pygame.draw.circle(s,CYAN,(sx2,sy2),5)
                pygame.draw.polygon(s,CYAN,[(sx2-3,sy2),(sx2+3,sy2),(sx2,sy2-10)])
            # Signpost in middle of scene
            if t > 30:
                pygame.draw.rect(s,(120,80,40),(550,430,8,130))
                pygame.draw.rect(s,(160,110,60),(480,420,140,44),0,6)
                pygame.draw.rect(s,(100,70,30),(480,420,140,44),2,6)
                fn2=pygame.font.Font(None,26)
                s.blit(fn2.render("LONG ROAD",True,(40,20,10)),(492,430))
                s.blit(fn2.render("→ 24 more lvls",True,(80,40,20)),(486,448))
            # Tumbleweeds rolling across
            for i in range(2):
                tx2 = int((i*600 + t*1.8)%1300)
                pygame.draw.circle(s,(140,100,50),(tx2,548),14,2)
                pygame.draw.line(s,(120,80,40),(tx2-10,548),(tx2+10,548),2)
                pygame.draw.line(s,(120,80,40),(tx2,538),(tx2,558),2)
                pygame.draw.line(s,(120,80,40),(tx2-7,541),(tx2+7,555),2)
            # Birds flying across the evening sky
            for i in range(3):
                brd_x = int((i*400 + t*2.2)%1400) - 50
                brd_y = 120 + i*28
                pygame.draw.line(s,(60,40,70),(brd_x,brd_y),(brd_x+10,brd_y-4),2)
                pygame.draw.line(s,(60,40,70),(brd_x+10,brd_y-4),(brd_x+20,brd_y),2)
            # Footprint trail behind Blue Guy
            for i in range(4):
                fp_x = int(walk_x)+20 - i*22
                if fp_x > 0:
                    pygame.draw.ellipse(s,(140,110,70),(fp_x,553,8,4))
            # Speech bubbles
            if t > 20:
                a0=min(255,(t-20)*7)
                speech("That was one loooong road...",
                       SCREEN_WIDTH//2-80,110,(a0,a0,255),(20,20,60))
            if t > 65:
                a1=min(255,(t-65)*7)
                speech("Red Guy can't be far now.",
                       SCREEN_WIDTH//2+40,170,(a1,a1//2,a1//2),(60,20,20))
            if t > 110:
                a2=min(255,(t-110)*8)
                speech("...I should have brought more water.",
                       SCREEN_WIDTH//2-60,230,CYAN,(20,40,60))
            # Stars beginning to appear as evening sets in
            if t > 80:
                star_alpha = min(255,(t-80)*4)
                for i in range(8):
                    stx = (i*173+97)%SCREEN_WIDTH
                    sty = 30 + (i*61)%100
                    star_surf = pygame.Surface((4,4),pygame.SRCALPHA)
                    pygame.draw.circle(star_surf,(*WHITE,star_alpha),(2,2),2)
                    s.blit(star_surf,(stx,sty))
            # Red Guy silhouette watching from far distance ominously
            if t > 90:
                rga = min(180,(t-90)*5)
                rg_surf = pygame.Surface((30,30),pygame.SRCALPHA)
                pygame.draw.rect(rg_surf,(200,20,20,rga),(0,0,30,30),0,4)
                pygame.draw.circle(rg_surf,(255,200,20,rga),(22,10),4)
                pygame.draw.circle(rg_surf,(255,200,20,rga),(8,10),4)
                s.blit(rg_surf,(SCREEN_WIDTH-80,490))
                if t > 110:
                    fa=min(255,(t-110)*6)
                    fev=pygame.font.Font(None,20)
                    ws=fev.render("???",True,(220,40,40))
                    ws.set_alpha(fa)
                    s.blit(ws,(SCREEN_WIDTH-72,478))
            # SPACE to skip hint
            if t > 100:
                fsk=pygame.font.Font(None,24)
                sk=fsk.render("SPACE to skip",True,(120,120,120))
                s.blit(sk,(SCREEN_WIDTH//2-sk.get_width()//2,SCREEN_HEIGHT-30))

        # ── CUTSCENE 9: After Level 8 — Desert Gas Station ─────────────────
        elif self.cutscene_mode == 9:
            # Hot desert sky — blazing white-yellow at top, deep orange low
            gradient((255,220,100),(220,100,30))
            # Desert sand ground
            pygame.draw.rect(s,(210,170,80),(0,545,SCREEN_WIDTH,230))
            pygame.draw.rect(s,(230,185,90),(0,545,SCREEN_WIDTH,8))
            # Sand dunes in background
            for i in range(5):
                dx = i*260; dh = 60+math.sin(i*1.1)*25
                pygame.draw.ellipse(s,(220,175,75),(dx,int(520-dh),280,int(dh*2)))
            # Blazing sun — huge and harsh
            pygame.draw.circle(s,(255,240,80),(SCREEN_WIDTH-90,70),60)
            for i in range(14):
                a = i/14*math.pi*2 + t*0.008
                pygame.draw.line(s,(255,250,120),
                    (SCREEN_WIDTH-90+int(math.cos(a)*68),70+int(math.sin(a)*68)),
                    (SCREEN_WIDTH-90+int(math.cos(a)*88),70+int(math.sin(a)*88)),3)
            # Heat shimmer lines near ground
            for i in range(6):
                sx2 = 80+i*180; shimmy = math.sin(t*0.3+i)*3
                pygame.draw.line(s,(230,190,100),(sx2,535),(sx2+60+int(shimmy),537),1)
            # Gas station building
            pygame.draw.rect(s,(215,200,175),(330,360,340,200))
            pygame.draw.rect(s,(180,60,40),(318,318,364,50))   # roof sign
            pygame.draw.rect(s,(200,195,185),(318,318,364,50),3)
            pygame.draw.rect(s,(200,190,160),(360,420,90,140)) # door
            pygame.draw.rect(s,(130,190,230),(510,410,80,75),0,4)  # window
            pygame.draw.line(s,WHITE,(514,414),(526,428),3)
            pygame.draw.line(s,WHITE,(514,422),(522,430),2)
            fb=pygame.font.Font(None,34)
            rb=fb.render("GAS  STOP",True,WHITE)
            s.blit(rb,(SCREEN_WIDTH//2-rb.get_width()//2,330))
            # Fuel pump
            pygame.draw.rect(s,(160,60,40),(640,420,30,100),0,4)
            pygame.draw.rect(s,(200,80,50),(632,412,46,20),0,4)
            pygame.draw.rect(s,(120,40,20),(660,450,16,6))
            # Cactus left side
            pygame.draw.rect(s,(60,140,50),(120,440,20,110))
            pygame.draw.rect(s,(60,140,50),(80,462,40,14))
            pygame.draw.rect(s,(60,140,50),(140,460,40,14))

            # ── PHASE: Blue Guy walks to door (t 0-60) ─────────────────────
            if t < 60:
                walk_to = min(t*5.5, 340)
                bob = math.sin(t*0.18)*3
                draw_blue_guy(int(walk_to)+30,int(490+bob),1,
                              getattr(self,'hat_equipped',None),t*0.25)
                if t > 15:
                    a0=min(255,(t-15)*7)
                    speech("A gas station!  Thank goodness...",
                           500,120,(a0,a0,255),(20,20,60))

            # ── PHASE: inside (t 60-110) — door closed, light flickers ─────
            elif t < 110:
                # Blue Guy gone inside — door is closed
                pygame.draw.rect(s,(180,168,148),(360,420,90,140))
                pygame.draw.rect(s,(140,120,100),(360,420,90,140),3)
                # Window light flicker
                flicker = 180+int(math.sin(t*0.8)*30)
                pygame.draw.rect(s,(flicker,flicker-20,80),(510,410,80,75),0,4)
                if t > 70:
                    a1=min(255,(t-70)*8)
                    speech("*browsing the fridge*",
                           500,130,CYAN,(20,40,60))
                if t > 90:
                    a2=min(255,(t-90)*9)
                    speech("Oh WOW they have the big ones!",
                           490,185,(a2,a2,255),(20,20,60))

            # ── PHASE: Blue Guy walks back out with bottle (t 110-180) ──────
            else:
                walk_out = min((t-110)*4.5, 280)
                bob2 = math.sin((t-110)*0.15)*3
                draw_blue_guy(int(350+walk_out),int(490+bob2),1,
                              getattr(self,'hat_equipped',None),(t-110)*0.22)
                # Water bottle in hand — big one!
                bx2=int(350+walk_out)+40; by2=int(480+bob2)
                pygame.draw.rect(s,CYAN,(bx2,by2,14,38),0,5)
                pygame.draw.rect(s,(180,240,255),(bx2+2,by2+2,10,34),2,5)
                pygame.draw.rect(s,WHITE,(bx2+2,by2+4,10,6))  # label
                # Bubbles rising
                for bi in range(3):
                    ba=(t*0.12+bi*0.7)%1
                    pygame.draw.circle(s,(180,240,255),(bx2+7,int(by2+34-ba*32)),2)
                # Drinking animation (t 140 onwards)
                if t > 140:
                    a3=min(255,(t-140)*9)
                    speech("*glug* *glug* *glug*",
                           600,130,CYAN,(20,40,60))
                    # Tilt bottle up
                    tilt_t = min(1.0,(t-140)/20.0)
                    tilt_y = int(by2 - tilt_t*18)
                    pygame.draw.rect(s,(100,200,240),(bx2+2,tilt_y,14,10),0,4)
                if t > 165:
                    a4=min(255,(t-165)*10)
                    speech("Ahhhh.  Now lets keep moving!",
                           580,185,(a4,a4,255),(20,20,60))
                    # Blue Guy walks forward purposefully
                if t > 178:
                    speech("Red Guy... here I come.",
                           560,240,(255,180,180),(60,20,20))

            # SPACE to skip
            if t > 80:
                fsk=pygame.font.Font(None,24)
                sk=fsk.render("SPACE to skip",True,(120,120,120))
                s.blit(sk,(SCREEN_WIDTH//2-sk.get_width()//2,SCREEN_HEIGHT-30))

        # ── CUTSCENE 5: The Confrontation ─────────────────────────────────
        elif self.cutscene_mode == 5:
            gradient((15,10,30),(40,20,60))
            # Cracked ground
            pygame.draw.rect(s,(40,35,50),(0,560,SCREEN_WIDTH,210))
            for i in range(8):
                cx2=100+i*130; cy2=560
                pygame.draw.line(s,(25,20,35),(cx2,cy2),(cx2+40,cy2+30),2)
                pygame.draw.line(s,(25,20,35),(cx2,cy2),(cx2-20,cy2+45),2)
            # Lightning bolt atmosphere
            if t%40 < 4:
                lx = random.randint(200,800)
                pts=[(lx,0),(lx+20,180),(lx-10,180),(lx+15,380)]
                pygame.draw.lines(s,(255,255,180),False,pts,3)
            # Blue guy left - approaches from far
            bx2 = min(200, t*3)
            draw_blue_guy(int(bx2), 490, 1, getattr(self,'hat_equipped',None))
            # Red guy right - floats ominously
            float_y = 470 + math.sin(t*0.07)*12
            draw_red_guy(int(680+math.sin(t*0.04)*8), int(float_y), 60)
            # Red aura
            for r in range(40,5,-6):
                as2=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
                pygame.draw.circle(as2,(220,40,40,20),(r,r),r)
                s.blit(as2,(710-r,float_y+30-r))
            # Dialogue
            if t>25:
                a=min(255,(t-25)*6)
                speech("I've fought my way through 9 levels for THIS?",
                       300,320,(a,a,255),(20,20,60))
            if t>70:
                a2=min(255,(t-70)*6)
                speech("Red Guy:  Impressive.  But it ends here.",
                       700,380,(255,a2//3,a2//3),(60,10,10))
            if t>115:
                a3=min(255,(t-115)*8)
                fb2=pygame.font.Font(None,72)
                fs2=fb2.render("FIGHT!",True,(255,a3,0))
                s.blit(fs2,(SCREEN_WIDTH//2-fs2.get_width()//2,200))
                # Shockwave
                r2=int((t-115)*8)
                if r2<300:
                    pygame.draw.circle(s,(255,200,0),(SCREEN_WIDTH//2,560),r2,3)

        # ── CUTSCENE 6: Enter the Woods ────────────────────────────────────
        elif self.cutscene_mode == 6:
            gradient((20,35,15),(50,80,30))
            # Ground
            pygame.draw.rect(s,(30,60,20),(0,570,SCREEN_WIDTH,230))
            # Animated trees - lots of them
            for i in range(10):
                tx = (i*130 - int(t*0.3))%1300 - 50
                ty = 350+math.sin(i*1.3)*30
                # Trunk
                pygame.draw.rect(s,(60,35,15),(int(tx)+45,int(ty)+60,18,220))
                # Foliage layers
                for layer in range(4):
                    lw=90-layer*15; lh=55+layer*8
                    pts=[(int(tx)+54,int(ty)+layer*28),
                         (int(tx)+54-lw//2,int(ty)+lh+layer*28),
                         (int(tx)+54+lw//2,int(ty)+lh+layer*28)]
                    pygame.draw.polygon(s,(25+layer*8,65+layer*10,18),pts)
                # Sway
                sway=math.sin(t*0.04+i)*3
                pygame.draw.line(s,(30,80,20),(int(tx)+54,int(ty)),(int(tx)+54+sway,int(ty)-20),3)
            # Fireflies
            for i in range(12):
                fx=(i*173+t*0.8)%SCREEN_WIDTH
                fy=400+math.sin(i*0.7+t*0.03)*80
                bright=int(abs(math.sin(t*0.08+i))*200+55)
                pygame.draw.circle(s,(bright,bright,80),(int(fx),int(fy)),3)
            # Blue guy walks in
            walk=min(t*1.8,380)
            bob=math.sin(t*0.15)*5
            draw_blue_guy(int(walk)+30,int(530+bob),1,
                         getattr(self,'hat_equipped',None),t*0.25)
            # Fog wisps
            for i in range(5):
                wx=(i*220+t*0.5)%SCREEN_WIDTH
                ws=pygame.Surface((120,30),pygame.SRCALPHA)
                pygame.draw.ellipse(ws,(200,220,200,35),ws.get_rect())
                s.blit(ws,(int(wx),560+i*8))
            # Dialogue
            a=min(255,t*5)
            if t>15:
                speech("Entering the WOODS...",SCREEN_WIDTH//2,80,(a//2,a,a//2),(15,35,15))
            if t>55:
                a2=min(255,(t-55)*6)
                speech("Blue Guy:  It sure is humid here...",SCREEN_WIDTH//2,140,CYAN,(20,40,40))
            if t>90:
                a3=min(255,(t-90)*6)
                speech("...and GREEN GUYS are everywhere!",SCREEN_WIDTH//2,200,(a3//2,255,a3//2),(15,40,15))
            if t>125:
                a4=min(255,(t-125)*6)
                speech("I can feel eyes watching me...",SCREEN_WIDTH//2,255,(a4,a4,a4//2),(30,30,20))
                # Eyes in the dark
                for i in range(4):
                    ex2=150+i*220; ey2=460+i%2*40
                    glow=pygame.Surface((20,10),pygame.SRCALPHA)
                    pygame.draw.ellipse(glow,(100,255,100,160),glow.get_rect())
                    s.blit(glow,(ex2,ey2))

        # ── CUTSCENE 7: Final Showdown ──────────────────────────────────────
        elif self.cutscene_mode == 7:
            gradient((8,5,5),(25,10,10))
            # Lava cracks on floor
            pygame.draw.rect(s,(30,15,15),(0,570,SCREEN_WIDTH,230))
            for i in range(6):
                cx2=80+i*170; lava_pulse=int(abs(math.sin(t*0.05+i))*40)
                pygame.draw.line(s,(200+lava_pulse,40,0),(cx2,570),(cx2+60,620),3)
                pygame.draw.line(s,(200+lava_pulse,40,0),(cx2+60,620),(cx2+30,650),2)
            # Floating fortress bg
            for i in range(5):
                fx2=100+i*200; fy2=200+math.sin(t*0.02+i)*15
                pygame.draw.rect(s,(50,20,20),(int(fx2),int(fy2),80,120))
                pygame.draw.rect(s,(60,25,25),(int(fx2)+10,int(fy2)-20,20,25))
                pygame.draw.rect(s,(60,25,25),(int(fx2)+50,int(fy2)-20,20,25))
            # Red Guy - BIG, centre, with wings
            ry=360+math.sin(t*0.06)*18
            rx=SCREEN_WIDTH//2-35
            # Wings
            for side in [-1,1]:
                wa=math.sin(t*0.1)*0.4
                wpts=[(rx+35,ry+30),
                      (rx+35+side*80,ry+10+int(math.sin(wa)*20)),
                      (rx+35+side*60,ry+60+int(math.sin(wa)*15))]
                pygame.draw.polygon(s,(120,20,20),wpts)
            draw_red_guy(rx,int(ry),70)
            # Orbiting spiked balls
            for i in range(5):
                oa=t*0.06+i/5*math.pi*2
                ox=rx+35+int(math.cos(oa)*110); oy=int(ry)+35+int(math.sin(oa)*50)
                pygame.draw.circle(s,GRAY,(ox,oy),10)
                for si in range(6):
                    sa=si/6*math.pi*2
                    pygame.draw.line(s,GRAY,(ox,oy),(ox+int(math.cos(sa)*14),oy+int(math.sin(sa)*14)),2)
            # Green minions march in
            for i in range(6):
                mx2=SCREEN_WIDTH+60-min(t*3,SCREEN_WIDTH-150)+i*90
                mb=math.sin(t*0.15+i)*5
                pygame.draw.rect(s,GREEN,(int(mx2),int(530+mb),28,28),0,4)
                pygame.draw.circle(s,BLACK,(int(mx2)+8,int(537+mb)),3)
                pygame.draw.circle(s,BLACK,(int(mx2)+20,int(537+mb)),3)
            # Blue Guy tiny on left
            draw_blue_guy(80,505,1,getattr(self,'hat_equipped',None))
            # Text
            if t>10:
                a=min(255,(t-10)*5)
                fb3=pygame.font.Font(None,76)
                fts=fb3.render("FINAL BATTLE",True,(255,a//4,0))
                s.blit(fts,(SCREEN_WIDTH//2-fts.get_width()//2,80))
            if t>50:
                a2=min(255,(t-50)*6)
                speech("Red Guy:  You've come all this way...",SCREEN_WIDTH//2,185,(255,a2//3,a2//3),(60,10,10))
            if t>90:
                a3=min(255,(t-90)*6)
                speech("Red Guy:  ...only to LOSE!",SCREEN_WIDTH//2,240,(255,a3//3,a3//3),(60,10,10))
            if t>130:
                a4=min(255,(t-130)*8)
                speech("Blue Guy:  I don't think so!",280,310,(a4,a4,255),(20,20,60))
            if t>160:
                a5=min(255,(t-160)*10)
                fb4=pygame.font.Font(None,52)
                fts2=fb4.render("USE YOUR GUN!  CTRL = SHOOT",True,(a5,a5,0))
                s.blit(fts2,(SCREEN_WIDTH//2-fts2.get_width()//2,370))

        # Skip prompt
        if t > 100:
            pulse = int(abs(math.sin(t*0.06))*110+100)
            fp=pygame.font.Font(None,26)
            ps=fp.render("SPACE to skip",True,(pulse,pulse,pulse))
            s.blit(ps,(SCREEN_WIDTH//2-ps.get_width()//2,SCREEN_HEIGHT-45))
    
    def _draw_hat_at(self, hat_key, px, py):
        """Draw equipped hat above player."""
        s = self.screen
        if hat_key == 'party':
            pts = [(px+10, py-18), (px+2, py+2), (px+18, py+2)]
            pygame.draw.polygon(s, (255, 80, 200), pts)
            pygame.draw.circle(s, YELLOW, (px+10, py-18), 3)
            for i,cx in enumerate([px+4, px+10, px+16]):
                pygame.draw.circle(s, [RED,YELLOW,CYAN][i], (cx, py+2), 3)
        elif hat_key == 'crown':
            pts = [(px+2,py),(px+2,py-10),(px+6,py-6),(px+10,py-14),(px+14,py-6),(px+18,py-10),(px+18,py)]
            pygame.draw.polygon(s, YELLOW, pts)
            pygame.draw.polygon(s, (180,140,0), pts, 2)
            for gx in [px+4, px+10, px+16]:
                pygame.draw.circle(s, RED, (gx, py-4), 2)
        elif hat_key == 'wizard':
            pts = [(px+10,py-22),(px+2,py),(px+18,py)]
            pygame.draw.polygon(s, PURPLE, pts)
            pygame.draw.ellipse(s, (120,40,160), (px,py-2,20,8))
            pygame.draw.circle(s, YELLOW, (px+10, py-22), 3)
        elif hat_key == 'cowboy':
            pygame.draw.ellipse(s, BROWN, (px+2,py-8,16,10))
            pygame.draw.ellipse(s, BROWN, (px-2,py-2,24,7))
            pygame.draw.line(s, (80,40,10), (px+2,py-3),(px+18,py-3), 2)
        elif hat_key == 'halo':
            pygame.draw.ellipse(s, YELLOW, (px+2,py-16,16,6), 2)
            glow_s = pygame.Surface((20,10), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_s, (255,240,0,60), (0,0,20,10))
            s.blit(glow_s, (px+1, py-18))

    def draw_world_map(self):
        """Full-screen interactive world map."""
        s = self.screen
        s.fill((15, 20, 35))
        t = pygame.time.get_ticks() * 0.001

        # Title
        f = pygame.font.Font(None, 54)
        ts = f.render("WORLD MAP", True, WHITE)
        s.blit(ts, (SCREEN_WIDTH//2 - ts.get_width()//2, 18))

        # Two worlds side by side
        worlds = [
            {'name':'Normal World','col':(60,80,160),'levels':range(0,15),'x':60,'y':80},
            {'name':'Woods World', 'col':(40,100,40),'levels':range(15,30),'x':540,'y':80},
        ]
        fn = pygame.font.Font(None, 26)
        fb = pygame.font.Font(None, 20)

        for w in worlds:
            # World panel
            pygame.draw.rect(s, (w['col'][0]//3, w['col'][1]//3, w['col'][2]//3),
                             (w['x'], w['y'], 440, 620), 0, 12)
            pygame.draw.rect(s, w['col'], (w['x'], w['y'], 440, 620), 3, 12)
            ws = fn.render(w['name'], True, WHITE)
            s.blit(ws, (w['x'] + 220 - ws.get_width()//2, w['y'] + 10))

            # Level nodes 5 per row
            for j, lv in enumerate(w['levels']):
                col = j % 5; row = j // 5
                nx = w['x'] + 50 + col * 80
                ny = w['y'] + 50 + row * 115
                beaten = lv in self.levels_beaten
                has_sticker = lv in self.stickers_found

                # Node circle
                node_col = GREEN if beaten else (w['col'][0], w['col'][1]+40, w['col'][2])
                pulse = abs(math.sin(t * 3 + lv * 0.4)) * 6 if not beaten else 0
                pygame.draw.circle(s, node_col, (nx, ny), int(24 + pulse))
                pygame.draw.circle(s, WHITE, (nx, ny), int(24 + pulse), 2)

                # Level number
                ln = fb.render(str(lv + 1), True, WHITE)
                s.blit(ln, (nx - ln.get_width()//2, ny - ln.get_height()//2))

                # Sticker badge
                if has_sticker:
                    emoji_idx = lv % len(self.sticker_names)
                    try:
                        ef = pygame.font.SysFont('segoe ui emoji', 16)
                        es = ef.render(self.sticker_names[emoji_idx], True, YELLOW)
                        s.blit(es, (nx + 16, ny - 30))
                    except Exception:
                        pygame.draw.circle(s, YELLOW, (nx+20, ny-20), 5)

                # Boss marker
                if lv in (9, 14, 29):
                    bf = fb.render("👑BOSS", True, RED)
                    try:
                        ef2 = pygame.font.SysFont('segoe ui emoji', 14)
                        bf = ef2.render("👑BOSS", True, RED)
                    except Exception:
                        pass
                    s.blit(bf, (nx - bf.get_width()//2, ny + 26))

        # Stats bar at bottom
        stats_y = SCREEN_HEIGHT - 70
        pygame.draw.rect(s, (20,25,45), (0, stats_y, SCREEN_WIDTH, 70))
        pygame.draw.line(s, (60,80,130), (0, stats_y), (SCREEN_WIDTH, stats_y), 2)
        fc = pygame.font.Font(None, 30)
        beaten_pct = int(len(self.levels_beaten) / 30 * 100)
        sticker_pct = len(self.stickers_found)
        stats = [
            f"Levels beaten: {len(self.levels_beaten)}/30  ({beaten_pct}%)",
            f"Stickers: {sticker_pct}/30",
            f"Total coins: {self.bank_coins}",
        ]
        for i, st in enumerate(stats):
            ss = fc.render(st, True, (180,200,220))
            s.blit(ss, (30 + i*340, stats_y + 20))

        # Close hint
        ch = pygame.font.Font(None, 26).render("Press M or ESC to close", True, (100,100,130))
        s.blit(ch, (SCREEN_WIDTH//2 - ch.get_width()//2, stats_y + 44))

    def draw_shop(self):
        """Shop overlay."""
        s = self.screen
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        s.blit(overlay, (0, 0))

        panel_x, panel_y, panel_w, panel_h = 100, 60, 824, 648
        pygame.draw.rect(s, (20, 25, 50), (panel_x, panel_y, panel_w, panel_h), 0, 16)
        pygame.draw.rect(s, (80, 100, 200), (panel_x, panel_y, panel_w, panel_h), 3, 16)

        ft = pygame.font.Font(None, 52)
        ts = ft.render("SHOP", True, YELLOW)
        s.blit(ts, (panel_x + panel_w//2 - ts.get_width()//2, panel_y + 14))

        # Coin balance
        fc = pygame.font.Font(None, 32)
        bal = fc.render(f"💰 {self.shop_coins} coins", True, YELLOW)
        s.blit(bal, (panel_x + panel_w - bal.get_width() - 20, panel_y + 18))

        # Tabs
        tabs = ["Clicker Upgrades", "Hats", "Colors"]
        for i, tab in enumerate(tabs):
            tx = panel_x + 20 + i * 275
            ty = panel_y + 62
            bg = (60,80,180) if i == self.shop_tab else (30,35,65)
            pygame.draw.rect(s, bg, (tx, ty, 260, 38), 0, 8)
            pygame.draw.rect(s, (80,100,200), (tx, ty, 260, 38), 2, 8)
            ts2 = fc.render(tab, True, WHITE)
            s.blit(ts2, (tx + 130 - ts2.get_width()//2, ty + 8))

        content_y = panel_y + 115
        fn = pygame.font.Font(None, 28)
        fs = pygame.font.Font(None, 22)

        if self.shop_tab == 0:
            # Clicker upgrades
            upgrades = [
                ('Auto Clicker',      'auto',  20,  'Earns 1 coin/sec automatically'),
                ('Better Eyes',       'eyes',  15,  'Blue Guy looks cooler'),
                ('Cape',              'cape',  25,  '+1 auto coin/sec'),
                ('Rocket Shoes',      'shoes', 40,  '+2 auto coins/sec'),
                ('Mega Multiplier',   'hat',   60,  'x2 coins per click'),
            ]
            for i, (name, key, cost, desc) in enumerate(upgrades):
                uy = content_y + i * 92
                owned = self.clicker_upgrades.get(key, 0)
                can_buy = self.shop_coins >= cost
                bg_col = (30, 50, 30) if can_buy else (40, 30, 30)
                pygame.draw.rect(s, bg_col, (panel_x+20, uy, panel_w-40, 84), 0, 8)
                pygame.draw.rect(s, (70,100,70) if can_buy else (80,50,50),
                                 (panel_x+20, uy, panel_w-40, 84), 2, 8)
                ns = fn.render(f"{name}  (owned: {owned})", True, WHITE)
                s.blit(ns, (panel_x + 36, uy + 12))
                ds = fs.render(desc, True, (160,180,160))
                s.blit(ds, (panel_x + 36, uy + 38))
                cost_s = fn.render(f"Buy: {cost} coins  [press {i+1}]", True, YELLOW if can_buy else GRAY)
                s.blit(cost_s, (panel_x + 36, uy + 58))

        elif self.shop_tab == 1:
            # Hats
            for i, hat in enumerate(self.HATS):
                col_i = i % 3; row_i = i // 3
                hx = panel_x + 30 + col_i * 270
                hy = content_y + row_i * 160
                owned = hat['key'] in self.hats_owned
                equipped = self.hat_equipped == hat['key']
                bg = (30,50,30) if owned else (35,30,50)
                pygame.draw.rect(s, bg, (hx, hy, 250, 145), 0, 10)
                bdr = GREEN if equipped else ((100,100,200) if owned else (60,60,90))
                pygame.draw.rect(s, bdr, (hx, hy, 250, 145), 2, 10)
                # Preview hat
                self._draw_hat_at(hat['key'], hx + 115, hy + 45)
                # Blue Guy preview
                pygame.draw.rect(s, getattr(self,'color_equipped', BLUE), (hx+105, hy+50, 22, 22))
                hn = fn.render(hat['name'], True, WHITE)
                s.blit(hn, (hx + 125 - hn.get_width()//2, hy + 82))
                if owned:
                    btn = "EQUIPPED" if equipped else f"Equip [press {i+1}]"
                    bs = fs.render(btn, True, GREEN if equipped else CYAN)
                else:
                    bs = fs.render(f"Buy: {hat['cost']} coins  [press {i+1}]",
                                   True, YELLOW if self.shop_coins >= hat['cost'] else GRAY)
                s.blit(bs, (hx + 125 - bs.get_width()//2, hy + 110))

        elif self.shop_tab == 2:
            # Colors
            for i, skin in enumerate(self.COLORS):
                col_i = i % 4; row_i = i // 4
                cx2 = panel_x + 30 + col_i * 200
                cy2 = content_y + row_i * 160
                owned = skin['col'] in self.colors_owned
                equipped = self.color_equipped == skin['col']
                bg = (30,50,30) if owned else (35,30,50)
                pygame.draw.rect(s, bg, (cx2, cy2, 185, 145), 0, 10)
                bdr = GREEN if equipped else ((100,200,100) if owned else (60,60,90))
                pygame.draw.rect(s, bdr, (cx2, cy2, 185, 145), 2, 10)
                pygame.draw.rect(s, skin['col'], (cx2+75, cy2+20, 35, 35))
                pygame.draw.circle(s, WHITE, (cx2+89, cy2+29), 4)
                sn = fs.render(skin['name'], True, WHITE)
                s.blit(sn, (cx2+92 - sn.get_width()//2, cy2+70))
                if owned:
                    btn = "EQUIPPED" if equipped else f"Equip [{i+1}]"
                    bs = fs.render(btn, True, GREEN if equipped else CYAN)
                else:
                    bs = fs.render(f"{skin['cost']}c [{i+1}]",
                                   True, YELLOW if self.shop_coins >= skin['cost'] else GRAY)
                s.blit(bs, (cx2+92 - bs.get_width()//2, cy2+100))

        # Nav hints
        nh = fs.render("TAB=Switch tab   ESC/S=Close", True, (100,100,130))
        s.blit(nh, (panel_x + panel_w//2 - nh.get_width()//2, panel_y + panel_h - 28))

    def draw_clicker(self):
        """Right-side clickable Big Blue Guy panel."""
        s = self.screen
        t = pygame.time.get_ticks() * 0.001
        cx, cy, cw, ch = SCREEN_WIDTH - 220, 150, 210, 460
        pygame.draw.rect(s, (15, 18, 40), (cx, cy, cw, ch), 0, 14)
        pygame.draw.rect(s, (50, 70, 160), (cx, cy, cw, ch), 2, 14)

        fn = pygame.font.Font(None, 24)
        fs = pygame.font.Font(None, 20)

        # Title
        ts = fn.render("👆 CLICK ME!", True, CYAN)
        s.blit(ts, (cx + cw//2 - ts.get_width()//2, cy + 10))

        # Big animated Blue Guy - store rect on self RIGHT AWAY so clicks work
        anim = self.clicker_anim
        squish_y = int(math.sin(anim * 8) * 6) if anim > 0 else 0
        squish_x = int(math.cos(anim * 8) * 4) if anim > 0 else 0
        bw = 60 + squish_x; bh = 60 - squish_y
        bx = cx + cw//2 - bw//2; by = cy + 50
        # Store the big guy rect so mouse clicks work on first frame too!
        self._big_guy_rect = pygame.Rect(bx, by, bw, bh)
        # Shadow
        pygame.draw.ellipse(s, (10,12,30), (bx+5, by+bh+4, bw-8, 10))
        # Body
        col = getattr(self, 'color_equipped', BLUE)
        pygame.draw.rect(s, col, (bx, by, bw, bh), 0, 8)
        # Hat
        hat = getattr(self, 'hat_equipped', None)
        if hat:
            self._draw_hat_at(hat, bx + bw//2 - 10, by - 2)
        # Eyes
        eye_offset = int(math.sin(t * 2) * 2)
        pygame.draw.circle(s, WHITE, (bx+18, by+20+eye_offset), 6)
        pygame.draw.circle(s, WHITE, (bx+42, by+20+eye_offset), 6)
        pygame.draw.circle(s, BLACK,  (bx+20, by+21+eye_offset), 3)
        pygame.draw.circle(s, BLACK,  (bx+44, by+21+eye_offset), 3)
        # Mouth smile
        pygame.draw.arc(s, (200,150,150), (bx+18, by+36, 24, 12), math.pi, 0, 3)
        # Arms wave
        arm_angle = math.sin(t * 3) * 0.4
        for side, sx2 in [(-1, bx-12), (1, bx+bw)]:
            arm_x = sx2 + int(side * math.cos(arm_angle + side) * 8)
            arm_y = by + 20 + int(math.sin(arm_angle + side) * 10)
            pygame.draw.line(s, col, (sx2 if side>0 else sx2+12, by+25), (arm_x+6, arm_y), 8)

        # Clicker anim decay
        if anim > 0:
            self.clicker_anim = max(0, anim - 0.15)

        # Stats
        sy = cy + 135
        lines = [
            (f"Clicks: {self.clicker_clicks}", WHITE),
            (f"Coins: {self.shop_coins}", YELLOW),
            (f"Per sec: {self.clicker_cps}", CYAN),
        ]
        for i, (txt, col2) in enumerate(lines):
            ts2 = fs.render(txt, True, col2)
            s.blit(ts2, (cx + cw//2 - ts2.get_width()//2, sy + i * 22))

        # Buttons
        shop_btn = pygame.Rect(cx+10, cy+240, cw-20, 34)
        map_btn  = pygame.Rect(cx+10, cy+278, cw-20, 34)
        stk_btn  = pygame.Rect(cx+10, cy+316, cw-20, 34)
        house_btn= pygame.Rect(cx+10, cy+354, cw-20, 34)
        race_btn = pygame.Rect(cx+10, cy+392, cw-20, 34)

        self._shop_btn_rect  = shop_btn
        self._map_btn_rect   = map_btn
        self._stk_btn_rect   = stk_btn
        self._house_btn_rect = house_btn
        self._race_btn_rect  = race_btn

        mx2, my2 = pygame.mouse.get_pos()
        for btn, lbl, col3 in [
            (shop_btn,  "SHOP  [S]",          (60,80,200)),
            (map_btn,   "WORLD MAP  [M]",      (40,100,60)),
            (stk_btn,   f"STICKERS  {len(self.stickers_found)}/30", (100,40,160)),
            (house_btn, "🏠 BLUE GUY'S HOUSE", (80,60,40)),
            (race_btn,  "🏁 RACE THE CPU",     (120,60,20)),
        ]:
            hover = btn.collidepoint(mx2, my2)
            bg = tuple(min(255, c + 40) for c in col3) if hover else col3
            pygame.draw.rect(s, bg, btn, 0, 8)
            pygame.draw.rect(s, WHITE, btn, 1, 8)
            ls = fs.render(lbl, True, WHITE)
            s.blit(ls, (btn.centerx - ls.get_width()//2, btn.centery - ls.get_height()//2))

        # Click hint
        ch_surf = fs.render("Click Blue Guy for coins!", True, (80,100,160))
        s.blit(ch_surf, (cx + cw//2 - ch_surf.get_width()//2, cy+415))

        # Auto coin timer
        self.clicker_timer += 1
        if self.clicker_timer >= 60 and self.clicker_cps > 0:
            self.clicker_timer = 0
            self.shop_coins += self.clicker_cps

    def draw_house(self):
        """Blue Guy's cozy house - visit and interact!"""
        s = self.screen
        t = pygame.time.get_ticks() * 0.001

        room = self.house_room

        # ── ROOM BACKGROUNDS ────────────────────────────────────────────
        if room == 'living':
            # Warm living room
            for y in range(SCREEN_HEIGHT):
                p = y/SCREEN_HEIGHT
                pygame.draw.line(s,(int(180+p*20),int(140+p*15),int(100+p*10)),(0,y),(SCREEN_WIDTH,y))
            # Floor
            pygame.draw.rect(s,(120,80,40),(0,580,SCREEN_WIDTH,190))
            # Floor boards
            for i in range(0,SCREEN_WIDTH,60):
                pygame.draw.line(s,(100,65,30),(i,580),(i,770),1)
            pygame.draw.line(s,(100,65,30),(0,580),(SCREEN_WIDTH,580),2)
            # Window with outside view
            pygame.draw.rect(s,(100,160,220),(80,120,220,180))
            pygame.draw.rect(s,(60,120,180),(85,125,100,170))
            pygame.draw.rect(s,(80,140,200),(190,125,105,170))
            # Window view - day/night based on level
            sky_col=(100,160,220) if len(self.levels_beaten)<15 else (20,20,60)
            pygame.draw.rect(s,sky_col,(85,125,210,170))
            if len(self.levels_beaten)<15:
                pygame.draw.circle(s,(255,220,80),(160,175),30)
            else:
                pygame.draw.circle(s,(220,220,200),(200,150),20)
                for i in range(15):
                    sx2=(i*137)%210+85; sy2=(i*97)%170+125
                    pygame.draw.circle(s,WHITE,(sx2,sy2),1)
            # Curtains
            pygame.draw.polygon(s,(180,60,60),[(80,120),(80,300),(130,280),(110,120)])
            pygame.draw.polygon(s,(180,60,60),[(300,120),(300,300),(250,280),(270,120)])
            pygame.draw.rect(s,(140,40,40),(75,115,235,14))
            # Sofa
            pygame.draw.rect(s,(160,80,60),(280,450,280,130),0,8)
            pygame.draw.rect(s,(180,100,70),(270,420,300,50),0,8)
            pygame.draw.rect(s,(140,60,40),(270,420,30,160),0,8)
            pygame.draw.rect(s,(140,60,40),(540,420,30,160),0,8)
            # Cushions
            pygame.draw.ellipse(s,(200,120,90),(310,430,80,50))
            pygame.draw.ellipse(s,(200,120,90),(440,430,80,50))
            # TV
            pygame.draw.rect(s,(30,30,30),(640,300,260,180),0,8)
            pygame.draw.rect(s,(20,20,20),(645,305,250,160),0,6)
            if self.tv_on:
                self.tv_timer += 1
                ch = self.tv_channel % 4
                # Different channels
                if ch == 0:  # News
                    pygame.draw.rect(s,(0,50,180),(645,305,250,160))
                    tf=pygame.font.Font(None,22)
                    ts=tf.render("📺 NEWS: Blue Guy saves world!",True,WHITE)
                    s.blit(ts,(648,350))
                    ts2=tf.render("Red Guy still at large",True,YELLOW)
                    s.blit(ts2,(648,375))
                elif ch == 1:  # Cartoon
                    pygame.draw.rect(s,(255,200,100),(645,305,250,160))
                    # Animated cartoon character
                    cx3=745+int(math.sin(self.tv_timer*0.1)*30)
                    pygame.draw.rect(s,BLUE,(cx3,360,30,30))
                    pygame.draw.circle(s,YELLOW,(cx3+15,340),15)
                elif ch == 2:  # Sports
                    pygame.draw.rect(s,(0,120,0),(645,305,250,120))
                    pygame.draw.rect(s,(200,200,200),(645,425,250,40))
                    bx3=int(695+math.sin(self.tv_timer*0.08)*90)
                    pygame.draw.circle(s,WHITE,(bx3,385),10)
                elif ch == 3:  # Static
                    for px2 in range(645,895,4):
                        for py2 in range(305,465,4):
                            c=random.randint(0,2)*127
                            pygame.draw.rect(s,(c,c,c),(px2,py2,4,4))
                tf2=pygame.font.Font(None,20)
                ch_names=["📡 NEWS","🎨 CARTOONS","⚽ SPORTS","📡 STATIC"]
                cs2=tf2.render(ch_names[ch],True,WHITE)
                s.blit(cs2,(648,457))
                # TV glow
                glow=pygame.Surface((260,180),pygame.SRCALPHA)
                pygame.draw.rect(glow,(100,150,255,25),(0,0,260,180))
                s.blit(glow,(640,300))
            else:
                # TV off - reflection
                pygame.draw.rect(s,(15,15,15),(645,305,250,160))
                rf=pygame.font.Font(None,24)
                rs=rf.render("[ off ]",True,(40,40,40))
                s.blit(rs,(755,375))
            # TV stand
            pygame.draw.rect(s,(50,40,30),(740,480,80,20))
            pygame.draw.rect(s,(50,40,30),(750,500,60,50))
            # TV buttons hint
            bf=pygame.font.Font(None,20)
            if not self.tv_on:
                bs=bf.render("Click TV to turn on!",True,(120,100,80))
                s.blit(bs,(645,510))
            else:
                bs=bf.render("Click TV: change channel",True,(120,100,80))
                s.blit(bs,(645,510))
            # Lamp
            pygame.draw.rect(s,(60,50,30),(500,380,12,160))
            pygame.draw.polygon(s,(240,200,120),[(460,370),(560,370),(540,390),(480,390)])
            if True:  # lamp always on
                lamp_g=pygame.Surface((200,150),pygame.SRCALPHA)
                pygame.draw.ellipse(lamp_g,(255,220,100,35),(0,0,200,150))
                s.blit(lamp_g,(410,380))
            # Bookshelf
            pygame.draw.rect(s,(100,70,40),(120,300,160,240))
            for row in range(4):
                for col2 in range(5):
                    bw2=24; bh2=40+random.randint(0,0)*0; bx4=125+col2*30; by4=308+row*58
                    book_col=[(180,60,60),(60,100,180),(60,160,60),(180,160,60),(160,60,180)][col2]
                    pygame.draw.rect(s,book_col,(bx4,by4,bw2,bh2))
                    pygame.draw.line(s,(0,0,0),(bx4,by4),(bx4,by4+bh2),1)
            # Blue Guy on sofa
            bg_x=350; bg_y=425
            pygame.draw.rect(s,getattr(self,'color_equipped',BLUE),(bg_x,bg_y,30,30),0,4)
            pygame.draw.circle(s,WHITE,(bg_x+22,bg_y+10),5)
            pygame.draw.circle(s,BLACK,(bg_x+23,bg_y+11),2)
            hat=getattr(self,'hat_equipped',None)
            if hat: self._draw_hat_at(hat,bg_x+5,bg_y-2)
            # Thought bubble if TV off
            if not self.tv_on:
                for r2,ox2,oy2 in [(4,50,55),(6,60,42),(9,68,28)]:
                    pygame.draw.circle(s,WHITE,(bg_x+ox2,bg_y-oy2+10),r2)
                pygame.draw.ellipse(s,WHITE,(bg_x+62,bg_y-65,70,40))
                tf3=pygame.font.Font(None,18)
                ts3=tf3.render("I need a",True,(40,40,80))
                ts4=tf3.render("vacation...",True,(40,40,80))
                s.blit(ts3,(bg_x+65,bg_y-62))
                s.blit(ts4,(bg_x+65,bg_y-46))
            # Room label
            lf=pygame.font.Font(None,28); ls=lf.render("Living Room",True,(80,50,30))
            s.blit(ls,(12,16))

        elif room == 'bedroom':
            # Night bedroom
            for y in range(SCREEN_HEIGHT):
                p=y/SCREEN_HEIGHT
                pygame.draw.line(s,(int(30+p*15),int(25+p*15),int(50+p*25)),(0,y),(SCREEN_WIDTH,y))
            pygame.draw.rect(s,(70,55,40),(0,580,SCREEN_WIDTH,190))
            # Bed
            pygame.draw.rect(s,(100,80,60),(200,380,450,220),0,8)  # frame
            pygame.draw.rect(s,(220,210,195),(210,420,430,170),0,6) # sheets
            pygame.draw.rect(s,(240,220,200),(210,380,430,60),0,6)  # pillow
            # Pillows
            pygame.draw.ellipse(s,(230,215,200),(230,385,130,50))
            pygame.draw.ellipse(s,(230,215,200),(490,385,130,50))
            # Blue Guy sleeping
            bg_sx=280; bg_sy=415
            pygame.draw.ellipse(s,getattr(self,'color_equipped',BLUE),(bg_sx,bg_sy,60,30))
            pygame.draw.circle(s,WHITE,(bg_sx+50,bg_sy+8),10)
            # ZZZ
            zf=pygame.font.Font(None,28)
            for i,z in enumerate(['z','Z','Z','Z']):
                zx=bg_sx+55+int(math.sin(t*1.2+i)*5)+i*15
                zy=bg_sy-20-i*14+int(math.sin(t+i)*3)
                za=min(255,max(0,int((math.sin(t*0.5+i)+1)*127)))
                zs=zf.render(z,True,(180,180,220))
                zs.set_alpha(za); s.blit(zs,(zx,zy))
            # Star/moon decorations on wall
            for i in range(8):
                sx3=80+i*130; sy3=120+int(math.sin(i*0.8)*30)
                pygame.draw.circle(s,(200,200,100),(sx3,sy3),3)
            pygame.draw.circle(s,(220,220,150),(820,100),35)  # moon
            pygame.draw.circle(s,(30,25,50),(845,90),28)       # crescent
            # Trophy shelf
            pygame.draw.rect(s,(80,55,35),(680,200,230,20))
            if len(self.levels_beaten) > 0:
                tf4=pygame.font.Font(None,22)
                ts5=tf4.render(f"🏆 x{len(self.levels_beaten)} levels",True,YELLOW)
                s.blit(ts5,(688,172))
            pygame.draw.rect(s,(140,100,30),(720,160,30,44))  # trophy
            pygame.draw.circle(s,(180,140,40),(735,155),18)
            # Sticker collection wall
            if len(self.stickers_found)>0:
                sf3=pygame.font.Font(None,22)
                ss2=sf3.render(f"Sticker wall: {len(self.stickers_found)}/30",True,(200,200,220))
                s.blit(ss2,(120,160))
                for i,lv in enumerate(sorted(self.stickers_found)[:12]):
                    sx4=125+(i%6)*45; sy4=185+(i//6)*40
                    pygame.draw.circle(s,YELLOW,(sx4,sy4),14)
                    pygame.draw.circle(s,(255,240,100),(sx4,sy4),10)
                    tf5=pygame.font.Font(None,16)
                    ts6=tf5.render(str(lv+1),True,(80,60,0))
                    s.blit(ts6,(sx4-8,sy4-7))
            lf2=pygame.font.Font(None,28); ls2=lf2.render("Bedroom  💤",True,(120,100,150))
            s.blit(ls2,(12,16))

        elif room == 'kitchen':
            # Bright kitchen
            for y in range(SCREEN_HEIGHT):
                p=y/SCREEN_HEIGHT
                pygame.draw.line(s,(int(220+p*15),int(215+p*10),int(200+p*10)),(0,y),(SCREEN_WIDTH,y))
            pygame.draw.rect(s,(180,160,120),(0,580,SCREEN_WIDTH,190))
            # Tiles
            for tx2 in range(0,SCREEN_WIDTH,40):
                for ty2 in range(580,770,40):
                    c=(175,155,115) if (tx2//40+ty2//40)%2==0 else (190,170,130)
                    pygame.draw.rect(s,c,(tx2,ty2,40,40))
            # Counter
            pygame.draw.rect(s,(100,80,60),(0,450,SCREEN_WIDTH,140))
            pygame.draw.rect(s,(130,110,80),(0,440,SCREEN_WIDTH,20))
            # Cabinets
            for cx4 in range(0,SCREEN_WIDTH,160):
                pygame.draw.rect(s,(160,120,80),(cx4+5,120,150,300),0,4)
                pygame.draw.rect(s,(140,100,60),(cx4+5,120,150,300),2,4)
                pygame.draw.circle(s,(180,150,100),(cx4+80,270),8)
            # Fridge
            pygame.draw.rect(s,(200,200,205),(820,120,160,340),0,6)
            pygame.draw.rect(s,(190,190,195),(825,125,150,155),0,4)
            pygame.draw.rect(s,(190,190,195),(825,285,150,170),0,4)
            pygame.draw.line(s,(150,150,155),(900,125),(900,460),2)
            # Stove
            pygame.draw.rect(s,(60,60,60),(100,440,250,20),0,4)
            for bx5,by5 in [(140,415),(220,415),(140,440),(220,440)]:
                pygame.draw.circle(s,(40,40,40),(bx5,by5),18)
                pygame.draw.circle(s,(80,80,80),(bx5,by5),12)
            # Pot on stove - bubbling
            pygame.draw.ellipse(s,(80,70,60),(115,400,110,30))
            pygame.draw.rect(s,(80,70,60),(125,370,90,35))
            for bi in range(4):
                bub_x=140+bi*20; bub_y=int(368-abs(math.sin(t*2+bi))*15)
                pygame.draw.circle(s,(100,160,180),(bub_x,bub_y),4)
            # Blue Guy cooking
            bg_kx=500; bg_ky=400
            pygame.draw.rect(s,getattr(self,'color_equipped',BLUE),(bg_kx,bg_ky,30,30),0,4)
            pygame.draw.circle(s,WHITE,(bg_kx+22,bg_ky+10),5)
            hat2=getattr(self,'hat_equipped',None)
            if hat2: self._draw_hat_at(hat2,bg_kx+5,bg_ky-2)
            # Chef hat regardless of equipped
            pygame.draw.rect(s,WHITE,(bg_kx+5,bg_ky-14,20,14))
            pygame.draw.ellipse(s,WHITE,(bg_kx+2,bg_ky-22,26,18))
            # Spoon
            spoon_angle=math.sin(t*2)*0.4
            sx5=bg_kx+25+int(math.cos(spoon_angle)*20)
            sy5=bg_ky+5+int(math.sin(spoon_angle)*20)
            pygame.draw.line(s,GRAY,(bg_kx+20,bg_ky+15),(sx5,sy5),3)
            pygame.draw.circle(s,GRAY,(sx5,sy5),5)
            # Coins on counter (spendable)
            cf2=pygame.font.Font(None,26)
            cs3=cf2.render(f"Pantry coins: {self.shop_coins}",True,(80,60,20))
            s.blit(cs3,(300,460))
            # Recipe on wall
            pygame.draw.rect(s,WHITE,(640,200,160,120),0,4)
            pygame.draw.rect(s,(180,160,100),(640,200,160,120),2,4)
            rf2=pygame.font.Font(None,20)
            for i,line in enumerate(["📋 TODAY'S RECIPE","","• 1 cup courage","• 2 bullets","• defeat Red Guy"]):
                rs2=rf2.render(line,True,(60,40,20))
                s.blit(rs2,(648,208+i*20))
            # Mini-game buttons
            mg1=pygame.Rect(200,500,220,44); mg2=pygame.Rect(440,500,240,44)
            mx2,my2=pygame.mouse.get_pos()
            for btn,lbl,bc in [(mg1,"🐚 Shell Game",(60,40,100)),(mg2,"🔢 Guess Number",(40,70,40))]:
                hv=btn.collidepoint(mx2,my2)
                pygame.draw.rect(s,(bc[0]+20,bc[1]+20,bc[2]+20) if hv else bc,btn,0,8)
                pygame.draw.rect(s,WHITE,btn,1,8)
                ls4=pygame.font.Font(None,26).render(lbl,True,WHITE)
                s.blit(ls4,(btn.centerx-ls4.get_width()//2,btn.centery-ls4.get_height()//2))
            self._mg1_rect=mg1; self._mg2_rect=mg2
            lf3=pygame.font.Font(None,28); ls3=lf3.render("Kitchen  🍳",True,(80,60,20))
            s.blit(ls3,(12,16))

        elif room == 'garden':
            self.draw_garden()
            # Still draw the nav tabs and store rects so clicking works!
            rooms_g = [('living','🛋 Living'),('bedroom','🛏 Bedroom'),('kitchen','🍳 Kitchen'),('garden','🌻 Garden')]
            for i,(rid,rname) in enumerate(rooms_g):
                tx3=20+i*220; ty3=SCREEN_HEIGHT-50
                active = (self.house_room==rid)
                bg=(80,60,40) if active else (50,40,30)
                tab=pygame.Rect(tx3,ty3,200,40)
                pygame.draw.rect(s,bg,tab,0,8)
                pygame.draw.rect(s,(140,100,60) if active else (80,60,40),tab,2,8)
                tf6=pygame.font.Font(None,26); ts7=tf6.render(rname,True,WHITE if active else (160,130,100))
                s.blit(ts7,(tx3+100-ts7.get_width()//2,ty3+10))
                setattr(self,f'_house_tab_{rid}',tab)
            # Close button
            cb=pygame.Rect(SCREEN_WIDTH-60,10,50,34)
            pygame.draw.rect(s,(120,40,40),cb,0,6)
            pygame.draw.rect(s,RED,cb,2,6)
            cf=pygame.font.Font(None,26); cs3=cf.render("✕ ESC",True,WHITE)
            s.blit(cs3,(SCREEN_WIDTH-58,18))
            self._house_close_rect=cb
            # Coins display
            fn_c=pygame.font.Font(None,26)
            s.blit(fn_c.render(f"💰 {self.shop_coins}",True,YELLOW),(SCREEN_WIDTH-160,18))
            return

        # ── ROOM NAVIGATION TABS ─────────────────────────────────────────
        rooms = [('living','🛋 Living'),('bedroom','🛏 Bedroom'),('kitchen','🍳 Kitchen'),('garden','🌻 Garden')]
        for i,(rid,rname) in enumerate(rooms):
            btn=pygame.Rect(SCREEN_WIDTH-220+i*0,SCREEN_HEIGHT-54+i*0,0,0)
            tx3=20+i*220; ty3=SCREEN_HEIGHT-50
            active = (self.house_room==rid)
            bg=(80,60,40) if active else (50,40,30)
            tab=pygame.Rect(tx3,ty3,200,40)
            pygame.draw.rect(s,bg,tab,0,8)
            pygame.draw.rect(s,(140,100,60) if active else (80,60,40),tab,2,8)
            tf6=pygame.font.Font(None,26); ts7=tf6.render(rname,True,WHITE if active else (160,130,100))
            s.blit(ts7,(tx3+100-ts7.get_width()//2,ty3+10))
            # Store tab rects
            setattr(self,f'_house_tab_{rid}',tab)

        # TV rect for clicking
        self._tv_rect = pygame.Rect(640,300,260,180)

        # Close button
        cb=pygame.Rect(SCREEN_WIDTH-60,10,50,34)
        pygame.draw.rect(s,(120,40,40),cb,0,6)
        pygame.draw.rect(s,RED,cb,2,6)
        cf3=pygame.font.Font(None,26); cs4=cf3.render("✕ ESC",True,WHITE)
        s.blit(cs4,(SCREEN_WIDTH-58,18))

        # Coins display
        cf4=pygame.font.Font(None,28); cs5=cf4.render(f"💰 {self.shop_coins}",True,YELLOW)
        s.blit(cs5,(SCREEN_WIDTH-160,18))

    def unlock_achievement(self, aid):
        """Unlock an achievement and show a popup."""
        if aid in self.achievements_earned or aid not in self.ACHIEVEMENTS:
            return
        self.achievements_earned.add(aid)
        name, desc, icon = self.ACHIEVEMENTS[aid]
        self.achievement_popup.append({'text': name, 'desc': desc, 'icon': icon, 'timer': 240})
        self.shop_coins += 10   # bonus coins for every achievement!
        self.save_game()

    def check_achievements(self):
        """Call each frame during gameplay to check conditions."""
        b = self.levels_beaten
        # Level milestones
        if 14 in b: self.unlock_achievement('level15')
        if len(b) >= 30: self.unlock_achievement('level30')
        # Boss
        if len(b) > 0 and (9 in b or 14 in b or 29 in b):
            self.unlock_achievement('boss1')
        if 9 in b and 14 in b and 29 in b:
            self.unlock_achievement('boss_all')
        # Stickers
        if len(self.stickers_found) >= 5:  self.unlock_achievement('sticker_5')
        if len(self.stickers_found) >= 30: self.unlock_achievement('sticker_all')
        # Clicker
        if self.clicker_clicks >= 100: self.unlock_achievement('clicker_100')
        # Hats
        if len(self.hats_owned) >= 1: self.unlock_achievement('hat_owner')
        if len(self.hats_owned) >= 5: self.unlock_achievement('all_hats')
        # Shop
        if self.shop_spent >= 50: self.unlock_achievement('shopper')
        # Combo
        if self.max_combo >= 3:  self.unlock_achievement('combo3')
        if self.max_combo >= 10: self.unlock_achievement('combo10')
        # Dash
        if self.dash_count >= 20: self.unlock_achievement('dasher')
        # TV
        if len(self.tv_channels_seen) >= 4: self.unlock_achievement('tv_watcher')
        # House
        if getattr(self, '_house_visited', False): self.unlock_achievement('home_owner')

    def draw_achievement_popups(self):
        """Draw sliding achievement notification toasts."""
        s = self.screen
        for i, pop in enumerate(self.achievement_popup[:]):
            pop['timer'] -= 1
            if pop['timer'] <= 0:
                self.achievement_popup.remove(pop)
                continue
            # Slide in from right
            slide = min(1.0, (240 - pop['timer']) / 20.0)
            slide_out = max(0.0, 1.0 - (pop['timer'] / 30.0))
            x_off = int((1.0 - slide + slide_out) * 320)
            px = SCREEN_WIDTH - 310 + x_off
            py = 60 + i * 80
            # Panel
            panel = pygame.Surface((295, 66), pygame.SRCALPHA)
            panel.fill((20, 30, 20, 210))
            pygame.draw.rect(panel, (80, 200, 80), (0, 0, 295, 66), 2, 10)
            s.blit(panel, (px, py))
            # Icon
            try:
                ef = pygame.font.SysFont('segoe ui emoji', 28)
                ic = ef.render(pop['icon'], True, WHITE)
                s.blit(ic, (px + 8, py + 16))
            except Exception:
                pass
            # Text
            ft = pygame.font.Font(None, 22)
            fh = pygame.font.Font(None, 18)
            s.blit(ft.render("Achievement Unlocked!", True, (100, 220, 100)), (px + 44, py + 8))
            s.blit(ft.render(pop['text'], True, WHITE), (px + 44, py + 26))
            s.blit(fh.render(pop['desc'], True, (160, 160, 160)), (px + 44, py + 46))

    def draw_achievements_screen(self):
        """Full achievements overlay."""
        s = self.screen
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        s.blit(overlay, (0, 0))
        ft = pygame.font.Font(None, 52)
        ts = ft.render(f"ACHIEVEMENTS  {len(self.achievements_earned)}/{len(self.ACHIEVEMENTS)}", True, YELLOW)
        s.blit(ts, (SCREEN_WIDTH//2 - ts.get_width()//2, 20))
        fn = pygame.font.Font(None, 26)
        fd = pygame.font.Font(None, 20)
        cols = 2; col_w = SCREEN_WIDTH // cols
        for i, (aid, (name, desc, icon)) in enumerate(self.ACHIEVEMENTS.items()):
            col = i % cols; row = i // cols
            ax = 30 + col * col_w
            ay = 80 + row * 62
            earned = aid in self.achievements_earned
            bg = (20, 40, 20) if earned else (25, 25, 35)
            bdr = (80, 180, 80) if earned else (50, 50, 70)
            pygame.draw.rect(s, bg,  (ax, ay, col_w - 20, 54), 0, 8)
            pygame.draw.rect(s, bdr, (ax, ay, col_w - 20, 54), 2, 8)
            try:
                ef = pygame.font.SysFont('segoe ui emoji', 22)
                ic = ef.render(icon if earned else '🔒', True, WHITE)
                s.blit(ic, (ax + 8, ay + 14))
            except Exception:
                pass
            col2 = WHITE if earned else GRAY
            s.blit(fn.render(name if earned else '???', True, col2), (ax + 44, ay + 10))
            s.blit(fd.render(desc if earned else 'Keep playing to unlock', True, (120,120,120) if not earned else (160,180,160)), (ax + 44, ay + 32))
            if earned:
                s.blit(fd.render("+10 🪙", True, YELLOW), (ax + col_w - 80, ay + 18))
        fh = pygame.font.Font(None, 24)
        hs = fh.render("Press A or ESC to close", True, (80, 80, 100))
        s.blit(hs, (SCREEN_WIDTH//2 - hs.get_width()//2, SCREEN_HEIGHT - 36))

    def draw_daily_challenge(self):
        """Daily challenge banner on menu."""
        s = self.screen
        t = pygame.time.get_ticks() * 0.001
        bx = SCREEN_WIDTH//2 - 200
        by = 640
        pulse = int(abs(math.sin(t * 2)) * 20)
        col = (50 + pulse, 30, 80 + pulse)
        pygame.draw.rect(s, col, (bx, by, 400, 52), 0, 10)
        pygame.draw.rect(s, PURPLE, (bx, by, 400, 52), 2, 10)
        fn = pygame.font.Font(None, 26)
        fd = pygame.font.Font(None, 20)
        goal_text = {'no_damage':'No deaths!','speed_run':'Beat in 15 sec!','all_coins':'Collect ALL coins!'}
        status = "✅ COMPLETED!" if self.daily_completed else f"Reward: {self.daily_reward}🪙"
        s.blit(fn.render(f"📅 DAILY: Level {self.daily_level+1} — {goal_text[self.daily_goal]}", True, WHITE), (bx+10, by+8))
        sc = GREEN if self.daily_completed else YELLOW
        s.blit(fd.render(status, True, sc), (bx+10, by+32))

    def draw_weather(self):
        """Rain or snow effect over gameplay based on level."""
        if self.state not in ['playing']: return
        lv = self.current_level
        # Rain in woods levels (15-29), snow in late normal levels (10-14)
        is_rain  = 15 <= lv <= 29
        is_snow  = 10 <= lv <= 14
        if not is_rain and not is_snow: return
        self.weather_timer += 1
        # Spawn
        if is_rain and self.weather_timer % 2 == 0:
            self.weather_particles.append({
                'x': random.randint(0, SCREEN_WIDTH), 'y': -10,
                'vx': -1, 'vy': 14, 'type': 'rain', 'life': 80
            })
        if is_snow and self.weather_timer % 4 == 0:
            self.weather_particles.append({
                'x': random.randint(0, SCREEN_WIDTH), 'y': -10,
                'vx': random.uniform(-0.5, 0.5), 'vy': 2, 'type': 'snow', 'life': 200
            })
        # Update and draw
        for wp in self.weather_particles[:]:
            wp['x'] += wp['vx']; wp['y'] += wp['vy']; wp['life'] -= 1
            if wp['life'] <= 0 or wp['y'] > SCREEN_HEIGHT:
                self.weather_particles.remove(wp)
                continue
            if wp['type'] == 'rain':
                a = min(180, wp['life'] * 3)
                pygame.draw.line(self.screen, (120, 160, 220),
                    (int(wp['x']), int(wp['y'])),
                    (int(wp['x']) + 2, int(wp['y']) + 8), 1)
            else:
                r = random.randint(2, 4)
                pygame.draw.circle(self.screen, (220, 230, 255),
                    (int(wp['x']), int(wp['y'])), r)
        # Cap particles
        if len(self.weather_particles) > 300:
            self.weather_particles = self.weather_particles[-300:]

    def handle_cheat_codes(self, key):
        """Check if cheat code has been entered."""
        self.cheat_buffer.append(key)
        if len(self.cheat_buffer) > 10:
            self.cheat_buffer.pop(0)
        for name, seq in self.CHEATS.items():
            if self.cheat_buffer[-len(seq):] == seq:
                if name == 'godmode':
                    self.cheat_active['godmode'] = 600
                    self.floaty_texts.append({'x': SCREEN_WIDTH//2-80, 'y': 300,
                        'vy': -1, 'text': '😎 GOD MODE ON!', 'col': YELLOW, 'life': 120, 'maxlife': 120})
                elif name == 'coins100':
                    self.shop_coins += 100; self.bank_coins += 100
                    self.floaty_texts.append({'x': SCREEN_WIDTH//2-80, 'y': 300,
                        'vy': -1, 'text': '+100 COINS! 💰', 'col': YELLOW, 'life': 120, 'maxlife': 120})
                elif name == 'allhats':
                    for h in self.HATS: self.hats_owned.add(h['key'])
                    self.floaty_texts.append({'x': SCREEN_WIDTH//2-80, 'y': 300,
                        'vy': -1, 'text': '🎩 ALL HATS!', 'col': CYAN, 'life': 120, 'maxlife': 120})
                self.cheat_buffer.clear()

    def draw_garden(self):
        """Blue Guy's garden room."""
        s = self.screen
        t = pygame.time.get_ticks() * 0.001
        # Sky
        for y in range(SCREEN_HEIGHT):
            p = y/SCREEN_HEIGHT
            pygame.draw.line(s,(int(100+p*60),int(160+p*40),int(220-p*40)),(0,y),(SCREEN_WIDTH,y))
        # Ground
        pygame.draw.rect(s,(80,140,60),(0,560,SCREEN_WIDTH,210))
        for gx in range(0,SCREEN_WIDTH,20):
            pygame.draw.line(s,(70,120,50),(gx,560),(gx+5,580),2)
        # Sun
        pygame.draw.circle(s,(255,230,100),(SCREEN_WIDTH-120,80),45)
        for i in range(12):
            a = i/12*math.pi*2 + t*0.3
            pygame.draw.line(s,(255,240,120),
                (SCREEN_WIDTH-120+int(math.cos(a)*52),80+int(math.sin(a)*52)),
                (SCREEN_WIDTH-120+int(math.cos(a)*68),80+int(math.sin(a)*68)),3)
        # Flowers
        for i, (fx,fy,fc) in enumerate([(150,520),(280,510),(420,530),(600,515),(750,525),(900,510),(1050,520)]):
            sway = math.sin(t*1.2+i*0.8)*4
            # Stem
            pygame.draw.line(s,(60,140,40),(fx,fy+30),(fx+int(sway),fy-40+int(sway)),3)
            # Petals
            for j in range(6):
                pa = j/6*math.pi*2 + t*0.5
                px2 = fx+int(sway)+int(math.cos(pa)*12)
                py2 = fy-40+int(sway)+int(math.sin(pa)*12)
                pygame.draw.circle(s,fc,(px2,py2),6)
            pygame.draw.circle(s,YELLOW,(fx+int(sway),fy-40+int(sway)),7)
        # Vegetables garden patch
        pygame.draw.rect(s,(100,70,40),(200,430,300,90),0,6)
        pygame.draw.rect(s,(80,55,30),(200,430,300,90),2,6)
        for i in range(5):
            vx = 225+i*55; vy=440
            pygame.draw.line(s,(60,130,40),(vx,vy+40),(vx,vy),3)
            pygame.draw.ellipse(s,(220,40,40),(vx-12,vy-15,24,20))  # tomato
        # Sticker garden (stickers you own become flowers)
        if len(self.stickers_found) > 0:
            fn = pygame.font.Font(None,22)
            gs = fn.render(f"🌸 Garden Stickers: {len(self.stickers_found)}/30",True,(40,80,20))
            s.blit(gs,(600,430))
        # Pond
        pygame.draw.ellipse(s,(80,150,220),(700,450,240,80))
        pygame.draw.ellipse(s,(100,170,240),(710,460,220,60),2)
        # Fish
        fish_x = 700+int(math.sin(t)*90)
        pygame.draw.ellipse(s,ORANGE,(fish_x,480,28,14))
        pts=[(fish_x,487),(fish_x-12,480),(fish_x-12,494)]
        pygame.draw.polygon(s,(220,100,20),pts)
        # Ripples - guard against zero size
        for r in range(1,4):
            rp = (t*0.8+r*0.3)%1
            rw = max(2, int(rp*80)); rh = max(2, int(rp*20))
            rx2 = int(820-rp*40); ry2 = int(488-rp*10)
            pygame.draw.ellipse(s,(100,180,240),(rx2,ry2,rw,rh),1)
        # Blue Guy gardening
        bgx=460; bgy=490
        pygame.draw.rect(s,getattr(self,'color_equipped',BLUE),(bgx,bgy,30,30),0,4)
        hat=getattr(self,'hat_equipped',None)
        if hat: self._draw_hat_at(hat,bgx+5,bgy-2)
        # Watering can
        pygame.draw.rect(s,(150,150,180),(bgx+28,bgy+8,24,16),0,4)
        pygame.draw.line(s,(150,150,180),(bgx+52,bgy+10),(bgx+65,bgy),3)
        for i in range(3):
            pygame.draw.circle(s,(100,170,220),(bgx+68+i*5,bgy+3+i*4),2)
        # Coins from gardening
        fn2=pygame.font.Font(None,22)
        cs2=fn2.render("Gardening earns 2 coins/visit!",True,(40,80,20))
        s.blit(cs2,(200,380))
        # Fence
        for fx2 in range(0,SCREEN_WIDTH,50):
            pygame.draw.rect(s,(160,110,60),(fx2+2,530,8,40),0,3)
            pygame.draw.rect(s,(140,90,40),(0,545,SCREEN_WIDTH,8))
        fn3=pygame.font.Font(None,28); ls=fn3.render("Garden 🌻",True,(40,80,20))
        s.blit(ls,(12,16))

    def draw_journal(self):
        """Blue Guy's journal — unlocks as you beat levels."""
        s = self.screen
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,200))
        s.blit(overlay,(0,0))
        # Book background
        pygame.draw.rect(s,(200,170,120),(100,60,SCREEN_WIDTH-200,SCREEN_HEIGHT-120),0,16)
        pygame.draw.rect(s,(160,120,80),(100,60,SCREEN_WIDTH-200,SCREEN_HEIGHT-120),3,16)
        # Spine
        pygame.draw.rect(s,(140,100,60),(100,60,40,SCREEN_HEIGHT-120),0,16)
        # Title
        ft=pygame.font.Font(None,52)
        ts=ft.render("📓 Blue Guy's Journal",True,(80,50,20))
        s.blit(ts,(SCREEN_WIDTH//2-ts.get_width()//2,78))
        pygame.draw.line(s,(140,100,60),(160,128),(SCREEN_WIDTH-120,128),2)
        # Entries
        fn=pygame.font.Font(None,28); fd=pygame.font.Font(None,22)
        unlocked = [(lv,title,text) for lv,(title,text) in self.JOURNAL_ENTRIES.items()
                    if lv in self.levels_beaten or lv==0]
        locked_count = len(self.JOURNAL_ENTRIES) - len(unlocked)
        for i,(lv,title,text) in enumerate(unlocked):
            ey = 148 + i * 90
            pygame.draw.rect(s,(220,190,140),(155,ey,SCREEN_WIDTH-320,80),0,6)
            pygame.draw.rect(s,(160,120,80),(155,ey,SCREEN_WIDTH-320,80),1,6)
            s.blit(fn.render(f"✏️  {title}",True,(80,50,20)),(168,ey+8))
            # Word-wrap text
            words=text.split(); line=''; ly=ey+34
            for w in words:
                test=line+w+' '
                if fd.size(test)[0]>700: s.blit(fd.render(line.strip(),True,(60,40,20)),(168,ly)); ly+=20; line=w+' '
                else: line=test
            if line: s.blit(fd.render(line.strip(),True,(60,40,20)),(168,ly))
        if locked_count>0:
            ls=fd.render(f"🔒 {locked_count} more entries unlock as you beat levels...",True,(120,90,60))
            s.blit(ls,(165,148+len(unlocked)*90+10))
        # Close hint
        ch=pygame.font.Font(None,24).render("Press J or ESC to close",True,(100,70,40))
        s.blit(ch,(SCREEN_WIDTH//2-ch.get_width()//2,SCREEN_HEIGHT-74))

    def draw_minigame(self):
        """Shell game and number guesser mini-games in the house."""
        s = self.screen
        t = pygame.time.get_ticks() * 0.001
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,185))
        s.blit(overlay,(0,0))
        pygame.draw.rect(s,(30,25,50),(200,100,SCREEN_WIDTH-400,SCREEN_HEIGHT-200),0,16)
        pygame.draw.rect(s,(80,60,140),(200,100,SCREEN_WIDTH-400,SCREEN_HEIGHT-200),3,16)
        ft=pygame.font.Font(None,42); fn=pygame.font.Font(None,28); fd=pygame.font.Font(None,22)

        if self.minigame_active == 'shell':
            s.blit(ft.render("🐚 Shell Game  — Cost: 5 coins",True,WHITE),(220,115))
            s.blit(fd.render("Find the ball! Win 15 coins.",True,GRAY),(220,155))
            cup_positions=[350,590,830]
            ball_visible=(self.shell_phase in ('hide','result'))
            for i,cx2 in enumerate(cup_positions):
                cy2=350
                # Cup
                cup_col=(140,100,60) if i!=self.shell_ball or not ball_visible else (140,100,60)
                pygame.draw.rect(s,cup_col,(cx2-40,cy2-60,80,90),0,10)
                pygame.draw.rect(s,(160,120,80),(cx2-40,cy2-60,80,90),2,10)
                # Handle
                pygame.draw.ellipse(s,(120,80,40),(cx2-20,cy2-80,40,24))
                # Ball under cup
                if ball_visible and i==self.shell_ball:
                    pygame.draw.circle(s,RED,(cx2,cy2+20),14)
                    pygame.draw.circle(s,(255,100,100),(cx2-4,cy2+16),5)
                # Number label
                ns=fn.render(str(i+1),True,WHITE); s.blit(ns,(cx2-ns.get_width()//2,cy2+40))
            if self.shell_phase=='hide':
                s.blit(fn.render("Remember which cup!  Press 1 2 or 3 to pick",True,YELLOW),(220,460))
            elif self.shell_phase=='result':
                msg="✅ CORRECT! +15 coins!" if self.shell_result=='win' else "❌ Wrong! Better luck next time."
                col=GREEN if self.shell_result=='win' else RED
                s.blit(fn.render(msg,True,col),(220,460))
                s.blit(fd.render("Press SPACE to play again or ESC to leave",True,GRAY),(220,490))

        elif self.minigame_active == 'guess':
            s.blit(ft.render("🔢 Number Guesser  — Free!",True,WHITE),(220,115))
            s.blit(fd.render(f"Guess 1-10. Win 20 coins!  Attempts left: {self.guess_attempts}",True,GRAY),(220,155))
            pygame.draw.rect(s,(40,30,70),(300,280,600,80),0,10)
            pygame.draw.rect(s,(80,60,140),(300,280,600,80),2,10)
            fs2=pygame.font.Font(None,52)
            input_text=self.guess_input if self.guess_input else '_'
            s.blit(fs2.render(input_text,True,CYAN),(590,292))
            hint_text=""
            if self.guess_result=='win': hint_text="🎉 CORRECT! You win 20 coins!"
            elif self.guess_result=='too_high': hint_text="📉 Too high! Try lower."
            elif self.guess_result=='too_low':  hint_text="📈 Too low! Try higher."
            elif self.guess_result=='lose':     hint_text=f"💀 Out of guesses! It was {self.guess_target}"
            if hint_text:
                col=GREEN if self.guess_result=='win' else (RED if self.guess_result=='lose' else YELLOW)
                s.blit(fn.render(hint_text,True,col),(220,390))
            s.blit(fd.render("Type a number and press ENTER. ESC to leave.",True,GRAY),(220,440))

        ch=pygame.font.Font(None,22).render("ESC to exit mini-game",True,(100,80,140))
        s.blit(ch,(SCREEN_WIDTH//2-ch.get_width()//2,SCREEN_HEIGHT-116))

    def draw_credits(self):
        """Scrolling credits screen."""
        s = self.screen
        t = pygame.time.get_ticks() * 0.001
        # Starfield
        for i in range(80):
            sx=( i*193)%SCREEN_WIDTH; sy=(i*137+int(self.credits_scroll*0.3))%SCREEN_HEIGHT
            br=int(abs(math.sin(t*0.4+i))*150+80)
            pygame.draw.circle(s,(br,br,br),(sx,sy),1)
        self.credits_scroll += 0.8
        lines = [
            ('title',  "MINIMAL PLATFORMER 4"),
            ('title',  "THE RED UPRISING"),
            ('',''),('',''),
            ('head',   "CREATED BY"),
            ('body',   "Kyle 🎮"),
            ('body',   "with Claude (AI)"),
            ('',''),
            ('head',   "GAME DESIGN"),
            ('body',   "Blue Guy (protagonist)"),
            ('body',   "Red Guy (villain)"),
            ('body',   "The Green Guys (cannon fodder)"),
            ('',''),
            ('head',   "SPECIAL THANKS"),
            ('body',   "Pygame community"),
            ('body',   "Coffee ☕"),
            ('body',   "Water bottles everywhere"),
            ('',''),
            ('head',   "STATS THIS SESSION"),
            ('body',   f"Levels beaten: {len(self.levels_beaten)} / 30"),
            ('body',   f"Stickers found: {len(self.stickers_found)} / 30"),
            ('body',   f"Total deaths: {self.total_deaths}"),
            ('body',   f"Max combo: x{self.max_combo}"),
            ('body',   f"Achievements: {len(self.achievements_earned)} / {len(self.ACHIEVEMENTS)}"),
            ('body',   f"Coins earned: {self.bank_coins}"),
            ('',''),
            ('head',   "SECRET CHEATS"),
            ('body',   "Type  god  →  God Mode"),
            ('body',   "Type  coins  →  +100 coins"),
            ('body',   "Type  hats  →  All hats!"),
            ('',''),('',''),
            ('end',    "THANK YOU FOR PLAYING! 🎮"),
            ('end',    "Blue Guy will return..."),
        ]
        start_y = SCREEN_HEIGHT - self.credits_scroll + 100
        for i,(style,text) in enumerate(lines):
            y = start_y + i * 48
            if y < -50 or y > SCREEN_HEIGHT + 50: continue
            if style=='title':
                f=pygame.font.Font(None,72); c=YELLOW
            elif style=='head':
                f=pygame.font.Font(None,42); c=CYAN
            elif style=='end':
                f=pygame.font.Font(None,56); c=(int(abs(math.sin(t))*255),200,100)
            else:
                f=pygame.font.Font(None,30); c=(200,200,200)
            if not text: continue
            ts=f.render(text,True,c)
            s.blit(ts,(SCREEN_WIDTH//2-ts.get_width()//2,int(y)))
        if start_y + len(lines)*48 < 0:
            self.credits_scroll = 0  # loop
        # Close hint
        ch=pygame.font.Font(None,22).render("ESC to close credits",True,(80,80,100))
        s.blit(ch,(SCREEN_WIDTH//2-ch.get_width()//2,SCREEN_HEIGHT-30))

    def draw_big_boss_healthbar(self):
        """Dramatic boss health bar at top of screen."""
        boss = self.boss or getattr(self,'flying_boss',None)
        if not boss: return
        s = self.screen
        t = pygame.time.get_ticks() * 0.001
        max_hp = 8 if getattr(self,'flying_boss',None) else 5
        hp = boss.health
        bw = 500; bh = 24
        bx = SCREEN_WIDTH//2 - bw//2; by = 18
        # Background
        pygame.draw.rect(s,(20,10,10),(bx-4,by-4,bw+8,bh+8),0,8)
        pygame.draw.rect(s,(60,20,20),(bx,by,bw,bh),0,6)
        # Health fill with pulse on low HP
        fill = int(bw * hp / max_hp)
        r = 220 if hp > max_hp//3 else int(200+abs(math.sin(t*5))*55)
        g = int(20 + (hp/max_hp)*180)
        pygame.draw.rect(s,(r,g,20),(bx,by,fill,bh),0,6)
        # Segments
        for i in range(1,max_hp):
            sx=bx+int(bw*i/max_hp)
            pygame.draw.line(s,(30,15,15),(sx,by),(sx,by+bh),2)
        # Border
        pygame.draw.rect(s,(200,50,50),(bx-4,by-4,bw+8,bh+8),2,8)
        # Label
        boss_name = "👑 FLYING BOSS" if getattr(self,'flying_boss',None) else "👑 BOSS"
        fn=pygame.font.Font(None,22)
        ns=fn.render(f"{boss_name}  {hp}/{max_hp} HP",True,WHITE)
        s.blit(ns,(SCREEN_WIDTH//2-ns.get_width()//2,by+4))
        # Warning flash on last HP
        if hp == 1:
            if int(t*4)%2==0:
                ws=pygame.font.Font(None,26).render("⚠️ LAST HP!",True,RED)
                s.blit(ws,(SCREEN_WIDTH//2-ws.get_width()//2,by+bh+8))

    def draw_level_transition(self):
        """Black fade in/out between levels."""
        if self.transition_timer <= 0: return
        s = self.screen
        self.transition_timer -= 1
        alpha = 0
        if self.transition_type == 'out':
            alpha = int(255 * (1 - self.transition_timer / 30))
        else:
            alpha = int(255 * self.transition_timer / 30)
        fade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        fade.fill(BLACK)
        fade.set_alpha(alpha)
        s.blit(fade,(0,0))

    def draw_clouds(self):
        """Parallax drifting clouds in sky."""
        s = self.screen
        t = pygame.time.get_ticks() * 0.001
        for cloud in self.clouds:
            cloud['x'] -= cloud['speed']
            if cloud['x'] < -cloud['w'] - 100:
                cloud['x'] = SCREEN_WIDTH + 100
            layer_alpha = [40, 70, 100][cloud['layer']]
            cw = cloud['w']; cy = cloud['y']
            cx2 = int(cloud['x'])
            surf = pygame.Surface((cw + 40, 40), pygame.SRCALPHA)
            for bx, by2, br in [(cw//2, 20, 20),(cw//3, 20, 15),(2*cw//3, 20, 17),(cw//4, 24, 12),(3*cw//4, 22, 13)]:
                pygame.draw.circle(surf, (255,255,255,layer_alpha), (bx, by2), br)
            s.blit(surf, (cx2, cy))

    def draw_health(self):
        """Draw heart health bar in HUD."""
        s = self.screen
        for i in range(self.player_max_health):
            hx = SCREEN_WIDTH - 30 - i * 32
            hy = 12
            full = i < self.player_health
            col = (220, 40, 60) if full else (60, 30, 35)
            # Heart shape with two circles + triangle
            pygame.draw.circle(s, col, (hx - 5, hy + 7), 7)
            pygame.draw.circle(s, col, (hx + 5, hy + 7), 7)
            pygame.draw.polygon(s, col, [(hx - 12, hy + 10), (hx + 12, hy + 10), (hx, hy + 24)])
            if full:
                pygame.draw.circle(s, (255, 100, 120), (hx - 5, hy + 5), 3)

    def draw_level_banner(self):
        """Big level name slides in and fades out at level start."""
        if self.level_banner_timer <= 0:
            return
        self.level_banner_timer -= 1
        t = self.level_banner_timer
        s = self.screen
        # Slide in: 0-30 frames, hold 30-150, slide out 150-180
        if t > 150:
            alpha = int(255 * (180 - t) / 30)
            ox = int((180 - t) / 30 * 80)
        elif t > 30:
            alpha = 255; ox = 0
        else:
            alpha = int(255 * t / 30)
            ox = int((30 - t) / 30 * 80)
        bg = pygame.Surface((700, 70), pygame.SRCALPHA)
        bg.fill((0, 0, 0, int(alpha * 0.6)))
        bx = SCREEN_WIDTH//2 - 350 + ox
        s.blit(bg, (bx, SCREEN_HEIGHT//2 - 35))
        fb = pygame.font.Font(None, 52)
        ts2 = fb.render(self.level_banner_name, True, YELLOW)
        ts2.set_alpha(alpha)
        s.blit(ts2, (SCREEN_WIDTH//2 - ts2.get_width()//2 + ox, SCREEN_HEIGHT//2 - ts2.get_height()//2))
        # Subtitle: daily challenge reminder
        if self.current_level == self.daily_level and not self.daily_completed:
            goal_text = {'no_damage':'★ Daily: No Deaths!','speed_run':'★ Daily: Beat in 15 sec!','all_coins':'★ Daily: All Coins!'}
            fd = pygame.font.Font(None, 26)
            ds = fd.render(goal_text[self.daily_goal], True, (255, 200, 100))
            ds.set_alpha(alpha)
            s.blit(ds, (SCREEN_WIDTH//2 - ds.get_width()//2 + ox, SCREEN_HEIGHT//2 + 22))

    def draw_pause(self):
        """Pause screen overlay."""
        s = self.screen
        t = pygame.time.get_ticks() * 0.001
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        s.blit(overlay, (0,0))
        ft = pygame.font.Font(None, 72)
        ps = ft.render("⏸ PAUSED", True, WHITE)
        s.blit(ps, (SCREEN_WIDTH//2 - ps.get_width()//2, 120))
        # Stats
        fn = pygame.font.Font(None, 30)
        stats = [
            f"Level: {self.current_level+1} — {self.LEVEL_NAMES.get(self.current_level,'')}",
            f"Health: {'♥'*self.player_health}{'♡'*(self.player_max_health-self.player_health)}",
            f"Coins this level: {self.coins_collected} / {self.total_coins}",
            f"Total coins: {self.bank_coins}",
            f"Deaths: {self.total_deaths}   Max combo: x{self.max_combo}",
            f"Stickers: {len(self.stickers_found)}/30   Achievements: {len(self.achievements_earned)}/{len(self.ACHIEVEMENTS)}",
        ]
        for i, stat in enumerate(stats):
            ss = fn.render(stat, True, (200,200,200))
            s.blit(ss, (SCREEN_WIDTH//2 - ss.get_width()//2, 210 + i*36))
        # Options
        options = ["▶  Resume (P)", "🏠  Back to Menu (ESC)", "💾  Save (F5)"]
        for i, opt in enumerate(options):
            active = i == self.pause_option
            col = YELLOW if active else (140,140,160)
            size = 36 if active else 28
            fo = pygame.font.Font(None, size)
            os2 = fo.render(opt, True, col)
            s.blit(os2, (SCREEN_WIDTH//2 - os2.get_width()//2, 440 + i*52))
            if active:
                pulse = int(abs(math.sin(t*4))*30)
                pygame.draw.rect(s, (60+pulse, 80+pulse, 200+pulse),
                    (SCREEN_WIDTH//2 - os2.get_width()//2 - 16, 436 + i*52, os2.get_width()+32, 40), 2, 8)

    def draw_game_over(self):
        """Dramatic game over screen."""
        s = self.screen
        t = pygame.time.get_ticks() * 0.001
        self.game_over_timer += 1
        for y in range(SCREEN_HEIGHT):
            p = y/SCREEN_HEIGHT
            pygame.draw.line(s,(int(40+p*20),0,int(10+p*10)),(0,y),(SCREEN_WIDTH,y))
        # Falling particles
        for i in range(30):
            px2 = (i*173 + int(t*40))%SCREEN_WIDTH
            py2 = (i*97  + int(t*60))%SCREEN_HEIGHT
            pygame.draw.circle(s,(200,20,20),(px2,py2),2)
        ft = pygame.font.Font(None, 96)
        fade = min(255, self.game_over_timer*5)
        ts2 = ft.render("GAME OVER", True, RED)
        ts2.set_alpha(fade)
        s.blit(ts2,(SCREEN_WIDTH//2-ts2.get_width()//2, 160))
        fn = pygame.font.Font(None,36)
        lines = [
            f"Level reached: {self.current_level+1}",
            f"Total coins earned: {self.bank_coins}",
            f"Deaths this run: {self.total_deaths}",
            f"Max combo: x{self.max_combo}",
        ]
        for i,line in enumerate(lines):
            ls2 = fn.render(line, True, (200,150,150))
            ls2.set_alpha(fade)
            s.blit(ls2,(SCREEN_WIDTH//2-ls2.get_width()//2, 300+i*44))
        if self.game_over_timer > 60:
            fp = pygame.font.Font(None, 30)
            pulse = int(abs(math.sin(t*3))*100+155)
            ps2 = fp.render("Press SPACE to try again   ESC to menu", True,(pulse,pulse,pulse))
            s.blit(ps2,(SCREEN_WIDTH//2-ps2.get_width()//2, 520))

    def draw_exit_portal(self):
        """Animated glowing exit portal instead of flat rectangle."""
        if not hasattr(self, 'exit_rect'): return
        s = self.screen
        t = pygame.time.get_ticks() * 0.001
        ex2 = self.exit_rect.x - self.camera_x
        ey2 = self.exit_rect.y - self.camera_y
        ew = self.exit_rect.width; eh = self.exit_rect.height
        cx2 = ex2 + ew//2; cy2 = ey2 + eh//2
        # Spinning outer rings
        for ring in range(3):
            r2 = 28 + ring*10
            a2 = t * (1.5 - ring*0.4)
            col_r = int(abs(math.sin(a2+ring))*100+80)
            col_g = int(abs(math.sin(a2+ring+1))*150+80)
            pygame.draw.circle(s, (col_r, 220, col_g), (int(cx2), int(cy2)), r2, 2)
        # Inner glow
        glow = pygame.Surface((60, 90), pygame.SRCALPHA)
        pulse = int(abs(math.sin(t*2))*40+180)
        pygame.draw.rect(glow,(0, pulse, 80, 160),(0,0,60,90),0,8)
        s.blit(glow,(int(ex2)-10, int(ey2)-25))
        # Center star
        for j in range(8):
            a3 = j/8*math.pi*2 + t*2
            sx2=cx2+int(math.cos(a3)*14); sy2=cy2+int(math.sin(a3)*14)
            pygame.draw.line(s,(100,255,150),(int(cx2),int(cy2)),(sx2,sy2),1)
        # "EXIT" label
        fe=pygame.font.Font(None,20)
        es2=fe.render("EXIT",True,WHITE)
        s.blit(es2,(int(cx2)-es2.get_width()//2, int(ey2)-38))

    def draw_race(self):
        """CPU race mini-game — hold RIGHT/D to accelerate, reach the finish!"""
        s = self.screen
        t = pygame.time.get_ticks() * 0.001

        # ── Background sky + ground ──────────────────────────────────────
        for y in range(SCREEN_HEIGHT):
            p = y/SCREEN_HEIGHT
            pygame.draw.line(s,(int(80+p*40),int(120+p*60),int(200-p*60)),(0,y),(SCREEN_WIDTH,y))
        pygame.draw.rect(s,(80,160,60),(0,520,SCREEN_WIDTH,260))
        # Track
        pygame.draw.rect(s,(60,60,70),(0,460,SCREEN_WIDTH,80))
        pygame.draw.rect(s,(50,50,60),(0,462,SCREEN_WIDTH,2))
        pygame.draw.rect(s,(50,50,60),(0,536,SCREEN_WIDTH,2))
        # Dashed centre line
        for dx in range(0,SCREEN_WIDTH,60):
            pygame.draw.rect(s,(220,220,80),(dx,497,36,6))
        # Crowd in background
        for i in range(20):
            cx2 = i*60+20; cy2 = 420
            col = [(220,80,80),(80,180,80),(80,80,220),(220,180,80)][i%4]
            pygame.draw.circle(s,col,(cx2,cy2),10)
            pygame.draw.rect(s,col,(cx2-8,cy2+8,16,20))

        # ── Scroll offset (track moves with player) ───────────────────────
        cam = max(0, self.race_player_x - SCREEN_WIDTH//3)

        # ── Finish line ───────────────────────────────────────────────────
        fx = self.race_finish - cam
        if -20 < fx < SCREEN_WIDTH+20:
            for fy in range(460,540,16):
                col = WHITE if (fy//16)%2==0 else BLACK
                pygame.draw.rect(s,col,(int(fx),fy,16,16))
            ff=pygame.font.Font(None,28)
            fs2=ff.render("FINISH",True,WHITE)
            s.blit(fs2,(int(fx)-fs2.get_width()//2+8,440))

        # ── CPU runner (Red Guy) ──────────────────────────────────────────
        cpx = int(self.race_cpu_x - cam)
        if -40 < cpx < SCREEN_WIDTH+40:
            bob = math.sin(t*8)*3 if self.race_state=='racing' else 0
            # Body
            pygame.draw.rect(s,RED,(cpx,int(475+bob),22,22),0,4)
            # Eyes
            pygame.draw.circle(s,YELLOW,(cpx+16,int(480+bob)),3)
            # Legs animate
            if self.race_state=='racing':
                lp=math.sin(t*10)
                pygame.draw.rect(s,(160,30,30),(cpx+4,int(497+bob),6,8+int(lp*4)))
                pygame.draw.rect(s,(160,30,30),(cpx+12,int(497+bob),6,8-int(lp*4)))
            else:
                pygame.draw.rect(s,(160,30,30),(cpx+4,int(497+bob),6,8))
                pygame.draw.rect(s,(160,30,30),(cpx+12,int(497+bob),6,8))

        # ── Player runner (Blue Guy) ──────────────────────────────────────
        ppx = int(self.race_player_x - cam)
        bob2 = math.sin(t*10)*3 if self.race_state=='racing' else 0
        col = getattr(self,'color_equipped',BLUE)
        pygame.draw.rect(s,col,(ppx,int(475+bob2),22,22),0,4)
        pygame.draw.circle(s,WHITE,(ppx+16,int(480+bob2)),3)
        pygame.draw.circle(s,BLACK,(ppx+17,int(481+bob2)),1)
        hat=getattr(self,'hat_equipped',None)
        if hat: self._draw_hat_at(hat,ppx+2,int(471+bob2))
        if self.race_state=='racing':
            lp2=math.sin(t*12)
            pygame.draw.rect(s,tuple(max(0,c-40) for c in col),(ppx+4,int(497+bob2),6,8+int(lp2*4)))
            pygame.draw.rect(s,tuple(max(0,c-40) for c in col),(ppx+12,int(497+bob2),6,8-int(lp2*4)))
        else:
            pygame.draw.rect(s,tuple(max(0,c-40) for c in col),(ppx+4,int(497+bob2),6,8))
            pygame.draw.rect(s,tuple(max(0,c-40) for c in col),(ppx+12,int(497+bob2),6,8))
        # Speed trail
        if self.race_player_vel > 3:
            for i in range(4):
                ts2=pygame.Surface((22,22),pygame.SRCALPHA)
                ts2.fill((*col, 60-i*12))
                s.blit(ts2,(ppx-(i+1)*10,int(475+bob2)))

        # ── Progress bar ─────────────────────────────────────────────────
        pygame.draw.rect(s,(20,20,30),(40,20,SCREEN_WIDTH-80,18),0,6)
        pp2=int((SCREEN_WIDTH-84)*min(1,self.race_player_x/self.race_finish))
        cp2=int((SCREEN_WIDTH-84)*min(1,self.race_cpu_x/self.race_finish))
        pygame.draw.rect(s,col,(42,22,pp2,14),0,4)
        pygame.draw.rect(s,RED,(42,22+7,cp2,7),0,4)
        pygame.draw.rect(s,WHITE,(40,20,SCREEN_WIDTH-80,18),1,6)
        s.blit(pygame.font.Font(None,18).render("YOU",True,WHITE),(42,6))
        s.blit(pygame.font.Font(None,18).render("CPU",True,(220,80,80)),(42,36))
        # Finish flag on bar
        s.blit(pygame.font.Font(None,18).render("🏁",True,WHITE),(SCREEN_WIDTH-46,18))

        # ── Speedometer ──────────────────────────────────────────────────
        spd = int(self.race_player_vel*10)
        sf=pygame.font.Font(None,36)
        s.blit(sf.render(f"⚡ {spd} km/h",True,CYAN),(20,560))

        # ── Timer ─────────────────────────────────────────────────────────
        if self.race_state=='racing':
            self.race_timer += 1
            elapsed = self.race_timer/60
            s.blit(pygame.font.Font(None,32).render(f"⏱ {elapsed:.2f}s",True,WHITE),(SCREEN_WIDTH//2-50,560))

        # ── Countdown ────────────────────────────────────────────────────
        if self.race_state=='ready':
            self.race_countdown -= 1
            cd = self.race_countdown
            if cd > 120:
                txt="3"; col2=(220,80,80)
            elif cd > 60:
                txt="2"; col2=(220,180,80)
            elif cd > 0:
                txt="1"; col2=(80,220,80)
            else:
                txt="GO!"; col2=YELLOW
                self.race_state='racing'
            scale=max(0.3,min(1.0,1-(60-(cd%60))/80.0) if cd%60<40 else 1.0)
            fc=pygame.font.Font(None,int(160*max(0.4,scale)))
            cs3=fc.render(txt,True,col2)
            s.blit(cs3,(SCREEN_WIDTH//2-cs3.get_width()//2,SCREEN_HEIGHT//2-80))

        # ── Race logic update ─────────────────────────────────────────────
        if self.race_state=='racing':
            # Player: hold RIGHT/D to accelerate, release to decelerate
            keys=pygame.key.get_pressed()
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.race_player_vel = min(7.0, self.race_player_vel+0.18)
            else:
                self.race_player_vel = max(0.0, self.race_player_vel-0.12)
            self.race_player_x += self.race_player_vel
            # CPU: slight speed variation to make it fair/exciting
            wobble = math.sin(t*0.7)*0.4
            self.race_cpu_x += self.race_cpu_speed + wobble
            # Check finish
            player_done = self.race_player_x >= self.race_finish
            cpu_done    = self.race_cpu_x    >= self.race_finish
            if player_done and self.race_player_time==0:
                self.race_player_time = self.race_timer
            if cpu_done and self.race_cpu_time==0:
                self.race_cpu_time = self.race_timer
            if player_done or cpu_done:
                if player_done and cpu_done:
                    self.race_result = 'tie' if abs(self.race_player_time-self.race_cpu_time)<3 else ('win' if self.race_player_time<=self.race_cpu_time else 'lose')
                elif player_done:
                    self.race_result = 'win'
                else:
                    self.race_result = 'lose'
                self.race_state = 'done'
                if self.race_result=='win':
                    self.shop_coins += 15
                    if self.race_best is None or self.race_player_time < self.race_best:
                        self.race_best = self.race_player_time

        # ── Result screen ─────────────────────────────────────────────────
        if self.race_state=='done':
            overlay=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA)
            overlay.fill((0,0,0,160))
            s.blit(overlay,(0,0))
            if self.race_result=='win':
                msg="🏆 YOU WIN! +15 coins!"; col3=YELLOW
            elif self.race_result=='lose':
                msg="💨 CPU WINS!  Try again!"; col3=RED
            else:
                msg="🤝 TIE!  So close!"; col3=CYAN
            fr=pygame.font.Font(None,72)
            rs=fr.render(msg,True,col3)
            s.blit(rs,(SCREEN_WIDTH//2-rs.get_width()//2,200))
            pt=self.race_player_time/60 if self.race_player_time else self.race_timer/60
            ct=self.race_cpu_time/60 if self.race_cpu_time else self.race_timer/60
            fn2=pygame.font.Font(None,32)
            s.blit(fn2.render(f"Your time: {pt:.2f}s   CPU time: {ct:.2f}s",True,WHITE),(SCREEN_WIDTH//2-200,290))
            if self.race_best:
                s.blit(fn2.render(f"Best time: {self.race_best/60:.2f}s",True,YELLOW),(SCREEN_WIDTH//2-100,330))
            fp=pygame.font.Font(None,28)
            s.blit(fp.render("SPACE = race again   ESC = back to menu",True,(180,180,180)),(SCREEN_WIDTH//2-200,400))

        # ── Instruction banner ────────────────────────────────────────────
        if self.race_state in ('ready','racing'):
            fi=pygame.font.Font(None,26)
            s.blit(fi.render("Hold RIGHT / D  to run!",True,(200,200,100)),(SCREEN_WIDTH//2-110,590))
        if self.race_best:
            s.blit(pygame.font.Font(None,22).render(f"Best: {self.race_best/60:.2f}s",True,YELLOW),(SCREEN_WIDTH-130,560))

        # ── ESC hint ──────────────────────────────────────────────────────
        s.blit(pygame.font.Font(None,20).render("ESC = back",True,(100,100,120)),(SCREEN_WIDTH-100,SCREEN_HEIGHT-24))

    def draw_menu(self):
        t = pygame.time.get_ticks() * 0.001

        # Animated dark gradient background
        self.menu_gradient = (self.menu_gradient + 0.01) % (2 * math.pi)
        for y in range(SCREEN_HEIGHT):
            wave = math.sin(self.menu_gradient + y * 0.004) * 0.5 + 0.5
            color = (int(8 + wave * 18), int(8 + wave * 22), int(25 + wave * 45))
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))

        # Animated stars in background
        for i in range(50):
            sx = (i * 193) % SCREEN_WIDTH
            sy = (i * 137) % (SCREEN_HEIGHT // 2)
            br = int(abs(math.sin(t * 0.7 + i)) * 180 + 60)
            pygame.draw.circle(self.screen, (br, br, br), (sx, sy), 1)

        # Silhouette platforms at bottom
        for i in range(8):
            px = i * 160 - int(t * 20) % 160
            pygame.draw.rect(self.screen, (20, 25, 40), (px, SCREEN_HEIGHT - 80, 140, 80))
            pygame.draw.rect(self.screen, (20, 25, 40), (px + 160, SCREEN_HEIGHT - 50, 120, 50))

        # Floating particles
        if random.random() < 0.15:
            col = YELLOW if random.random() > 0.5 else BLUE
            self.particles.append(Particle(
                random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT,
                random.uniform(-0.8, 0.8), random.uniform(-2.5, -1),
                col, 140
            ))
        for particle in self.particles[:]:
            particle.update()
            particle.draw(self.screen)
            if particle.life <= 0:
                self.particles.remove(particle)

        # Animated Blue Guy on menu
        bounce = math.sin(t * 2.5) * 8
        bx, by = SCREEN_WIDTH // 2 - 15, 290 + bounce
        # cape
        pygame.draw.polygon(self.screen, (30, 60, 160),
            [(bx - 8, by + 5), (bx - 22, by + 32), (bx + 5, by + 28)])
        pygame.draw.rect(self.screen, BLUE, (bx, by, 30, 30))
        pygame.draw.circle(self.screen, WHITE, (bx + 21, by + 10), 4)
        pygame.draw.circle(self.screen, BLACK, (bx + 22, by + 11), 2)

        # Big title with glow layers
        for glow_size in [76, 74, 72]:
            font_title = pygame.font.Font(None, glow_size)
            glow_surf = font_title.render("MINIMAL PLATFORMER 4", True,
                (0, 0, int(60 + math.sin(t) * 40)))
            self.screen.blit(glow_surf, (SCREEN_WIDTH // 2 - glow_surf.get_width() // 2 + (76 - glow_size) // 2,
                                         100 + (76 - glow_size) // 2))
        font_title = pygame.font.Font(None, 72)
        title_surf = font_title.render("MINIMAL PLATFORMER 4", True, WHITE)
        self.screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 100))

        font_sub = pygame.font.Font(None, 42)
        r_pulse = int(200 + math.sin(t * 1.5) * 55)
        sub_surf = font_sub.render("T H E   R E D   U P R I S I N G", True, (r_pulse, 40, 40))
        self.screen.blit(sub_surf, (SCREEN_WIDTH // 2 - sub_surf.get_width() // 2, 180))

        # Menu options with highlighted box
        options = [
            "▶  START GAME",
            f"◀  LEVEL: {self.start_level}  ▶",
            "✕   QUIT"
        ]
        world_hint = ""
        if self.selected_option == 1 and self.start_level != 'T':
            world_hint = "🌲 WOODS WORLD" if isinstance(self.start_level, int) and self.start_level > 15 else "⭐ NORMAL WORLD"

        font_opt = pygame.font.Font(None, 50)
        font_hint = pygame.font.Font(None, 26)
        for i, option in enumerate(options):
            is_sel = (i == self.selected_option)
            y_pos = 360 + i * 80

            if is_sel:
                # Glowing selection box
                box_w = 420; box_h = 52
                box_x = SCREEN_WIDTH // 2 - box_w // 2
                glow_alpha = int(abs(math.sin(t * 3)) * 60 + 40)
                box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
                box_surf.fill((60, 80, 180, glow_alpha))
                self.screen.blit(box_surf, (box_x, y_pos - 8))
                pygame.draw.rect(self.screen, (100, 130, 255), (box_x, y_pos - 8, box_w, box_h), 2)
                col = YELLOW
                size = 52
            else:
                col = (160, 160, 180)
                size = 44

            font_opt = pygame.font.Font(None, size)
            text_surf = font_opt.render(option, True, col)
            self.screen.blit(text_surf, (SCREEN_WIDTH // 2 - text_surf.get_width() // 2, y_pos))

        # World hint below level selector
        if world_hint:
            hint_surf = font_hint.render(world_hint, True, GREEN if "WOODS" in world_hint else CYAN)
            self.screen.blit(hint_surf, (SCREEN_WIDTH // 2 - hint_surf.get_width() // 2, 445))

        # Controls at bottom
        font_ctrl = pygame.font.Font(None, 26)
        ctrl_text = "UP/DOWN: Select   ENTER: Confirm   LEFT/RIGHT: Change Level"

        # ── Player stats sidebar on menu ──────────────────────────────────
        sx = 40; sy = 220
        pygame.draw.rect(self.screen,(10,10,30,0),(sx-6,sy-6,230,280),0,8)
        pygame.draw.rect(self.screen,(50,50,80),(sx-6,sy-6,230,280),1,8)
        fn2 = pygame.font.Font(None, 22)
        stat_lines = [
            ("📊 YOUR STATS", CYAN),
            (f"Levels beaten: {len(self.levels_beaten)}/30", WHITE),
            (f"Stickers: {len(self.stickers_found)}/30", YELLOW),
            (f"Coins total: {self.bank_coins}", YELLOW),
            (f"Deaths: {self.total_deaths}", (200,100,100)),
            (f"Max combo: x{self.max_combo}", ORANGE),
            (f"Achievements: {len(self.achievements_earned)}/{len(self.ACHIEVEMENTS)}", GREEN),
            (f"High score: {self.high_score} coins", (200,200,100)),
        ]
        for i,(text,col2) in enumerate(stat_lines):
            ss2 = fn2.render(text, True, col2)
            self.screen.blit(ss2,(sx, sy + i*30))

        # ── Tips ticker at bottom ──────────────────────────────────────────
        tips = [
            "TIP: Press J for Blue Guy's journal!",
            "TIP: Type 'coins' on the menu for +100 coins!",
            "TIP: Dash with SHIFT for brief invincibility!",
            "TIP: Kill enemies in a row for combo bonuses!",
            "TIP: Collect all 30 stickers for a secret!",
            "TIP: Press A to see all achievements!",
            "TIP: Visit Blue Guy's house for mini-games!",
            "TIP: ShieldEnemies (blue) need 2 hits!",
            "TIP: FastEnemies (orange) move at 2x speed!",
            "TIP: Gems are worth 5 coins each!",
            "TIP: F5 saves your progress anytime!",
            "TIP: Daily challenge resets every day!",
        ]
        tip_idx = int(t * 0.15) % len(tips)
        tip_off = (t * 0.15 - int(t * 0.15))
        tp = pygame.font.Font(None, 22)
        tip_s = tp.render(tips[tip_idx], True, (120,120,160))
        tip_s.set_alpha(int(min(255, min(tip_off, 1-tip_off)*8*255)))
        self.screen.blit(tip_s,(SCREEN_WIDTH//2-tip_s.get_width()//2, SCREEN_HEIGHT-90))
        ctrl_surf = font_ctrl.render(ctrl_text, True, (100, 100, 120))
        self.screen.blit(ctrl_surf, (SCREEN_WIDTH // 2 - ctrl_surf.get_width() // 2, SCREEN_HEIGHT - 38))

        # Version tag
        ver_surf = font_ctrl.render("By Kyle & Claude  |  F5=Save  A=Achievements  J=Journal  C=Credits  |  CTRL=Shoot  SPACE=Jump  SHIFT=Dash", True, (70, 70, 90))
        self.screen.blit(ver_surf, (SCREEN_WIDTH // 2 - ver_surf.get_width() // 2, SCREEN_HEIGHT - 64))

        # Save notification
        if self.save_notif > 0:
            a = min(255, self.save_notif * 4)
            sf2 = pygame.font.Font(None, 38)
            ss = sf2.render("💾 SAVED!", True, GREEN)
            ss.set_alpha(a)
            self.screen.blit(ss, (SCREEN_WIDTH//2 - ss.get_width()//2, SCREEN_HEIGHT - 110))
    
    def get_save_path(self):
        """Save file lives next to the game .py file."""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'savefile.json')

    def save_game(self):
        data = {
            'bank_coins':      self.bank_coins,
            'shop_coins':      self.shop_coins,
            'levels_beaten':   list(self.levels_beaten),
            'stickers_found':  list(self.stickers_found),
            'best_times':      {str(k): v for k, v in self.best_times.items()},
            'max_combo':       self.max_combo,
            'clicker_clicks':  self.clicker_clicks,
            'clicker_cps':     self.clicker_cps,
            'clicker_upgrades':self.clicker_upgrades,
            'hat_equipped':    self.hat_equipped,
            'color_equipped':  list(self.color_equipped),
            'hats_owned':      list(self.hats_owned),
            'colors_owned':    [list(c) for c in self.colors_owned],
            'current_level':   self.current_level,
            'cutscenes_seen':  list(self.cutscenes_seen),
            'tv_on':           self.tv_on,
            'tv_channel':      self.tv_channel,
            'achievements':    list(self.achievements_earned),
            'total_deaths':    self.total_deaths,
            'daily_completed': self.daily_completed,
            'daily_seed':      self.daily_seed,
            'high_score':      self.high_score,
            'runs_completed':  self.runs_completed,
        }
        try:
            with open(self.get_save_path(), 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Save failed: {e}")
            return False

    def load_game(self):
        path = self.get_save_path()
        if not os.path.exists(path):
            return False
        try:
            with open(path) as f:
                data = json.load(f)
            self.bank_coins       = data.get('bank_coins', 0)
            self.shop_coins       = data.get('shop_coins', 0)
            self.levels_beaten    = set(data.get('levels_beaten', []))
            self.stickers_found   = set(data.get('stickers_found', []))
            self.best_times       = {int(k): v for k, v in data.get('best_times', {}).items()}
            self.max_combo        = data.get('max_combo', 0)
            self.clicker_clicks   = data.get('clicker_clicks', 0)
            self.clicker_cps      = data.get('clicker_cps', 0)
            self.clicker_upgrades = data.get('clicker_upgrades', {})
            self.hat_equipped     = data.get('hat_equipped', None)
            col                   = data.get('color_equipped', list(BLUE))
            self.color_equipped   = tuple(col)
            self.hats_owned       = set(data.get('hats_owned', []))
            self.colors_owned     = {tuple(c) for c in data.get('colors_owned', [list(BLUE)])}
            self.current_level    = data.get('current_level', 0)
            self.cutscenes_seen   = set(data.get('cutscenes_seen', []))
            self.tv_on            = data.get('tv_on', False)
            self.tv_channel       = data.get('tv_channel', 0)
            self.achievements_earned = set(data.get('achievements', []))
            self.total_deaths     = data.get('total_deaths', 0)
            # Only restore daily if same day
            if data.get('daily_seed') == self.daily_seed:
                self.daily_completed = data.get('daily_completed', False)
            self.high_score      = data.get('high_score', 0)
            self.runs_completed  = data.get('runs_completed', 0)
            print(f"✅ Save loaded! Level {self.current_level+1}, {len(self.levels_beaten)} levels beaten")
            return True
        except Exception as e:
            print(f"❌ Load failed: {e}")
            return False

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.state in ['playing', 'tutorial']:
                        if self.game_over:
                            # Restart from same level
                            self.game_over = False; self.game_over_timer = 0
                            self.player_health = self.player_max_health
                            self.load_level(self.current_level)
                        elif not self.paused:
                            self.player.jump()
                            if 'jump' in self.sfx:
                                try: self.sfx['jump'].play()
                                except: pass
                    elif event.key == pygame.K_p and self.state in ['playing','tutorial']:
                        if not self.game_over:
                            self.paused = not self.paused
                            self.pause_option = 0
                    elif event.key == pygame.K_ESCAPE:
                        if self.state in ['playing', 'tutorial']:
                            if self.journal_open:
                                self.journal_open = False
                            elif self.paused:
                                self.paused = False
                            else:
                                self.state = 'intro'
                                self.intro_timer = 0
                                self.particles = []
                                self.paused = False
                        elif self.state == 'menu':
                            if getattr(self, 'shop_open', False):
                                self.shop_open = False
                            elif getattr(self, 'map_open', False):
                                self.map_open = False
                            elif getattr(self, 'house_open', False):
                                self.house_open = False
                            elif getattr(self, 'race_open', False):
                                self.race_open = False
                            elif getattr(self, 'achievements_open', False):
                                self.achievements_open = False
                            elif getattr(self, 'journal_open', False):
                                self.journal_open = False
                            elif getattr(self, 'credits_open', False):
                                self.credits_open = False
                            else:
                                running = False
                        elif self.game_completed:
                            # Return to menu from win screen - DON'T quit!
                            self.game_completed = False
                            self.state = 'menu'
                        else:
                            running = False
                    elif self.state == 'menu':
                        # Shop gets first priority when open
                        if self.shop_open and event.key == pygame.K_TAB:
                            self.shop_tab = (self.shop_tab + 1) % 3
                        elif self.shop_open and event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                            num = {pygame.K_1:0, pygame.K_2:1, pygame.K_3:2, pygame.K_4:3, pygame.K_5:4}[event.key]
                            if self.shop_tab == 0:
                                upg = [('auto',20),('eyes',15),('cape',25),('shoes',40),('hat',60)]
                                if num < len(upg):
                                    key2, cost = upg[num]
                                    if self.shop_coins >= cost and not self.clicker_upgrades.get(key2):
                                        self.shop_coins -= cost; self.shop_spent += cost
                                        self.clicker_upgrades[key2] = 1
                                        self.clicker_cps = sum([
                                            1 if self.clicker_upgrades.get('auto') else 0,
                                            1 if self.clicker_upgrades.get('cape') else 0,
                                            2 if self.clicker_upgrades.get('shoes') else 0,
                                        ])
                            elif self.shop_tab == 1:
                                if num < len(self.HATS):
                                    hat = self.HATS[num]
                                    if hat['key'] in self.hats_owned:
                                        self.hat_equipped = hat['key']
                                    elif self.shop_coins >= hat['cost']:
                                        self.shop_coins -= hat['cost']; self.shop_spent += hat['cost']
                                        self.hats_owned.add(hat['key'])
                                        self.hat_equipped = hat['key']
                            elif self.shop_tab == 2:
                                skins = self.SKINS if hasattr(self,'SKINS') else []
                                if num < len(skins):
                                    skin = skins[num]
                                    if skin['col'] in self.colors_owned:
                                        self.color_equipped = skin['col']
                                    elif self.shop_coins >= skin['cost']:
                                        self.shop_coins -= skin['cost']; self.shop_spent += skin['cost']
                                        self.colors_owned.add(skin['col'])
                                        self.color_equipped = skin['col']
                        elif event.key == pygame.K_UP:
                            self.selected_option = (self.selected_option - 1) % 3
                        elif event.key == pygame.K_DOWN:
                            self.selected_option = (self.selected_option + 1) % 3
                        elif event.key == pygame.K_LEFT and self.selected_option == 1:
                            if self.start_level == 'T':
                                self.start_level = 30  # 30 LEVELS!
                            elif self.start_level == 1:
                                self.start_level = 'T'
                            else:
                                self.start_level -= 1
                        elif event.key == pygame.K_RIGHT and self.selected_option == 1:
                            if self.start_level == 'T':
                                self.start_level = 1
                            elif self.start_level == 30:  # 30 LEVELS!
                                self.start_level = 'T'
                            else:
                                self.start_level += 1
                        elif event.key == pygame.K_RETURN:
                            if self.selected_option == 0:  # Start Game
                                self.current_level = 0
                                self.load_level(self.current_level)
                                self.state = 'playing'
                                self.game_completed = False
                                self.particles = []
                                self.session_started_level = 0  # track for 1 Sitting
                            elif self.selected_option == 1:  # Start Level
                                if self.start_level == 'T':
                                    self.tutorial_step = 0
                                    self.load_tutorial_level()
                                    self.state = 'tutorial'
                                    self.particles = []
                                    self.session_started_level = None
                                else:
                                    self.current_level = self.start_level - 1
                                    self.load_level(self.current_level)
                                    self.state = 'playing'
                                    self.game_completed = False
                                    self.particles = []
                                    self.session_started_level = None  # not a fresh run
                            elif self.selected_option == 2:  # Exit
                                running = False
                        # Shop/map shortcuts in menu
                        elif event.key == pygame.K_s:
                            self.shop_open = not self.shop_open
                            self.map_open  = False
                        elif event.key == pygame.K_m:
                            self.map_open  = not self.map_open
                            self.shop_open = False
                        elif event.key == pygame.K_F5:
                            if self.save_game(): self.save_notif = 150
                        elif event.key == pygame.K_a and not self.shop_open and not self.map_open and not self.house_open:
                            self.achievements_open = not getattr(self, 'achievements_open', False)
                        elif event.key == pygame.K_j and not self.shop_open and not self.map_open and not self.house_open:
                            self.journal_open = not self.journal_open
                        elif event.key == pygame.K_c and not self.shop_open and not self.map_open and not self.house_open:
                            self.credits_open = not self.credits_open
                            if self.credits_open: self.credits_scroll = 0
                        # Race key handling
                        elif self.race_open:
                            if event.key == pygame.K_SPACE and self.race_state == 'done':
                                self.race_state = 'ready'
                                self.race_countdown = 180
                                self.race_player_x = 60.0
                                self.race_cpu_x = 60.0
                                self.race_timer = 0
                                self.race_player_time = 0
                                self.race_cpu_time = 0
                                self.race_result = None
                                self.race_player_vel = 0.0
                            elif event.key == pygame.K_ESCAPE:
                                self.race_open = False
                        # Mini-game key handling
                        elif self.minigame_active == 'shell' and self.shell_phase == 'hide':
                            pick = None
                            if event.key == pygame.K_1: pick = 0
                            elif event.key == pygame.K_2: pick = 1
                            elif event.key == pygame.K_3: pick = 2
                            if pick is not None:
                                self.shell_phase = 'result'
                                if pick == self.shell_ball:
                                    self.shell_result = 'win'
                                    self.shop_coins += 15
                                else:
                                    self.shell_result = 'lose'
                        elif self.minigame_active == 'shell' and self.shell_phase == 'result':
                            if event.key == pygame.K_SPACE:
                                if self.shop_coins >= 5:
                                    self.shop_coins -= 5; self.shop_spent += 5
                                    self.shell_phase = 'hide'
                                    self.shell_ball = random.randint(0,2)
                                    self.shell_result = None
                            elif event.key == pygame.K_ESCAPE:
                                self.minigame_active = None
                        elif self.minigame_active == 'guess':
                            if event.key == pygame.K_ESCAPE:
                                self.minigame_active = None
                            elif event.key == pygame.K_BACKSPACE:
                                self.guess_input = self.guess_input[:-1]
                            elif event.key == pygame.K_RETURN and self.guess_input:
                                try:
                                    n = int(self.guess_input)
                                    if n == self.guess_target:
                                        self.guess_result = 'win'
                                        self.shop_coins += 20
                                    elif self.guess_attempts > 1:
                                        self.guess_result = 'too_high' if n > self.guess_target else 'too_low'
                                        self.guess_attempts -= 1
                                    else:
                                        self.guess_result = 'lose'
                                        self.guess_attempts = 0
                                    self.guess_input = ''
                                except ValueError:
                                    self.guess_input = ''
                            elif event.unicode.isdigit() and len(self.guess_input) < 2:
                                self.guess_input += event.unicode
                        elif event.key == pygame.K_ESCAPE:
                            if self.shop_open: self.shop_open = False
                            elif self.map_open: self.map_open  = False
                            elif self.house_open: self.house_open = False
                            else: running = False
                        elif self.shop_open:
                            if event.key == pygame.K_TAB:
                                self.shop_tab = (self.shop_tab + 1) % 3
                            # Number keys to buy in shop
                            num = None
                            if event.key == pygame.K_1: num = 0
                            elif event.key == pygame.K_2: num = 1
                            elif event.key == pygame.K_3: num = 2
                            elif event.key == pygame.K_4: num = 3
                            elif event.key == pygame.K_5: num = 4
                            if num is not None:
                                if self.shop_tab == 0:
                                    upg = [('auto',20),('eyes',15),('cape',25),('shoes',40),('hat',60)]
                                    if num < len(upg):
                                        key, cost = upg[num]
                                        if self.shop_coins >= cost:
                                            self.shop_coins -= cost
                                            self.clicker_upgrades[key] = self.clicker_upgrades.get(key,0)+1
                                            if key == 'auto': self.clicker_cps += 1
                                            elif key == 'cape': self.clicker_cps += 1
                                            elif key == 'shoes': self.clicker_cps += 2
                                elif self.shop_tab == 1:
                                    if num < len(self.HATS):
                                        hat = self.HATS[num]
                                        if hat['key'] in self.hats_owned:
                                            self.hat_equipped = None if self.hat_equipped==hat['key'] else hat['key']
                                        elif self.shop_coins >= hat['cost']:
                                            self.shop_coins -= hat['cost']
                                            self.hats_owned.add(hat['key'])
                                            self.hat_equipped = hat['key']
                                elif self.shop_tab == 2:
                                    if num < len(self.COLORS):
                                        skin = self.COLORS[num]
                                        if skin['col'] in self.colors_owned:
                                            self.color_equipped = skin['col']
                                        elif self.shop_coins >= skin['cost']:
                                            self.shop_coins -= skin['cost']
                                            self.colors_owned.add(skin['col'])
                                            self.color_equipped = skin['col']
                        # Cheat code handler - catches any key not handled above
                        if self.state == 'menu' and not self.shop_open:
                            self.handle_cheat_codes(event.key)

                # MOUSEBUTTONDOWN - clicker and buttons (inside the SAME event loop!)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == 'menu':
                        mx, my = event.pos
                        if self.house_open:
                            # House room tabs
                            for rid in ['living','bedroom','kitchen','garden']:
                                tab=getattr(self,f'_house_tab_{rid}',None)
                                if tab and tab.collidepoint(mx,my):
                                    self.house_room=rid
                                    self.minigame_active=None
                            # TV click
                            if self.house_room=='living':
                                tv=getattr(self,'_tv_rect',None)
                                if tv and tv.collidepoint(mx,my):
                                    if not self.tv_on:
                                        self.tv_on=True
                                    else:
                                        self.tv_channel+=1
                                    self.tv_channels_seen.add(self.tv_channel % 4)
                            # Mini-game buttons in kitchen
                            if self.house_room=='kitchen' and not self.minigame_active:
                                if getattr(self,'_mg1_rect',None) and self._mg1_rect.collidepoint(mx,my):
                                    if self.shop_coins>=5:
                                        self.shop_coins-=5; self.shop_spent+=5
                                        self.shell_phase='hide'; self.shell_ball=random.randint(0,2)
                                        self.shell_result=None; self.minigame_active='shell'
                                elif getattr(self,'_mg2_rect',None) and self._mg2_rect.collidepoint(mx,my):
                                    self.guess_target=random.randint(1,10)
                                    self.guess_attempts=3; self.guess_input=''
                                    self.guess_result=None; self.minigame_active='guess'
                            # Shell game picks
                            if self.minigame_active=='shell' and self.shell_phase=='hide':
                                pass  # handled by keydown
                        elif not getattr(self,'shop_open',False) and not getattr(self,'map_open',False):
                            big_guy = getattr(self, '_big_guy_rect', None)
                            shop_b  = getattr(self, '_shop_btn_rect', None)
                            map_b   = getattr(self, '_map_btn_rect', None)
                            house_b = getattr(self, '_house_btn_rect', None)
                            if big_guy and big_guy.collidepoint(mx, my):
                                mult = 2 if self.clicker_upgrades.get('hat',0) > 0 else 1
                                self.shop_coins   += mult
                                self.bank_coins   += mult
                                self.clicker_clicks += 1
                                self.clicker_anim  = 1.0
                            elif shop_b and shop_b.collidepoint(mx, my):
                                self.shop_open = True
                            elif map_b and map_b.collidepoint(mx, my):
                                self.map_open = True
                            elif house_b and house_b.collidepoint(mx, my):
                                self.house_open = True
                                self._house_visited = True
                            else:
                                race_b = getattr(self,'_race_btn_rect',None)
                                if race_b and race_b.collidepoint(mx, my):
                                    self.race_open = True
                                    self.race_state = 'ready'
                                    self.race_countdown = 180
                                    self.race_player_x = 60.0
                                    self.race_cpu_x = 60.0
                                    self.race_timer = 0
                                    self.race_player_time = 0
                                    self.race_cpu_time = 0
                                    self.race_result = None
                                    self.race_player_vel = 0.0
            
            if self.state == 'intro':
                # Play cutscene music based on intro scene - use flags not exact frames!
                if self.intro_timer == 0:
                    pygame.mixer.stop()
                    self.current_music = None
                    # Play cutscene 1 audio RIGHT when intro starts!
                    if self.cutscene1_music:
                        self.cutscene1_music.play()
                        self.current_music = 'cutscene1'
                
                if self.intro_timer == 120 and self.cutscene2_music:
                    pygame.mixer.stop()
                    self.cutscene2_music.play()
                    self.current_music = 'cutscene2'
                elif self.intro_timer == 240 and self.cutscene3_music:
                    pygame.mixer.stop()
                    self.cutscene3_music.play()
                    self.current_music = 'cutscene3'
                
                self.intro_timer += 1
                self.draw_intro()
                if self.intro_timer > 360:  # Extended for epic story!
                    self.state = 'menu'
                    self.intro_timer = 0
                    self.particles = []
                    # Stop cutscene music, start menu music
                    pygame.mixer.stop()
                    if self.menu_music and self.current_music != 'menu':
                        self.menu_music.play(loops=-1)  # Loop forever!
                        self.current_music = 'menu'
            
            elif self.state == 'menu':
                # Play menu music if not already playing
                if self.menu_music and self.current_music != 'menu':
                    pygame.mixer.stop()
                    self.menu_music.play(loops=-1)
                    self.current_music = 'menu'
                self.draw_menu()
                self.draw_daily_challenge()
                self.draw_clicker()
                if self.race_open:
                    self.draw_race()
                elif self.house_open:
                    self.draw_house()
                    if self.minigame_active:
                        self.draw_minigame()
                elif self.map_open:
                    self.draw_world_map()
                elif self.shop_open:
                    self.draw_shop()
                elif getattr(self, 'achievements_open', False):
                    self.draw_achievements_screen()
                elif self.journal_open:
                    self.draw_journal()
                elif self.credits_open:
                    self.credits_scroll += 0  # scrolled inside draw_credits
                    s_backup = self.screen
                    self.screen.fill(BLACK)
                    self.draw_credits()
                self.draw_achievement_popups()
                self.check_achievements()
            
            elif self.state == 'cutscene':
                # Handle cutscenes!
                self.cutscene_timer += 1
                self.draw_cutscene()
                
                # Press SPACE to continue after 120 frames (2 seconds)
                keys = pygame.key.get_pressed()
                if self.cutscene_timer > 120 and keys[pygame.K_SPACE]:
                    # Go to the level that was queued when cutscene started
                    next_lv = getattr(self, 'cutscene_next_level', self.current_level + 1)
                    if next_lv < len(self.levels):
                        self.current_level = next_lv
                        self.load_level(self.current_level)
                        self.state = 'playing'
                        self.game_completed = False  # make sure not set mid-game!
                        pygame.mixer.stop()
                        if self.menu_music:
                            self.menu_music.play(loops=-1)
                            self.current_music = 'menu'
                    else:
                        # Only truly done if we've beaten ALL 30 levels
                        self.game_completed = True
                        self.state = 'menu'
            
            elif self.state in ['playing', 'tutorial']:
                # Keep menu music playing during gameplay (it's also gameplay music!)
                if self.menu_music and self.current_music != 'menu':
                    pygame.mixer.stop()
                    self.menu_music.play(loops=-1)
                    self.current_music = 'menu'

                # ── DASH (SHIFT key) ──────────────────────────────────────
                if not self.paused and not self.game_over:
                    self.dash_cd = max(0, self.dash_cd - 1)
                    # Decay invincibility frames
                    if self.invincibility_frames > 0:
                        self.invincibility_frames -= 1
                        # Flash player when invincible after hit
                        if self.invincibility_frames % 8 < 4:
                            self.player.invincible = 4
                self.dash_timer = max(0, self.dash_timer - 1)
                dash_keys = pygame.key.get_pressed()
                if (dash_keys[pygame.K_LSHIFT] or dash_keys[pygame.K_RSHIFT]) and self.dash_cd == 0:
                    self.dash_cd = 40
                    self.dash_timer = 8
                    self.dash_dir = -1 if (dash_keys[pygame.K_LEFT] or dash_keys[pygame.K_a]) else 1
                    self.player.vel_x = self.dash_dir * 16
                    self.player.invincible = max(self.player.invincible, 8)
                    for _ in range(6):
                        self.particles.append(Particle(
                            self.player.x + 10, self.player.y + 10,
                            -self.dash_dir * random.uniform(2, 5), random.uniform(-1, 1),
                            CYAN, 15))

                # ── COMBO DECAY ───────────────────────────────────────────
                if self.combo_timer > 0:
                    self.combo_timer -= 1
                    if self.combo_timer == 0:
                        self.combo = 0

                # ── COIN MAGNET DECAY ─────────────────────────────────────
                self.coin_magnet = max(0, self.coin_magnet - 1)

                # ── LEVEL TIMER ───────────────────────────────────────────
                if self.state == 'playing':
                    self.level_timer += 1

                # ── SCREEN SHAKE ──────────────────────────────────────────
                if self.shake_timer > 0:
                    self.shake_timer -= 1

                # ── FLOATY TEXT UPDATE ────────────────────────────────────
                for ft in self.floaty_texts[:]:
                    ft['y'] += ft['vy']
                    ft['life'] -= 1
                    if ft['life'] <= 0:
                        self.floaty_texts.remove(ft)

                if not self.paused and not self.game_over:
                 self.player.update(self.platforms, self.projectiles)
                
                 # Update moving platforms!
                 for moving_plat in getattr(self, 'moving_platforms', []):
                    moving_plat.update()
                    self.platforms = self.levels[self.current_level if self.state == 'playing' else 0]['platforms'] + getattr(self, 'moving_platforms', [])
                
                 for enemy in self.enemies:
                    enemy.update(self.platforms)
                 if self.boss:
                    self.boss.update(self.platforms, self.player, self.projectiles)
                
                 if getattr(self, 'flying_boss', None):
                    self.flying_boss.update(self.player)
                
                for projectile in self.projectiles[:]:
                    projectile.update()
                    if not (0 <= projectile.x <= 3000 and 0 <= projectile.y <= 1000):
                        self.projectiles.remove(projectile)
                        continue
                    
                    if projectile.is_player_bullet:
                        for enemy in self.enemies[:]:
                            if projectile.rect.colliderect(enemy.rect):
                                # ShieldEnemy takes 2 hits!
                                if isinstance(enemy, ShieldEnemy):
                                    enemy.health -= 1
                                    enemy.hit_flash = 10
                                    if projectile in self.projectiles:
                                        self.projectiles.remove(projectile)
                                    if enemy.health <= 0:
                                        self.enemies.remove(enemy)
                                    else:
                                        break
                                else:
                                    self.enemies.remove(enemy)
                                    if projectile in self.projectiles:
                                        self.projectiles.remove(projectile)
                                self.session_kills += 1
                                self.unlock_achievement('first_blood')
                                # Death sparks!
                                for _ in range(12):
                                    self.particles.append(Particle(
                                        enemy.x+10, enemy.y+10,
                                        random.uniform(-4,4), random.uniform(-4,0),
                                        (255,100,50), 20))
                                # COMBO SYSTEM!
                                self.combo += 1
                                self.combo_timer = 120
                                self.max_combo = max(self.max_combo, self.combo)
                                bonus = self.combo * 2
                                self.shop_coins += bonus
                                self.bank_coins += bonus
                                # Floaty combo text!
                                label = f"+{bonus}" if self.combo < 3 else f"x{self.combo} COMBO! +{bonus}"
                                col = YELLOW if self.combo < 3 else (ORANGE if self.combo < 6 else RED)
                                self.floaty_texts.append({'x': enemy.x, 'y': enemy.y,
                                    'vy': -2, 'text': label, 'col': col, 'life': 50, 'maxlife': 50})
                                # Screen shake on big combos
                                if self.combo >= 3:
                                    self.shake_timer = 8
                                    self.shake_intensity = min(self.combo, 8)
                                # Epic particles!
                                for _ in range(10):
                                    self.particles.append(Particle(
                                        enemy.x + enemy.width // 2, enemy.y + enemy.height // 2,
                                        random.uniform(-4, 4), random.uniform(-4, 4),
                                        RED, 30
                                    ))
                                break
                        # Check boss hits
                        if self.boss and projectile.rect.colliderect(self.boss.rect):
                            self.boss.health -= 1
                            self.shake_timer = 6; self.shake_intensity = 4
                            self.floaty_texts.append({'x': self.boss.x+25, 'y': self.boss.y,
                                'vy': -2, 'text': f'-1 HP ({self.boss.health} left)', 'col': RED, 'life': 45, 'maxlife': 45})
                            if projectile in self.projectiles:
                                self.projectiles.remove(projectile)
                            if self.boss.health <= 0:
                                self.boss = None
                                self.boss_defeated = True
                                self.shake_timer = 25; self.shake_intensity = 10
                                self.floaty_texts.append({'x': SCREEN_WIDTH//2-60, 'y': 300,
                                    'vy': -1, 'text': 'BOSS DOWN!!!', 'col': GREEN, 'life': 120, 'maxlife': 120})
                                for _ in range(20):
                                    self.particles.append(Particle(
                                        self.player.x + 10, self.player.y + 10,
                                        random.uniform(-4, 4), random.uniform(-4, 4),
                                        RED if random.random() > 0.5 else YELLOW, 50
                                    ))
                        # Check flying boss hits
                        if getattr(self, 'flying_boss', None) and projectile.rect.colliderect(self.flying_boss.rect):
                            self.flying_boss.health -= 1
                            if projectile in self.projectiles:
                                self.projectiles.remove(projectile)
                            for _ in range(5):
                                self.particles.append(Particle(
                                    self.flying_boss.x + 30, self.flying_boss.y + 30,
                                    random.uniform(-2, 2), random.uniform(-2, 2),
                                    RED, 20
                                ))
                            if self.flying_boss.health <= 0:
                                self.flying_boss = None
                    # Enemy bullets hit player
                    elif projectile.rect.colliderect(self.player.rect):
                        if not getattr(self.player, 'invincible', 0) and self.invincibility_frames <= 0:
                            self.player_health -= 1
                            self.level_no_death = False
                            self.invincibility_frames = 90  # 1.5 sec invincible after hit
                            try: self.sfx.get('hit',None) and self.sfx['hit'].play()
                            except: pass
                            # Shake
                            self.shake_timer = 12; self.shake_intensity = 5
                            if self.player_health <= 0:
                                self.player_health = 0
                                self.total_deaths += 1
                                self.game_over = True
                                self.game_over_timer = 0
                                try: self.sfx.get('death',None) and self.sfx['death'].play()
                                except: pass
                            else:
                                # Respawn at start, keep health
                                self.player.x, self.player.y = self.levels[self.current_level]['spawn'] if self.state == 'playing' else self.tutorial_level['spawn']
                                self.player.vel_x = 0; self.player.vel_y = 0
                                self.total_deaths += 1
                        if projectile in self.projectiles:
                            self.projectiles.remove(projectile)
                
                for coin in self.coins:
                    if not coin.collected:
                        # Coin magnet - coins fly toward player!
                        if self.coin_magnet > 0:
                            dx = self.player.x - coin.x
                            dy = self.player.y - coin.y
                            dist = max(1, math.sqrt(dx*dx+dy*dy))
                            if dist < 250:
                                coin.x += dx/dist * 8
                                coin.y += dy/dist * 8
                                coin.rect.x = int(coin.x)
                                coin.rect.y = int(coin.y)
                        if self.player.rect.colliderect(coin.rect):
                            coin.collected = True
                            self.coins_collected += 1
                            self.bank_coins  += 1
                            self.shop_coins  += 1
                            self.clicker_coins += 1
                            self.run_coins   += 1
                            try: self.sfx.get('coin') and self.sfx['coin'].play()
                            except: pass

                # Sticker collection (hidden sparkle in each level)!
                if self.current_level not in self.stickers_found:
                    if hasattr(self, '_sticker_rect') and self.player.rect.colliderect(self._sticker_rect):
                        self.stickers_found.add(self.current_level)
                        self.shop_coins += 5  # bonus coins for sticker!
                
                # Power-up collection!
                for power_up in getattr(self, 'power_ups', []):
                    if not power_up.collected and self.player.rect.colliderect(power_up.rect):
                        power_up.collected = True
                        try: self.sfx.get('powerup') and self.sfx['powerup'].play()
                        except: pass
                        # Apply power-up effect!
                        if power_up.power_type == 'speed':
                            self.player.speed_boost = 300
                        elif power_up.power_type == 'invincible':
                            self.player.invincible = 300
                        elif power_up.power_type == 'mega_jump':
                            self.player.mega_jump = 300
                        elif power_up.power_type == 'magnet':
                            self.coin_magnet = 300  # 5 seconds coin magnet!
                        # Epic particles!
                        for _ in range(20):
                            self.particles.append(Particle(
                                power_up.x + 12, power_up.y + 12,
                                random.uniform(-4, 4), random.uniform(-4, 4),
                                power_up.colors[power_up.power_type], 40
                            ))
                
                for spike in self.spikes:
                    if self.player.rect.colliderect(spike.rect):
                        self.player.x, self.player.y = self.levels[self.current_level]['spawn'] if self.state == 'playing' else self.tutorial_level['spawn']
                        self.player.vel_x = 0
                        self.player.vel_y = 0
                for enemy in self.enemies:
                    if self.player.rect.colliderect(enemy.rect):
                        self.player.x, self.player.y = self.levels[self.current_level]['spawn'] if self.state == 'playing' else self.tutorial_level['spawn']
                        self.player.vel_x = 0
                        self.player.vel_y = 0
                if self.boss and self.player.rect.colliderect(self.boss.rect):
                    if self.player.vel_y > 0 and self.player.rect.bottom <= self.boss.rect.top + 10:
                        self.boss.health -= 1
                        self.player.vel_y = JUMP_STRENGTH
                        if self.boss.health <= 0:
                            self.boss = None
                            self.boss_defeated = True
                            if self.current_level == 29:
                                self.unlock_achievement('wowy')
                        self.player.x, self.player.y = self.levels[self.current_level]['spawn']
                        self.player.vel_x = 0
                        self.player.vel_y = 0
                
                # Flying boss collision - JUMP ON RED GUY!
                if getattr(self, 'flying_boss', None) and self.player.rect.colliderect(self.flying_boss.rect):
                    if self.player.vel_y > 0 and self.player.rect.bottom <= self.flying_boss.rect.top + 15:
                        self.flying_boss.health -= 1
                        self.player.vel_y = JUMP_STRENGTH  # Bounce!
                        # Epic particles!
                        for _ in range(10):
                            self.particles.append(Particle(
                                self.flying_boss.x + self.flying_boss.width // 2,
                                self.flying_boss.y + self.flying_boss.height // 2,
                                random.uniform(-3, 3), random.uniform(-3, 3),
                                RED, 30
                            ))
                        if self.flying_boss.health <= 0:
                            self.flying_boss = None
                            self.boss_defeated = True  # Track boss is dead!
                            if self.current_level == 29:
                                self.unlock_achievement('wowy')
                            # EPIC EXPLOSION!
                            for _ in range(30):
                                self.particles.append(Particle(
                                    self.player.x + 10, self.player.y + 10,
                                    random.uniform(-5, 5), random.uniform(-5, 5),
                                    RED if random.random() > 0.5 else YELLOW, 60
                                ))
                    else:
                        # Hit from side = death!
                        self.player.x, self.player.y = self.levels[self.current_level]['spawn']
                        self.player.vel_x = 0
                        self.player.vel_y = 0
                
                if self.player.rect.colliderect(self.exit_rect):
                    # Can only exit if no boss or boss is defeated!
                    can_exit = True
                    if self.boss is not None:
                        can_exit = False  # Boss still alive!
                    if getattr(self, 'flying_boss', None) is not None:
                        can_exit = False  # Flying boss still alive!
                    
                    if can_exit and self.state == 'playing':
                        # Save best time for this level!
                        if self.current_level not in self.best_times or self.level_timer < self.best_times[self.current_level]:
                            self.best_times[self.current_level] = self.level_timer
                        # Speed run achievement (under 15 seconds = 900 frames)
                        if self.level_timer < 900:
                            self.unlock_achievement('speed_run')
                        # No damage achievement
                        if self.level_no_death:
                            self.unlock_achievement('no_damage')
                        # All coins achievement
                        if self.coins_collected == self.total_coins and self.total_coins > 0:
                            self.unlock_achievement('all_coins_1')
                        # Daily challenge check
                        if self.current_level == self.daily_level and not self.daily_completed:
                            goal = self.daily_goal
                            if goal == 'no_damage' and self.level_no_death:
                                self.daily_completed = True
                                self.shop_coins += self.daily_reward
                                self.floaty_texts.append({'x':SCREEN_WIDTH//2-80,'y':250,
                                    'vy':-1,'text':f'📅 DAILY DONE! +{self.daily_reward}🪙','col':PURPLE,'life':180,'maxlife':180})
                            elif goal == 'speed_run' and self.level_timer < 900:
                                self.daily_completed = True
                                self.shop_coins += self.daily_reward
                                self.floaty_texts.append({'x':SCREEN_WIDTH//2-80,'y':250,
                                    'vy':-1,'text':f'📅 DAILY DONE! +{self.daily_reward}🪙','col':PURPLE,'life':180,'maxlife':180})
                            elif goal == 'all_coins' and self.coins_collected == self.total_coins:
                                self.daily_completed = True
                                self.shop_coins += self.daily_reward
                                self.floaty_texts.append({'x':SCREEN_WIDTH//2-80,'y':250,
                                    'vy':-1,'text':f'📅 DAILY DONE! +{self.daily_reward}🪙','col':PURPLE,'life':180,'maxlife':180})
                        self.level_no_death = True  # reset for next level
                        self.level_timer = 0
                        # Mark this level as beaten!
                        self.levels_beaten.add(self.current_level)
                        # Update high score
                        if self.run_coins > self.high_score:
                            self.high_score = self.run_coins
                        # AUTO-SAVE!
                        self.save_game()
                        self.save_notif = 120
                        next_level = self.current_level + 1
                        
                        # TRIGGER CUTSCENES!
                        cutscene_to_show = None
                        if next_level == 5 and 4 not in self.cutscenes_seen:  # After level 5 flying boss
                            cutscene_to_show = 4  # Gas station
                            self.cutscenes_seen.add(4)
                            self.unlock_achievement('gotta_drink')
                        elif next_level == 6 and 8 not in self.cutscenes_seen:  # After level 6 long road
                            cutscene_to_show = 8  # The Long Road cutscene
                            self.cutscenes_seen.add(8)
                        elif next_level == 8 and 9 not in self.cutscenes_seen:  # After level 8, desert gas station
                            cutscene_to_show = 9  # Desert gas station
                            self.cutscenes_seen.add(9)
                        elif next_level == 10 and 5 not in self.cutscenes_seen:  # After level 10 boss
                            cutscene_to_show = 5  # Confrontation
                            self.cutscenes_seen.add(5)
                        elif next_level == 15 and 6 not in self.cutscenes_seen:  # After level 15, entering woods
                            cutscene_to_show = 6  # Enter the Woods
                            self.cutscenes_seen.add(6)
                        elif next_level == 29 and 7 not in self.cutscenes_seen:  # Before level 30
                            cutscene_to_show = 7  # Final boss
                            self.cutscenes_seen.add(7)
                        
                        if cutscene_to_show:
                            self.cutscene_mode = cutscene_to_show
                            self.cutscene_timer = 0
                            self.cutscene_next_level = next_level  # remember where to go after!
                            self.state = 'cutscene'
                            # Play cutscene music
                            pygame.mixer.stop()
                            cutscene_music = getattr(self, f'cutscene{cutscene_to_show}_music', None)
                            if cutscene_music:
                                cutscene_music.play()
                        else:
                            self.current_level = next_level
                            if self.current_level < len(self.levels):
                                self.load_level(self.current_level)
                            else:
                                self.game_completed = True
                                self.state = 'intro'
                                self.intro_timer = 0
                                self.particles = []
                                # 1 Sitting — completed whole game from level 0 without restarting
                                if self.session_started_level == 0:
                                    self.unlock_achievement('1_sitting')
                    else:
                        self.state = 'intro'
                        self.intro_timer = 0
                        self.particles = []
                # Check for falling off screen
                if self.player.y > 1000 and not self.game_over:
                    self.player_health -= 1
                    self.level_no_death = False
                    self.invincibility_frames = 60
                    self.shake_timer = 10; self.shake_intensity = 6
                    try: self.sfx.get('hit') and self.sfx['hit'].play()
                    except: pass
                    if self.player_health <= 0:
                        self.player_health = 0
                        self.total_deaths += 1
                        self.game_over = True
                        self.game_over_timer = 0
                    else:
                        self.total_deaths += 1
                        spawn = self.levels[self.current_level]['spawn'] if self.state=='playing' else self.tutorial_level['spawn']
                        self.player.x, self.player.y = spawn
                        self.player.vel_x = 0; self.player.vel_y = 0
                
                self.update_camera()
                # ── SCREEN SHAKE ──────────────────────────────────────────
                shake_x = random.randint(-self.shake_intensity, self.shake_intensity) if self.shake_timer > 0 else 0
                shake_y = random.randint(-self.shake_intensity, self.shake_intensity) if self.shake_timer > 0 else 0
                self.camera_x += shake_x
                self.camera_y += shake_y
                self.draw_background()
                self.draw_weather()
                
                # Draw regular platforms (BLACK!)
                for platform in self.platforms:
                    if not isinstance(platform, MovingPlatform):  # Regular platforms
                        pygame.draw.rect(self.screen, PLATFORM_COLOR, 
                                        (platform.x - self.camera_x, platform.y - self.camera_y, 
                                         platform.width, platform.height))
                        pygame.draw.rect(self.screen, GRAY, 
                                        (platform.x - self.camera_x, platform.y - self.camera_y, 
                                         platform.width, platform.height), 2)
                
                # Draw moving platforms separately with their draw method
                for moving_plat in getattr(self, 'moving_platforms', []):
                    moving_plat.draw(self.screen, self.camera_x, self.camera_y)
                
                for enemy in self.enemies:
                    enemy.draw(self.screen, self.camera_x, self.camera_y)
                if self.boss:
                    self.boss.draw(self.screen, self.camera_x, self.camera_y)
                
                if getattr(self, 'flying_boss', None):
                    self.flying_boss.draw(self.screen, self.camera_x, self.camera_y)

                # Update and draw NPCs
                for npc in getattr(self, 'npcs', []):
                    npc.update(self.player.rect)
                    npc.draw(self.screen, self.camera_x, self.camera_y)
                
                for coin in self.coins:
                    coin.draw(self.screen, self.camera_x, self.camera_y)

                # Draw gems!
                for gem in getattr(self, 'gems', []):
                    gem.draw(self.screen, self.camera_x, self.camera_y)
                    if not gem.collected and self.player.rect.colliderect(gem.rect):
                        gem.collected = True
                        self.gems_collected += 1
                        self.shop_coins += 5; self.bank_coins += 5; self.run_coins += 5
                        self.floaty_texts.append({'x': gem.x, 'y': gem.y,
                            'vy': -2, 'text': '💎 +5', 'col': (150,200,255), 'life': 55, 'maxlife': 55})
                        try: self.sfx.get('gem') and self.sfx['gem'].play()
                        except: pass
                for power_up in getattr(self, 'power_ups', []):
                    power_up.draw(self.screen, self.camera_x, self.camera_y)
                
                for spike in self.spikes:
                    spike.draw(self.screen, self.camera_x, self.camera_y)
                for projectile in self.projectiles:
                    projectile.draw(self.screen, self.camera_x, self.camera_y)

                # Draw sticker - BIG visible spinning star with bouncing arrow
                if self.current_level not in self.stickers_found and hasattr(self, '_sticker_rect'):
                    self._sticker_anim += 0.06
                    sr = self._sticker_rect
                    cx2 = sr.x + sr.w // 2 - self.camera_x
                    cy2 = sr.y + sr.h // 2 - self.camera_y
                    bob = math.sin(self._sticker_anim * 2) * 6
                    cy2 += bob

                    # Big outer glow
                    for r, alpha in [(28, 30), (20, 60), (14, 100)]:
                        gs = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                        pygame.draw.circle(gs, (255, 220, 0, alpha), (r, r), r)
                        self.screen.blit(gs, (cx2 - r, cy2 - r))

                    # Spinning 8-point star
                    spin = self._sticker_anim * 60
                    for angle in range(0, 360, 45):
                        a = math.radians(angle + spin)
                        r_len = 18 if angle % 90 == 0 else 11
                        ex2 = cx2 + math.cos(a) * r_len
                        ey2 = cy2 + math.sin(a) * r_len
                        pygame.draw.line(self.screen, YELLOW, (int(cx2), int(cy2)), (int(ex2), int(ey2)), 3)
                    pygame.draw.circle(self.screen, WHITE, (int(cx2), int(cy2)), 7)
                    pygame.draw.circle(self.screen, YELLOW, (int(cx2), int(cy2)), 5)

                    # Bouncing "⭐" label above it
                    sf = pygame.font.Font(None, 22)
                    slbl = sf.render("STICKER!", True, YELLOW)
                    self.screen.blit(slbl, (cx2 - slbl.get_width()//2, cy2 - 38))

                    # Downward arrow pointing at it
                    arr_y = cy2 - 50 + math.sin(self._sticker_anim * 3) * 5
                    pygame.draw.polygon(self.screen, YELLOW, [
                        (cx2, arr_y + 14), (cx2 - 7, arr_y), (cx2 + 7, arr_y)
                    ])

                self.player.draw(self.screen, self.camera_x, self.camera_y)
                # Draw equipped hat on player in-game!
                hat = getattr(self, 'hat_equipped', None)
                if hat:
                    self._draw_hat_at(hat,
                        int(self.player.x - self.camera_x + 2),
                        int(self.player.y - self.camera_y - 2))

                # Draw hat on top of player!
                hat = getattr(self, 'hat_equipped', None)
                if hat:
                    px = self.player.rect.x - self.camera_x
                    py = self.player.rect.y - self.camera_y
                    self._draw_hat_at(hat, px + 10, py - 2)

                pygame.draw.rect(self.screen, GREEN,
                                (self.exit_rect.x - self.camera_x, self.exit_rect.y - self.camera_y,
                                 self.exit_rect.width, self.exit_rect.height))
                self.draw_mini_map()
                if self.state == 'playing':
                    self.draw_ui()
                    self.draw_health()
                    self.draw_big_boss_healthbar()
                    self.draw_exit_portal()
                elif self.state == 'tutorial':
                    self.draw_tutorial_ui()

                # ── FLOATY TEXTS (world space) ─────────────────────────────
                ff = pygame.font.Font(None, 28)
                for ft in self.floaty_texts:
                    a = int(255 * ft['life'] / ft['maxlife'])
                    col = (*ft['col'][:3],) if len(ft['col']) == 3 else ft['col']
                    surf = ff.render(ft['text'], True, col)
                    surf.set_alpha(a)
                    self.screen.blit(surf, (ft['x'] - self.camera_x, ft['y'] - self.camera_y))

                # ── COMBO DISPLAY ──────────────────────────────────────────
                if self.combo >= 2 and self.combo_timer > 0:
                    cf = pygame.font.Font(None, 52)
                    fade = min(255, self.combo_timer * 4)
                    combo_col = (255, max(0,255-self.combo*20), 0)
                    cs = cf.render(f"x{self.combo} COMBO!", True, combo_col)
                    cs.set_alpha(fade)
                    self.screen.blit(cs, (SCREEN_WIDTH//2 - cs.get_width()//2, 80))

                # ── DASH COOLDOWN BAR ──────────────────────────────────────
                if self.dash_cd > 0:
                    df = pygame.font.Font(None, 20)
                    ds = df.render("DASH", True, CYAN)
                    self.screen.blit(ds, (SCREEN_WIDTH - 90, SCREEN_HEIGHT - 50))
                    pygame.draw.rect(self.screen, DARK_GRAY, (SCREEN_WIDTH-90, SCREEN_HEIGHT-34, 80, 8))
                    fill = int(80 * (1 - self.dash_cd / 40))
                    pygame.draw.rect(self.screen, CYAN, (SCREEN_WIDTH-90, SCREEN_HEIGHT-34, fill, 8))
                else:
                    df = pygame.font.Font(None, 20)
                    ds = df.render("DASH ready!", True, CYAN)
                    self.screen.blit(ds, (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 50))

                # ── SAVE NOTIFICATION ─────────────────────────────────────
                if self.save_notif > 0:
                    self.save_notif -= 1
                    a = min(255, self.save_notif * 4)
                    sf2 = pygame.font.Font(None, 36)
                    ss = sf2.render("💾 SAVED!", True, GREEN)
                    ss.set_alpha(a)
                    self.screen.blit(ss, (SCREEN_WIDTH//2 - ss.get_width()//2, 40))

                self.draw_achievement_popups()
                self.check_achievements()
                self.draw_level_transition()
                # Gem count HUD
                gems_left = sum(1 for g in getattr(self,'gems',[]) if not g.collected)
                if gems_left > 0:
                    gf=pygame.font.Font(None,22)
                    gt=gf.render(f"💎 {gems_left} gem{'s' if gems_left>1 else ''} left",True,(150,200,255))
                    self.screen.blit(gt,(SCREEN_WIDTH-gt.get_width()-12,SCREEN_HEIGHT-72))
                if self.state == 'playing':
                    secs = self.level_timer // 60
                    best = self.best_times.get(self.current_level)
                    tf = pygame.font.Font(None, 22)
                    tcol = GREEN if best and self.level_timer < best else WHITE
                    ts2 = tf.render(f"⏱ {secs}s" + (f"  best:{best//60}s" if best else ""), True, tcol)
                    self.screen.blit(ts2, (SCREEN_WIDTH//2 - ts2.get_width()//2, SCREEN_HEIGHT - 24))

                # Journal overlay during gameplay
                if self.journal_open:
                    self.draw_journal()

                # Level name banner (first ~3 seconds of level)
                if self.state == 'playing':
                    self.draw_level_banner()

                # Pause screen
                if self.paused:
                    self.draw_pause()

                # Game over screen
                if self.game_over:
                    self.draw_game_over()
            
            if self.game_completed and self.state not in ['playing','tutorial','cutscene','intro']:
                self.screen.fill(BLACK)
                font = pygame.font.Font(None, 64)
                text = font.render("🎉 YOU WIN! 🎉", True, YELLOW)
                self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 60))
                font2 = pygame.font.Font(None, 36)
                text2 = font2.render(f"Levels beaten: {len(self.levels_beaten)} / 30   Stickers: {len(self.stickers_found)} / 30", True, WHITE)
                self.screen.blit(text2, (SCREEN_WIDTH // 2 - text2.get_width() // 2, SCREEN_HEIGHT // 2 + 10))
                text3 = font2.render("Press ESC to return to menu", True, GRAY)
                self.screen.blit(text3, (SCREEN_WIDTH // 2 - text3.get_width() // 2, SCREEN_HEIGHT // 2 + 60))
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
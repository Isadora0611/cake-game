import pygame
import random
import sys
import math
import array
import os
from enum import Enum

# 初始化Pygame
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=8, buffer=1024)

# ========== 自动搜索并加载 FLAC 背景音乐 ==========
bgm_sound = None
code_dir = os.path.dirname(os.path.abspath(__file__))  # 获取代码所在的文件夹路径
flac_files = [f for f in os.listdir(code_dir) if f.lower().endswith('.flac')]  # 自动找出所有flac文件

if flac_files:
    try:
        bgm_sound = pygame.mixer.Sound(os.path.join(code_dir, flac_files[0]))
        bgm_sound.set_volume(0.4)  # 音量 0.0~1.0，0.4 比较柔和
        print(f"🎵 找到音乐文件: {flac_files[0]}，正在播放~")
    except Exception as e:
        print(f"⚠️ 音乐加载失败({e})，将以静音模式运行。")
else:
    print(" 没有找到任何 .flac 文件。")
    print(f"   请把音乐文件放到这个文件夹: {code_dir}")
# =======================================

# 游戏常量
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
BASKET_WIDTH = 110
BASKET_HEIGHT = 20
CAKE_SIZE = 50
WIN_COUNT = 44
MAX_MISSED = 20

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)
UI_BROWN = (80, 40, 10)
PINK = (255, 192, 203)
HEART_PINK = (255, 200, 210)
BASKET_DARK = (101, 67, 33)
BASKET_LIGHT = (160, 82, 45)
BABY_BLUE1 = (191, 239, 255)
BABY_BLUE2 = (174, 238, 238)
BABY_BLUE3 = (135, 206, 235)
ICING_WHITE = (255, 255, 255)
ACCENT_BLUE = (70, 130, 180)
PASTEL_YELLOW = (255, 224, 130)
FLAME_YELLOW = (255, 241, 118)
FLAME_ORANGE = (255, 213, 79)
STAR_COLORS = [YELLOW, WHITE, PASTEL_YELLOW, (255, 200, 200)]
CRACK_COLORS = [BABY_BLUE1, BABY_BLUE2, BABY_BLUE3, ICING_WHITE, ACCENT_BLUE]
CREAM_YELLOW = (255, 253, 230)
SOFT_GRID = (230, 220, 200)
WARM_ORANGE = (255, 223, 186)
SOFT_BLUE_GREY = (200, 210, 220)


# ========== 音效生成 ==========
def generate_sound(frequency=440, duration=0.1, volume=0.3, fade_out=True):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * n_samples)
    for i in range(n_samples):
        t = i / sample_rate
        wave = math.sin(2 * math.pi * frequency * t)
        wave += 0.5 * math.sin(4 * math.pi * frequency * t)
        val = int(wave * volume * 32767)
        if fade_out:
            val = int(val * (1 - i / n_samples))
        buf[i] = max(-32767, min(32767, val))
    sound = pygame.mixer.Sound(buffer=buf)
    return sound

def generate_crash_sound(duration=0.15, volume=0.4):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * n_samples)
    for i in range(n_samples):
        val = random.randint(-32767, 32767) * volume
        fade = (1 - (i / n_samples) ** 0.5)
        buf[i] = max(-32767, min(32767, int(val * fade)))
    sound = pygame.mixer.Sound(buffer=buf)
    return sound

catch_sounds = [
    generate_sound(frequency=880, duration=0.15, volume=0.4),
    generate_sound(frequency=1046, duration=0.15, volume=0.4),
    generate_sound(frequency=1318, duration=0.2, volume=0.5),
]
miss_sound = generate_crash_sound(duration=0.2, volume=0.3)


# ========== 特效类 ==========
class Particle:
    def __init__(self, x, y, color, is_star=False):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6) if is_star else random.uniform(1, 4)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - (3 if is_star else 1)
        self.life = 1.0
        self.decay = random.uniform(0.02, 0.05)
        self.size = random.randint(3, 7) if is_star else random.randint(2, 5)
        self.is_star = is_star

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if not self.is_star:
            self.vy += 0.2
        self.life -= self.decay
        return self.life > 0

    def draw(self, surface):
        s = int(self.size * self.life)
        if s > 0:
            if self.is_star:
                pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), s)
            else:
                rect = pygame.Rect(int(self.x), int(self.y), s, s)
                pygame.draw.rect(surface, self.color, rect)


# ========== 蛋糕绘制函数 ==========
def draw_cake(surface, cx, bottom_y, s=0.2):
    bw, bh = int(240*s), int(65*s)
    bx, rt = cx - bw//2, bottom_y - bh
    ehw, ehh = bw//2, int(16*s)
    pygame.draw.rect(surface, BABY_BLUE2, (bx, rt, bw, bh))
    pygame.draw.ellipse(surface, BABY_BLUE1, (cx-ehw, rt-ehh, bw, 2*ehh))
    draw_icing(surface, cx, rt, ehw, ehh, s)
    draw_dots(surface, bx, rt, bw, bh, s)
    mw, mh = int(180*s), int(60*s)
    mx = cx - mw//2
    mrt = rt - 2*ehh + int(5*s)
    mhw, mhh = mw//2, int(15*s)
    pygame.draw.rect(surface, BABY_BLUE3, (mx, mrt, mw, mh))
    pygame.draw.ellipse(surface, BABY_BLUE2, (cx-mhw, mrt-mhh, mw, 2*mhh))
    draw_icing(surface, cx, mrt, mhw, mhh, s)
    draw_dots(surface, mx, mrt, mw, mh, s)
    tw, th = int(120*s), int(45*s)
    tx = cx - tw//2
    trt = mrt - 2*mhh + int(5*s)
    thw, thh = tw//2, int(11*s)
    pygame.draw.rect(surface, BABY_BLUE1, (tx, trt, tw, th))
    pygame.draw.ellipse(surface, BABY_BLUE3, (cx-thw, trt-thh, tw, 2*thh))
    draw_icing(surface, cx, trt, thw, thh, s)
    cby = trt - thh
    cw = max(2, int(6*s))
    ch = int(35*s)
    for i in range(7):
        cx_i = tx + int(tw/8*(i+1))
        pygame.draw.rect(surface, PASTEL_YELLOW, (cx_i-cw//2, cby-ch, cw, ch))
        pygame.draw.circle(surface, FLAME_ORANGE, (cx_i, cby-ch-int(5*s)), max(3, int(9*s)))
        pygame.draw.circle(surface, FLAME_YELLOW, (cx_i, cby-ch-int(5*s)), max(2, int(5*s)))

def draw_icing(surface, cx, rect_top, hw, hh, s):
    pts = []
    for i in range(101):
        a = math.pi * i / 100
        px = cx + hw * math.cos(a)
        py = rect_top + hh * math.sin(a)
        pts.append((int(px), int(py)))
    if len(pts) > 2:
        pygame.draw.lines(surface, ICING_WHITE, False, pts, max(2, int(5*s)))
    for i in range(1, 10, 2):
        a = math.pi * i / 10
        px = cx + hw * math.cos(a)
        py = rect_top + hh * math.sin(a)
        dw = max(3, int(10*s))
        dh = max(4, int(14*s))
        pygame.draw.ellipse(surface, ICING_WHITE, (int(px)-dw//2, int(py), dw, dh))

def draw_dots(surface, x, y, w, h, s):
    r = max(2, int(6*s))
    for i in range(5):
        pygame.draw.circle(surface, ACCENT_BLUE, (int(x + w//6*(i+1)), int(y + h*0.45)), r)


# ========== 游戏核心类 ==========
class GameState(Enum):
    PLAYING = 1
    WIN = 2
    LOSE = 3

class Basket:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.speed = 9
    
    def move_left(self):
        if self.rect.left > 0:
            self.rect.x -= self.speed
    
    def move_right(self):
        if self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed
    
    def draw(self, surface):
        w, h = self.rect.width, self.rect.height + 30
        cx, cy = self.rect.centerx, self.rect.top
        points = [
            (cx - w//2, cy), (cx + w//2, cy),
            (cx + w//2 - 10, cy + h), (cx - w//2 + 10, cy + h),
        ]
        pygame.draw.polygon(surface, BASKET_LIGHT, points)
        pygame.draw.polygon(surface, BASKET_DARK, points, 3)
        for i in range(3):
            yy = cy + 8 + i * 10
            pygame.draw.line(surface, BASKET_DARK, (cx - w//2 + 3, yy), (cx + w//2 - 3, yy), 2)
        pygame.draw.arc(surface, BASKET_DARK, (cx - 25, cy - 25, 50, 35), 0.3, math.pi - 0.3, 3)

class Cake:
    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x, y, size, size)
        self.speed = random.randint(2, 4)
    
    def fall(self):
        self.rect.y += self.speed
    
    def is_off_screen(self):
        return self.rect.y > SCREEN_HEIGHT
    
    def draw(self, surface):
        draw_cake(surface, self.rect.centerx, self.rect.bottom - 5, s=0.2)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Cake Catching Game")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        self.particles = []
        self.win_petals = []
        self.reset_game()
    
    def reset_game(self):
        self.basket = Basket(SCREEN_WIDTH // 2 - BASKET_WIDTH // 2, 
                            SCREEN_HEIGHT - 60, BASKET_WIDTH, BASKET_HEIGHT)
        self.cakes = []
        self.score = 0
        self.missed = 0
        self.state = GameState.PLAYING
        self.spawn_timer = 0
        self.spawn_rate = 50
        self.win_frame = 0
        self.lose_frame = 0
        self.particles = []
        self.win_petals = []
        
        # 播放背景乐
        if bgm_sound:
            bgm_sound.play(loops=-1)
    
    def spawn_catch_effect(self, x, y):
        for _ in range(12):
            color = random.choice(STAR_COLORS)
            self.particles.append(Particle(x, y, color, is_star=True))
    
    def spawn_miss_effect(self, x, y):
        for _ in range(15):
            color = random.choice(CRACK_COLORS)
            self.particles.append(Particle(x, y, color, is_star=False))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE:
                    if self.state in [GameState.WIN, GameState.LOSE]:
                        self.reset_game()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.basket.move_left()
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.basket.move_right()
        return True
    
    def update(self):
        self.particles = [p for p in self.particles if p.update()]
        
        for p in self.win_petals[:]:
            p.y += p.speed
            p.x += math.sin(self.win_frame * 0.02 + p.offset) * 0.5
            if p.y > SCREEN_HEIGHT + 20:
                self.win_petals.remove(p)

        if self.state != GameState.PLAYING:
            return
            
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_rate:
            self.spawn_cake()
            self.spawn_timer = 0
            
        for cake in self.cakes[:]:
            cake.fall()
            if self.basket.rect.colliderect(cake.rect):
                self.cakes.remove(cake)
                self.score += 1
                
                if self.score < 15:
                    catch_sounds[0].play()
                elif self.score < 35:
                    catch_sounds[1].play()
                else:
                    catch_sounds[2].play()
                    
                self.spawn_catch_effect(cake.rect.centerx, cake.rect.bottom)
                
                if self.spawn_rate > 24:
                    self.spawn_rate -= 0.25
                    
            elif cake.is_off_screen():
                self.cakes.remove(cake)
                self.missed += 1
                
                miss_sound.play()
                self.spawn_miss_effect(cake.rect.centerx, SCREEN_HEIGHT - 10)
                
                if self.missed >= MAX_MISSED:
                    self.state = GameState.LOSE
                    if bgm_sound:
                        bgm_sound.stop()
                    
        if self.score >= WIN_COUNT:
            self.state = GameState.WIN
            if bgm_sound:
                bgm_sound.stop()
            for _ in range(60):
                self.win_petals.append({
                    'x': random.randint(0, SCREEN_WIDTH),
                    'y': random.randint(-SCREEN_HEIGHT, 0),
                    'speed': random.uniform(0.5, 1.5),
                    'size': random.randint(4, 8),
                    'color': random.choice([HEART_PINK, PINK, (255, 220, 230), (255, 245, 245)]),
                    'offset': random.uniform(0, math.pi * 2)
                })
    
    def spawn_cake(self):
        x = random.randint(0, SCREEN_WIDTH - CAKE_SIZE)
        cake = Cake(x, -CAKE_SIZE, CAKE_SIZE)
        self.cakes.append(cake)
    
    def draw(self):
        self.screen.fill(CREAM_YELLOW)
        self.draw_grid()
        
        for cake in self.cakes:
            cake.draw(self.screen)
            
        for p in self.particles:
            p.draw(self.screen)
            
        self.basket.draw(self.screen)
        self.draw_ui()
        
        if self.state == GameState.WIN:
            self.draw_win_screen()
        elif self.state == GameState.LOSE:
            self.draw_lose_screen()
            
        pygame.display.flip()
    
    def draw_grid(self):
        grid_size = 40
        for x in range(0, SCREEN_WIDTH, grid_size):
            pygame.draw.line(self.screen, SOFT_GRID, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, grid_size):
            pygame.draw.line(self.screen, SOFT_GRID, (0, y), (SCREEN_WIDTH, y), 1)
    
    def draw_ui(self):
        score_text = self.font_medium.render(f"Cakes: {self.score}/{WIN_COUNT}", True, UI_BROWN)
        self.screen.blit(score_text, (20, 20))
        
        lives_left = MAX_MISSED - self.missed
        label = self.font_small.render("Lives: ", True, HEART_PINK)
        self.screen.blit(label, (20, 60))
        
        for i in range(lives_left):
            hx = 90 + i * 28
            hy = 72
            pygame.draw.circle(self.screen, HEART_PINK, (hx - 6, hy - 4), 7)
            pygame.draw.circle(self.screen, HEART_PINK, (hx + 6, hy - 4), 7)
            pygame.draw.polygon(self.screen, HEART_PINK, [(hx - 13, hy), (hx, hy + 14), (hx + 13, hy)])
            
        difficulty_text = self.font_small.render(f"Level: {int((50 - self.spawn_rate) / 1.3) + 1}", True, UI_BROWN)
        self.screen.blit(difficulty_text, (SCREEN_WIDTH - 150, 20))

    def draw_win_screen(self):
        self.win_frame += 1
        
        for p in self.win_petals:
            pygame.draw.ellipse(self.screen, p['color'], (int(p['x']), int(p['y']), p['size'], int(p['size']*0.6)))
            if len(self.win_petals) < 100 and self.win_frame % 10 == 0:
                self.win_petals.append({
                    'x': random.randint(0, SCREEN_WIDTH),
                    'y': random.randint(-20, -5),
                    'speed': random.uniform(0.5, 1.5),
                    'size': random.randint(4, 8),
                    'color': random.choice([HEART_PINK, PINK, (255, 220, 230)]),
                    'offset': random.uniform(0, math.pi * 2)
                })
                
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 240, 220, 160))
        self.screen.blit(overlay, (0, 0))
        
        cake_cx = SCREEN_WIDTH // 2
        cake_bottom = SCREEN_HEIGHT // 2 + 80
        draw_cake(self.screen, cake_cx, cake_bottom, s=0.55)
        
        flame_y_base = cake_bottom - 120
        for i in range(5):
            fx = cake_cx - 40 + i * 20
            flicker = math.sin(self.win_frame * 0.1 + i) * 3
            fy = flame_y_base + flicker
            
            glow_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 255, 200, 80), (15, 15), 15)
            self.screen.blit(glow_surf, (fx - 15, fy - 20))
            
            pygame.draw.ellipse(self.screen, FLAME_ORANGE, (fx - 5, int(fy) - 12, 10, 16))
            pygame.draw.ellipse(self.screen, FLAME_YELLOW, (fx - 3, int(fy) - 10, 6, 12))
        
        win_text = self.font_large.render("Happy Birthday!", True, UI_BROWN)
        win_rect = win_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120))
        self.screen.blit(win_text, win_rect)
        
        sub_text = self.font_small.render(f"Successfully caught {self.score} cakes!", True, HEART_PINK)
        sub_rect = sub_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 75))
        self.screen.blit(sub_text, sub_rect)
        
        restart_text = self.font_small.render("Press SPACE to restart", True, BASKET_LIGHT)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 140))
        self.screen.blit(restart_text, restart_rect)

    def draw_lose_screen(self):
        self.lose_frame += 1
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((220, 225, 230, 180)) 
        self.screen.blit(overlay, (0, 0))
        
        alpha = min(255, self.lose_frame * 5)
        
        sad_cx = SCREEN_WIDTH // 2
        sad_cy = SCREEN_HEIGHT // 2 - 80
        draw_cake(self.screen, sad_cx, sad_cy + 20, s=0.3)
        
        pygame.draw.circle(self.screen, UI_BROWN, (sad_cx - 10, sad_cy - 15), 3)
        pygame.draw.circle(self.screen, UI_BROWN, (sad_cx + 10, sad_cy - 15), 3)
        
        pygame.draw.arc(self.screen, UI_BROWN, (sad_cx - 8, sad_cy - 8, 16, 12), 0.2, math.pi - 0.2, 2)
        
        tear_x = sad_cx + 18
        tear_y = sad_cy - 18 + math.sin(self.lose_frame * 0.1) * 2
        pygame.draw.ellipse(self.screen, BABY_BLUE3, (tear_x - 3, int(tear_y), 6, 8))

        sub_text = self.font_medium.render("Almost there~", True, HEART_PINK)
        sub_rect = sub_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        sub_text.set_alpha(alpha)
        self.screen.blit(sub_text, sub_rect)
        
        score_text = self.font_small.render(f"Cakes: {self.score}/{WIN_COUNT}", True, UI_BROWN)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 90))
        score_text.set_alpha(alpha)
        self.screen.blit(score_text, score_rect)
        
        if self.lose_frame > 30:
            restart_text = self.font_small.render("Press SPACE to restart", True, ACCENT_BLUE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 140))
            restart_text.set_alpha(min(255, (self.lose_frame - 30) * 8))
            self.screen.blit(restart_text, restart_rect)
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()

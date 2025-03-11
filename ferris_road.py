import pygame
import os
import sys
import random

WIN_WIDTH, WIN_HEIGHT = 500, 700
GRID_SIZE = 50
MAX_LANES = 15
MAX_RIVER_COUNT = 2
MAX_GRASS_COUNT = 1
MAX_ROAD_COUNT = 3
PRE_GENERATE_LINES = 5

pygame.init()
win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Ferris Road")
clock = pygame.time.Clock()

# Initialize Pygame mixer for music
pygame.mixer.init()

# Load game textures
BG_IMG = pygame.image.load("images/background.png").convert()
CRAB_IMG = pygame.image.load("images/crab.png").convert_alpha()  # Renamed from frog.png to crab.png

# Load 8 different car textures
CAR_IMGS = [
    pygame.image.load("images/car1.png").convert_alpha(),
    pygame.image.load("images/car2.png").convert_alpha(),
    pygame.image.load("images/car3.png").convert_alpha(),
    pygame.image.load("images/car4.png").convert_alpha(),
    pygame.image.load("images/car5.png").convert_alpha(),
    pygame.image.load("images/car6.png").convert_alpha(),
    pygame.image.load("images/car7.png").convert_alpha(),
    pygame.image.load("images/car8.png").convert_alpha()
]
CAR_IMGS_FLIPPED = [pygame.transform.flip(img, True, False) for img in CAR_IMGS]

# Load 6 different grass textures
GRASS_IMGS = [
    pygame.image.load("images/grass1.png").convert(),
    pygame.image.load("images/grass2.png").convert(),
    pygame.image.load("images/grass3.png").convert(),
    pygame.image.load("images/grass4.png").convert(),
    pygame.image.load("images/grass5.png").convert(),
    pygame.image.load("images/grass6.png").convert()
]

# Load 2 different road textures
ROAD_IMGS = [
    pygame.image.load("images/road1.png").convert(),
    pygame.image.load("images/road2.png").convert()
]

# Load 2 different river textures
RIVER_IMGS = [
    pygame.image.load("images/river1.png").convert(),
    pygame.image.load("images/river2.png").convert()
]

LOG_IMG = pygame.image.load("images/log.png").convert_alpha()

# Load background for Game Over screen
GAME_OVER_BG = pygame.image.load("images/game_over_background.png").convert()  # Must be 500x700 in size

# Load music and sound effects
try:
    pygame.mixer.music.load("sounds/background_music.mp3")  # Background music during gameplay
    game_over_sound = pygame.mixer.Sound("sounds/game_over.mp3")  # Sound for Game Over screen
except pygame.error as e:
    print(f"Error loading music: {e}")
    pygame.mixer.music.load("sounds/background_music.mp3")  # Fallback to a default file if needed
    game_over_sound = pygame.mixer.Sound("sounds/game_over.mp3")

# Set initial volumes
pygame.mixer.music.set_volume(0.01)  # Reduced to 98% of original volume
game_over_sound.set_volume(0.0325)  # Reduced to 95% of original volume

# Play background music in a loop
pygame.mixer.music.play(-1)  # -1 means loop indefinitely

class Obstacle:
    def __init__(self, x, y, speed, img):
        self.x = x
        self.y = y
        self.speed = speed
        self.img = pygame.transform.flip(img, True, False) if speed >= 0 else img  # Flipped for right, original for left

    def move(self):
        self.x += self.speed
        if self.speed > 0 and self.x > WIN_WIDTH:
            self.x = -self.img.get_width()
        elif self.speed < 0 and self.x < -self.img.get_width():
            self.x = WIN_WIDTH

    def draw(self, win, camera_y):
        win.blit(self.img, (self.x, self.y - camera_y))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.img.get_width(), GRID_SIZE)

class Lane:
    def __init__(self, y, lane_type):
        self.y = y
        self.type = lane_type
        # Randomly select a texture based on lane type
        if lane_type == "grass":
            self.texture = random.choice(GRASS_IMGS)
        elif lane_type == "road":
            self.texture = random.choice(ROAD_IMGS)
        elif lane_type == "river":
            self.texture = random.choice(RIVER_IMGS)

        self.obstacles = []
        if lane_type == "road":
            lane_speed = random.choice([-3, 3])
            num_cars = random.randint(1, 2)
            min_distance = CAR_IMGS[0].get_width() * 2  # Use the first car's width for consistency
            max_x = WIN_WIDTH - CAR_IMGS[0].get_width()  # Use the first car's width for consistency
            for i in range(num_cars):
                # Randomly choose a car texture
                car_img = random.choice(CAR_IMGS)
                if not self.obstacles:
                    obs_x = random.randint(0, max_x)
                else:
                    last_x = self.obstacles[-1].x
                    start_x = last_x + min_distance
                    if start_x > max_x:
                        obs_x = random.randint(0, max_x // 2)
                    else:
                        while True:
                            obs_x = random.randint(start_x, max_x)
                            new_rect = pygame.Rect(obs_x, y, car_img.get_width(), GRID_SIZE)
                            collision = False
                            for obs in self.obstacles:
                                if new_rect.colliderect(obs.get_rect()):
                                    collision = True
                                    break
                            if not collision:
                                break
                self.obstacles.append(Obstacle(obs_x, y, lane_speed, car_img))
        elif lane_type == "river":
            speed = random.choice([-2, 2])
            for _ in range(random.randint(2, 4)):
                obs_x = random.randint(0, WIN_WIDTH)
                self.obstacles.append(Obstacle(obs_x, y, speed, LOG_IMG))

lanes = []

def reset_game():
    global x, y, score, camera_y, lanes, river_count, grass_count, road_count, can_move, game_over, current_log, game_over_sound_played
    x, y = WIN_WIDTH // 2, WIN_HEIGHT - GRID_SIZE
    score, camera_y, river_count, grass_count, road_count = 0, 0, 0, 0, 0
    lanes.clear()
    can_move, game_over = True, False
    current_log = None
    game_over_sound_played = False  # Flag to track if Game Over sound has been played
    for i in range(MAX_LANES):
        lane_y = WIN_HEIGHT - (i + 1) * GRID_SIZE
        if i == 0:
            lane_type = "grass"
            grass_count = 1
        else:
            if river_count >= MAX_RIVER_COUNT:
                available_types = ["grass", "road"]
            else:
                available_types = ["grass", "road", "river"]
            if grass_count >= MAX_GRASS_COUNT:
                available_types.remove("grass")
            if road_count >= MAX_ROAD_COUNT:
                available_types.remove("road")
            lane_type = random.choice(available_types)
            if lane_type == "river":
                river_count += 1
                grass_count = 0
                road_count = 0
            elif lane_type == "grass":
                grass_count += 1
                river_count = 0
                road_count = 0
            elif lane_type == "road":
                road_count += 1
                river_count = 0
                grass_count = 0
        lanes.append(Lane(lane_y, lane_type))
    # Restart background music when resetting the game
    pygame.mixer.music.play(-1)

# Load Poppins fonts
try:
    SCORE_FONT = pygame.font.Font("C:\\ESD\\testgame\\font\\Poppins-Medium.ttf", 30)  # For score and button
    GAME_FONT = pygame.font.Font("C:\\ESD\\testgame\\font\\Poppins-Bold.ttf", 50)  # For "GAME OVER"
except:
    SCORE_FONT = pygame.font.SysFont("Arial", 30)  # Fallback font
    GAME_FONT = pygame.font.SysFont("Arial", 50)

reset_game()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if game_over and event.type == pygame.MOUSEBUTTONDOWN:
            # Synchronize clickable area with button position
            if btn_rect.collidepoint(event.pos):
                reset_game()

    if not game_over:
        keys = pygame.key.get_pressed()
        if can_move:
            if keys[pygame.K_UP]:
                y -= GRID_SIZE
                score += 1
                can_move = False
            elif keys[pygame.K_LEFT] and x > 0:
                x -= GRID_SIZE
                can_move = False
            elif keys[pygame.K_RIGHT] and x < WIN_WIDTH - GRID_SIZE:
                x += GRID_SIZE
                can_move = False

        if not any(keys[k] for k in [pygame.K_UP, pygame.K_LEFT, pygame.K_RIGHT]):
            can_move = True

        camera_y = min(camera_y, y - WIN_HEIGHT + GRID_SIZE * PRE_GENERATE_LINES)

        if lanes[0].y - camera_y > -GRID_SIZE:
            new_y = lanes[0].y - GRID_SIZE
            if river_count >= MAX_RIVER_COUNT:
                available_types = ["grass", "road"]
            else:
                available_types = ["grass", "road", "river"]
            if grass_count >= MAX_GRASS_COUNT:
                available_types.remove("grass")
            if road_count >= MAX_ROAD_COUNT:
                available_types.remove("road")
            lane_type = random.choice(available_types)
            if lane_type == "river":
                river_count += 1
                grass_count = 0
                road_count = 0
            elif lane_type == "grass":
                grass_count += 1
                river_count = 0
                road_count = 0
            elif lane_type == "road":
                road_count += 1
                river_count = 0
                grass_count = 0
            lanes.insert(0, Lane(new_y, lane_type))
            if len(lanes) > MAX_LANES:
                lanes.pop(-1)

        win.blit(BG_IMG, (0, 0))
        crab_rect = pygame.Rect(x, y - camera_y, GRID_SIZE, GRID_SIZE)

        for lane in lanes:
            lane_screen_y = lane.y - camera_y
            win.blit(lane.texture, (0, lane_screen_y))

            if lane.type == "road":
                for obs in lane.obstacles:
                    obs.move()
                    obs_rect = pygame.Rect(obs.x, lane_screen_y, obs.img.get_width(), GRID_SIZE)
                    obs.draw(win, camera_y)
                    if abs(lane.y - y) < GRID_SIZE / 2 and crab_rect.colliderect(obs_rect):
                        game_over = True

            elif lane.type == "river":
                on_log = False
                current_log = None
                if abs(lane.y - y) < GRID_SIZE / 2:
                    for obs in lane.obstacles:
                        obs_rect = pygame.Rect(obs.x, lane_screen_y, obs.img.get_width(), GRID_SIZE)
                        if crab_rect.colliderect(obs_rect):
                            on_log = True
                            current_log = obs
                            break
                for obs in lane.obstacles:
                    obs.move()
                    obs.draw(win, camera_y)
                if abs(lane.y - y) < GRID_SIZE / 2 and not on_log:
                    game_over = True
                elif current_log:
                    x += current_log.speed

            else:
                for obs in lane.obstacles:
                    obs.move()
                    obs.draw(win, camera_y)

        win.blit(CRAB_IMG, (x, y - camera_y))

        # Draw score text with black outline
        text_surface = SCORE_FONT.render(f"Score: {score}", True, (255, 182, 193))  # LightPink color
        text_outline = SCORE_FONT.render(f"Score: {score}", True, (0, 0, 0))  # Black outline
        outline_thickness = 1
        text_pos = (WIN_WIDTH - text_surface.get_width() - 10, 10)
        for dx in range(-outline_thickness, outline_thickness + 1):
            for dy in range(-outline_thickness, outline_thickness + 1):
                if dx != 0 or dy != 0:  # Avoid drawing outline at the center
                    win.blit(text_outline, (text_pos[0] + dx, text_pos[1] + dy))
        win.blit(text_surface, text_pos)

    else:
        # Play Game Over sound only once
        if not game_over_sound_played:
            pygame.mixer.music.stop()
            pygame.mixer.Sound.play(game_over_sound, 0)  # 0 means no looping
            game_over_sound_played = True

        # Draw background for Game Over screen from image
        win.blit(GAME_OVER_BG, (0, 0))

        font = GAME_FONT
        game_over_text = font.render("GAME prOVER!", True, (255, 0, 0))
        
        # Add dark red outline (1px) for "GAME OVER!"
        outline_thickness = 1
        dark_red_outline = font.render("GAME prOVER!", True, (139, 0, 0))  # Dark Red (#8B0000)
        for dx in range(-outline_thickness, outline_thickness + 1):
            for dy in range(-outline_thickness, outline_thickness + 1):
                if dx != 0 or dy != 0:  # Avoid drawing outline at the center
                    win.blit(dark_red_outline, (WIN_WIDTH // 2 - game_over_text.get_width() // 2 + dx, WIN_HEIGHT // 4 + dy))
        win.blit(game_over_text, (WIN_WIDTH // 2 - game_over_text.get_width() // 2, WIN_HEIGHT // 4))

        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        
        # Add black outline (1px) for "Score: {score}"
        score_outline = font.render(f"Score: {score}", True, (0, 0, 0))  # Black outline
        for dx in range(-outline_thickness, outline_thickness + 1):
            for dy in range(-outline_thickness, outline_thickness + 1):
                if dx != 0 or dy != 0:  # Avoid drawing outline at the center
                    win.blit(score_outline, (WIN_WIDTH // 2 - score_text.get_width() // 2 + dx, WIN_HEIGHT // 2 + 20 + dy))
        win.blit(score_text, (WIN_WIDTH // 2 - score_text.get_width() // 2, WIN_HEIGHT // 2 + 20))

        button_text = font.render("Try Again", True, (255, 255, 255))

        # Increase button size and center it
        btn_width = 300  # Button width
        btn_height = 100  # Button height
        btn_rect = pygame.Rect(WIN_WIDTH // 2 - btn_width // 2, WIN_HEIGHT // 2 + 100, btn_width, btn_height)
        
        # Change button background to LightPink (#FFB6C1) and add dark pink outline (2px)
        pygame.draw.rect(win, (255, 182, 193), btn_rect)  # LightPink background (#FFB6C1)
        pygame.draw.rect(win, (255, 20, 147), btn_rect, 2)  # DarkPink border (#FF1493), 2px thickness

        # Center text inside the button with uniform padding
        text_rect = button_text.get_rect()
        padding = 10  # Uniform padding on all sides
        text_rect.x = btn_rect.x + (btn_rect.width - button_text.get_width()) // 2
        text_rect.y = btn_rect.y + (btn_rect.height - button_text.get_height()) // 2
        win.blit(button_text, (text_rect.x, text_rect.y))

    pygame.display.update()
    clock.tick(60)
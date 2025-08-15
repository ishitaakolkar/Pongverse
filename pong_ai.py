import pygame
import numpy as np
import random
import math
import sys
import os

# --- Settings ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 500
FPS = 60
PADDLE_WIDTH = 12
PADDLE_HEIGHT = 100
BALL_SIZE = 18
PADDLE_SPEED = 7
BALL_SPEED = 7
ELASTICITY = 0.95
SPIN_FACTOR = 0.25
FRICTION = 0.98
FONT_NAME = 'freesansbold.ttf'
WIN_SCORE = 7

# --- Q-Learning Settings ---
STATE_BINS = (12, 12, 6, 6)  # Ball X/Y, Ball VX/VY, Paddle Y
ACTIONS = [0, 1, 2]  # Up, Down, Stay
ALPHA = 0.1
GAMMA = 0.95
EPSILON_START = 1.0
EPSILON_MIN = 0.02
EPSILON_DECAY = 0.998

# --- Initialize pygame ---
pygame.init()
pygame.mixer.init()
os.environ['SDL_VIDEO_CENTERED'] = '1'
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Pong ML')
clock = pygame.time.Clock()
font = pygame.font.Font(FONT_NAME, 32)

# --- Sound Effects ---
def load_sound(name):
    return pygame.mixer.Sound(os.path.join('assets', name))

bounce_sound = load_sound('bounce.wav') if os.path.exists('assets/bounce.wav') else None
score_sound = load_sound('score.wav') if os.path.exists('assets/score.wav') else None
start_sound = load_sound('start.wav') if os.path.exists('assets/start.wav') else None

# --- Utility functions ---
def draw_text(surface, text, size, x, y, color=(255,255,255)):
    font = pygame.font.Font(FONT_NAME, size)
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect()
    rect.center = (x, y)
    surface.blit(text_surface, rect)

# --- Game Objects ---
class Paddle:
    def __init__(self, x, y, is_player=True):
        self.x = x
        self.y = y
        self.width = PADDLE_WIDTH
        self.height = PADDLE_HEIGHT
        self.is_player = is_player
        self.speed = PADDLE_SPEED
        self.vel = 0

    def move(self, direction):
        self.vel = direction * self.speed
        self.y += self.vel
        self.y = max(0, min(SCREEN_HEIGHT - self.height, self.y))

    def draw(self, surface):
        pygame.draw.rect(surface, (255,255,255), pygame.Rect(self.x, int(self.y), self.width, self.height), border_radius=8)

class Ball:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = SCREEN_WIDTH // 2 - BALL_SIZE // 2
        self.y = SCREEN_HEIGHT // 2 - BALL_SIZE // 2
        angle = random.uniform(-0.3, 0.3) * math.pi
        self.vx = BALL_SPEED * random.choice([-1, 1]) * math.cos(angle)
        self.vy = BALL_SPEED * math.sin(angle)
        self.spin = 0

    def move(self):
        self.x += self.vx
        self.y += self.vy
        self.vy *= FRICTION  # Simulate friction/air resistance

    def draw(self, surface):
        pygame.draw.ellipse(surface, (0,255,255), pygame.Rect(int(self.x), int(self.y), BALL_SIZE, BALL_SIZE))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, BALL_SIZE, BALL_SIZE)

# --- Q-Learning AI Agent ---
class QAgent:
    def __init__(self, difficulty='medium'):
        bins = STATE_BINS
        self.q_table = np.zeros(bins + (len(ACTIONS),))  # Discretized Q-table
        self.alpha = ALPHA
        self.gamma = GAMMA
        self.epsilon = EPSILON_START
        self.epsilon_min = EPSILON_MIN
        self.epsilon_decay = EPSILON_DECAY
        self.last_state = None
        self.last_action = None
        self.difficulty = difficulty

    def discretize_state(self, ball, paddle):
        bx = int(ball.x * STATE_BINS[0] / SCREEN_WIDTH)
        by = int(ball.y * STATE_BINS[1] / SCREEN_HEIGHT)
        bvx = int((ball.vx + BALL_SPEED) * STATE_BINS[2] / (2 * BALL_SPEED))
        bvy = int((ball.vy + BALL_SPEED) * STATE_BINS[3] / (2 * BALL_SPEED))
        py = int(paddle.y * STATE_BINS[1] / SCREEN_HEIGHT)
        return (bx, by, bvx, bvy, py)

    def select_action(self, state):
        if random.random() < self.epsilon:
            if self.difficulty == 'easy':
                return random.choice(ACTIONS)
            elif self.difficulty == 'medium':
                # Slightly bias towards correct move but still random
                return random.choice(ACTIONS)
            else:
                return random.choice(ACTIONS)
        else:
            return np.argmax(self.q_table[state])

    def update(self, old_state, action, reward, new_state):
        old_q = self.q_table[old_state + (action,)]
        future_q = np.max(self.q_table[new_state])
        self.q_table[old_state + (action,)] += self.alpha * (reward + self.gamma * future_q - old_q)

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

# --- Game Logic ---
class PongGame:
    def __init__(self):
        self.left_paddle = Paddle(30, SCREEN_HEIGHT//2 - PADDLE_HEIGHT//2, is_player=True)
        self.right_paddle = Paddle(SCREEN_WIDTH - 30 - PADDLE_WIDTH, SCREEN_HEIGHT//2 - PADDLE_HEIGHT//2, is_player=False)
        self.ball = Ball()
        self.player_score = 0
        self.ai_score = 0
        self.agent = None
        self.difficulty = 'medium'
        self.menu = True
        self.running = True

    def set_difficulty(self, diff):
        self.difficulty = diff
        self.agent = QAgent(difficulty=diff)
        self.agent.epsilon = {
            'easy': 0.8,
            'medium': 0.3,
            'hard': 0.05
        }[diff]

    def reset(self):
        self.left_paddle.y = SCREEN_HEIGHT//2 - PADDLE_HEIGHT//2
        self.right_paddle.y = SCREEN_HEIGHT//2 - PADDLE_HEIGHT//2
        self.ball.reset()

    def step_ai(self):
        state = self.agent.discretize_state(self.ball, self.right_paddle)
        action = self.agent.select_action(state)
        if action == 0:
            self.right_paddle.move(-1)
        elif action == 1:
            self.right_paddle.move(1)
        else:
            self.right_paddle.move(0)
        self.agent.last_state = state
        self.agent.last_action = action

    def reward_ai(self, reward):
        new_state = self.agent.discretize_state(self.ball, self.right_paddle)
        self.agent.update(self.agent.last_state, self.agent.last_action, reward, new_state)
        self.agent.decay_epsilon()

    def handle_collisions(self):
        ball_rect = self.ball.get_rect()
        lp_rect = pygame.Rect(self.left_paddle.x, self.left_paddle.y, self.left_paddle.width, self.left_paddle.height)
        rp_rect = pygame.Rect(self.right_paddle.x, self.right_paddle.y, self.right_paddle.width, self.right_paddle.height)

        # Ball hits top/bottom
        if self.ball.y <= 0 or self.ball.y + BALL_SIZE >= SCREEN_HEIGHT:
            self.ball.vy *= -ELASTICITY
            self.ball.vy += random.uniform(-SPIN_FACTOR, SPIN_FACTOR)  # Add spin
            if bounce_sound: bounce_sound.play()

        # Ball hits left paddle
        if ball_rect.colliderect(lp_rect):
            offset = (self.ball.y + BALL_SIZE/2) - (self.left_paddle.y + PADDLE_HEIGHT/2)
            norm_offset = offset / (PADDLE_HEIGHT/2)
            self.ball.vx = abs(self.ball.vx) * ELASTICITY
            self.ball.vy += norm_offset * BALL_SPEED * SPIN_FACTOR
            self.ball.x = self.left_paddle.x + PADDLE_WIDTH + 1
            if bounce_sound: bounce_sound.play()

        # Ball hits right paddle
        if ball_rect.colliderect(rp_rect):
            offset = (self.ball.y + BALL_SIZE/2) - (self.right_paddle.y + PADDLE_HEIGHT/2)
            norm_offset = offset / (PADDLE_HEIGHT/2)
            self.ball.vx = -abs(self.ball.vx) * ELASTICITY
            self.ball.vy += norm_offset * BALL_SPEED * SPIN_FACTOR
            self.ball.x = self.right_paddle.x - BALL_SIZE - 1
            self.reward_ai(1.0)  # Reward for hitting ball
            if bounce_sound: bounce_sound.play()

        # Ball goes past left paddle (AI scores)
        if self.ball.x <= 0:
            self.ai_score += 1
            self.reward_ai(-2.0)
            if score_sound: score_sound.play()
            self.reset()

        # Ball goes past right paddle (Player scores)
        if self.ball.x + BALL_SIZE >= SCREEN_WIDTH:
            self.player_score += 1
            self.reward_ai(2.0)
            if score_sound: score_sound.play()
            self.reset()

    def update(self, player_move):
        # Move paddles
        self.left_paddle.move(player_move)
        self.step_ai()
        # Move ball
        self.ball.move()
        # Handle collisions
        self.handle_collisions()
        # Difficulty: speed up ball after certain score
        if self.player_score + self.ai_score > 0 and (self.player_score + self.ai_score) % 5 == 0:
            self.ball.vx *= 1.08
            self.ball.vy *= 1.08

    def draw(self):
        screen.fill((30,30,30))
        # Center dotted line
        for i in range(0, SCREEN_HEIGHT, 30):
            pygame.draw.line(screen, (90,90,90), (SCREEN_WIDTH//2, i), (SCREEN_WIDTH//2, i+18), 4)
        self.left_paddle.draw(screen)
        self.right_paddle.draw(screen)
        self.ball.draw(screen)
        # Scores
        draw_text(screen, str(self.player_score), 44, SCREEN_WIDTH//2 - 60, 40)
        draw_text(screen, str(self.ai_score), 44, SCREEN_WIDTH//2 + 60, 40)
        # Difficulty
        draw_text(screen, f"Difficulty: {self.difficulty.capitalize()}", 20, SCREEN_WIDTH//2, SCREEN_HEIGHT - 30)
        pygame.display.flip()

    def draw_menu(self):
        screen.fill((20,20,40))
        draw_text(screen, "Pong ML", 64, SCREEN_WIDTH//2, SCREEN_HEIGHT//3)
        draw_text(screen, "Select Difficulty", 32, SCREEN_WIDTH//2, SCREEN_HEIGHT//2-30)
        draw_text(screen, "1: Easy", 28, SCREEN_WIDTH//2, SCREEN_HEIGHT//2+20)
        draw_text(screen, "2: Medium", 28, SCREEN_WIDTH//2, SCREEN_HEIGHT//2+60)
        draw_text(screen, "3: Hard", 28, SCREEN_WIDTH//2, SCREEN_HEIGHT//2+100)
        draw_text(screen, "Press SPACE to Start", 24, SCREEN_WIDTH//2, SCREEN_HEIGHT-60)
        pygame.display.flip()

    def draw_end(self):
        winner = "Player" if self.player_score > self.ai_score else "AI"
        screen.fill((50,20,20))
        draw_text(screen, f"{winner} Wins!", 48, SCREEN_WIDTH//2, SCREEN_HEIGHT//2-40)
        draw_text(screen, f"Player: {self.player_score}  AI: {self.ai_score}", 32, SCREEN_WIDTH//2, SCREEN_HEIGHT//2+10)
        draw_text(screen, "Press R to Restart or Q to Quit", 24, SCREEN_WIDTH//2, SCREEN_HEIGHT//2+70)
        pygame.display.flip()

    def is_game_over(self):
        return self.player_score >= WIN_SCORE or self.ai_score >= WIN_SCORE

# --- Mobile Touch Controls (basic) ---
def get_player_move(paddle):
    move = 0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP: move = -1
            elif event.key == pygame.K_DOWN: move = 1
        elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEMOTION:
            mx, my = pygame.mouse.get_pos()
            if my < paddle.y + PADDLE_HEIGHT//2 - 10:
                move = -1
            elif my > paddle.y + PADDLE_HEIGHT//2 + 10:
                move = 1
        elif event.type == pygame.FINGERDOWN or event.type == pygame.FINGERMOTION:
            try:
                fy = event.y * SCREEN_HEIGHT
                if fy < paddle.y + PADDLE_HEIGHT//2 - 10:
                    move = -1
                elif fy > paddle.y + PADDLE_HEIGHT//2 + 10:
                    move = 1
            except Exception: pass
    return move

# --- Main Loop ---
def main():
    game = PongGame()
    selected_diff = None
    # Menu loop
    while game.menu:
        game.draw_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: selected_diff = 'easy'
                elif event.key == pygame.K_2: selected_diff = 'medium'
                elif event.key == pygame.K_3: selected_diff = 'hard'
                if event.key == pygame.K_SPACE and selected_diff:
                    game.set_difficulty(selected_diff)
                    game.menu = False
                    if start_sound: start_sound.play()
        clock.tick(FPS)
    # Game loop
    while game.running:
        player_move = get_player_move(game.left_paddle)
        game.update(player_move)
        game.draw()
        if game.is_game_over():
            game.draw_end()
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            game.player_score = 0
                            game.ai_score = 0
                            game.reset()
                            break
                        elif event.key == pygame.K_q:
                            pygame.quit(); sys.exit()
                clock.tick(FPS)
        clock.tick(FPS)

if __name__ == '__main__':
    main()
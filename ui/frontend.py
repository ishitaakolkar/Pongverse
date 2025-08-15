from typing import Dict, Optional, Tuple
import pygame
import logging
from dataclasses import dataclass
from ..game.engine import GameEngine, GameConfig, GameState, GameMode

logger = logging.getLogger(__name__)

@dataclass
class UIConfig:
    """Configuration for UI elements."""
    window_width: int = 960
    window_height: int = 600
    fps: int = 60
    font_size: int = 32
    paddle_color: Tuple[int, int, int] = (255, 255, 255)
    ball_color: Tuple[int, int, int] = (255, 255, 255)
    bg_color: Tuple[int, int, int] = (10, 10, 15)
    accent_color: Tuple[int, int, int] = (0, 255, 255)

class PongUI:
    """
    Pygame-based UI renderer for Pongverse.
    
    Handles window management, rendering, and input processing
    for the native desktop version of the game.
    """
    
    def __init__(self, game_engine: GameEngine, config: UIConfig):
        pygame.init()
        pygame.display.set_caption("Pongverse")
        
        self.game = game_engine
        self.config = config
        self.screen = pygame.display.set_mode(
            (config.window_width, config.window_height)
        )
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, config.font_size)
        
        # Load sounds
        self.sounds = self._load_sounds()
        self.sound_enabled = True
        
    def _load_sounds(self) -> Dict[str, Optional[pygame.mixer.Sound]]:
        """Load game sound effects."""
        sounds = {}
        try:
            sounds['hit'] = pygame.mixer.Sound('assets/hit.wav')
            sounds['wall'] = pygame.mixer.Sound('assets/wall.wav')
            sounds['score'] = pygame.mixer.Sound('assets/score.wav')
        except Exception as e:
            logger.warning(f"Could not load sounds: {e}")
            return {}
        return sounds
        
    def draw_game(self, state: GameState) -> None:
        """Render current game state."""
        # Clear screen
        self.screen.fill(self.config.bg_color)
        
        # Draw center line
        pygame.draw.line(
            self.screen,
            (50, 50, 50),
            (self.config.window_width // 2, 0),
            (self.config.window_width // 2, self.config.window_height),
            2
        )
        
        # Draw paddles
        pygame.draw.rect(
            self.screen,
            self.config.paddle_color,
            pygame.Rect(
                state.left_paddle_pos,
                state.ball_pos[1],
                self.game.config.paddle_width,
                self.game.config.paddle_height
            )
        )
        
        pygame.draw.rect(
            self.screen,
            self.config.paddle_color,
            pygame.Rect(
                state.right_paddle_pos,
                state.ball_pos[1],
                self.game.config.paddle_width,
                self.game.config.paddle_height
            )
        )
        
        # Draw ball
        pygame.draw.rect(
            self.screen,
            self.config.ball_color,
            pygame.Rect(
                state.ball_pos[0],
                state.ball_pos[1],
                self.game.config.ball_size,
                self.game.config.ball_size
            )
        )
        
        # Draw scores
        player_score = self.font.render(
            str(state.player_score),
            True,
            self.config.accent_color
        )
        ai_score = self.font.render(
            str(state.ai_score),
            True,
            self.config.accent_color
        )
        
        self.screen.blit(
            player_score,
            (self.config.window_width // 4, 20)
        )
        self.screen.blit(
            ai_score,
            (3 * self.config.window_width // 4, 20)
        )
        
        pygame.display.flip()
        
    def handle_input(self) -> bool:
        """Process input events. Returns False if game should quit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_p:
                    self.game.state.is_paused = not self.game.state.is_paused
                elif event.key == pygame.K_m:
                    self.sound_enabled = not self.sound_enabled
                    
            elif event.type == pygame.MOUSEMOTION:
                # Update player paddle position
                if not self.game.state.is_paused:
                    mouse_y = event.pos[1]
                    self.game.move_paddle(
                        True,
                        mouse_y - self.game.state.left_paddle_pos
                    )
                    
        return True
        
    def play_sound(self, sound_name: str) -> None:
        """Play a sound effect if enabled."""
        if self.sound_enabled and sound_name in self.sounds:
            self.sounds[sound_name].play()
            
    def run(self) -> None:
        """Main game loop."""
        running = True
        while running:
            running = self.handle_input()
            
            if not self.game.state.is_paused:
                self.game.update()
                
            self.draw_game(self.game.state)
            self.clock.tick(self.config.fps)
            
        pygame.quit()

# TODO: Add support for custom themes/skins
# TODO: Implement replay viewer

def toggle_visual_effects(self) -> None:
    """Toggle visual effects on/off."""
    if not hasattr(self, 'visual_effects_enabled'):
        self.visual_effects_enabled = True
    else:
        self.visual_effects_enabled = not self.visual_effects_enabled

# Example usage: Call self.toggle_visual_effects() when a key is pressed (e.g., 'v')
# You can use self.visual_effects_enabled in draw_game to enable/disable effects.
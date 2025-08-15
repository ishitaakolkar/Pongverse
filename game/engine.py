from dataclasses import dataclass
from typing import Tuple, Optional, Dict
import numpy as np
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class GameMode(Enum):
    SINGLE_PLAYER = "single"
    MULTIPLAYER = "multi"
    AI_TRAINING = "training"

@dataclass
class GameConfig:
    """Game configuration parameters."""
    width: int = 960
    height: int = 600
    paddle_width: int = 16
    paddle_height: int = 100
    ball_size: int = 16
    base_speed: float = 7.0
    max_speed: float = 15.0
    speed_increment: float = 1.04
    winning_score: int = 10

@dataclass
class GameState:
    """Represents the current state of the game."""
    ball_pos: Tuple[float, float]
    ball_vel: Tuple[float, float]
    left_paddle_pos: float
    right_paddle_pos: float
    player_score: int
    ai_score: int
    game_mode: GameMode
    is_paused: bool = False
    ball_speed: float = 7.0

class PhysicsEngine:
    """Handles game physics calculations."""
    
    def __init__(self, config: GameConfig):
        self.config = config
    
    def update_ball_position(self, state: GameState) -> Tuple[float, float]:
        """Update ball position based on velocity."""
        if state.is_paused:
            return state.ball_pos
            
        new_x = state.ball_pos[0] + state.ball_vel[0]
        new_y = state.ball_pos[1] + state.ball_vel[1]
        return (new_x, new_y)
    
    def check_wall_collision(self, pos: Tuple[float, float]) -> bool:
        """Check if ball collides with top/bottom walls."""
        return pos[1] <= 0 or pos[1] + self.config.ball_size >= self.config.height
    
    def check_paddle_collision(
        self,
        ball_pos: Tuple[float, float],
        paddle_pos: float,
        is_left: bool
    ) -> bool:
        """Check if ball collides with a paddle."""
        paddle_x = (
            self.config.paddle_width 
            if is_left else 
            self.config.width - 2 * self.config.paddle_width
        )
        
        return (
            ball_pos[0] < paddle_x + self.config.paddle_width
            and ball_pos[0] + self.config.ball_size > paddle_x
            and ball_pos[1] < paddle_pos + self.config.paddle_height
            and ball_pos[1] + self.config.ball_size > paddle_pos
        )

class GameEngine:
    """
    Main game engine class handling game state and logic.
    
    Coordinates physics, scoring, and game flow while remaining
    independent of rendering and input handling.
    """
    
    def __init__(self, config: GameConfig):
        self.config = config
        self.physics = PhysicsEngine(config)
        self.reset_game()
        
    def reset_game(self) -> None:
        """Reset game to initial state."""
        self.state = GameState(
            ball_pos=(self.config.width/2, self.config.height/2),
            ball_vel=(self.config.base_speed, 0),
            left_paddle_pos=self.config.height/2 - self.config.paddle_height/2,
            right_paddle_pos=self.config.height/2 - self.config.paddle_height/2,
            player_score=0,
            ai_score=0,
            game_mode=GameMode.SINGLE_PLAYER,
            ball_speed=self.config.base_speed
        )
        
    def update(self) -> None:
        """Update game state for one frame."""
        if self.state.is_paused:
            return
            
        # Update ball position
        new_pos = self.physics.update_ball_position(self.state)
        
        # Handle collisions
        if self.physics.check_wall_collision(new_pos):
            self.state.ball_vel = (
                self.state.ball_vel[0],
                -self.state.ball_vel[1]
            )
            new_pos = self.physics.update_ball_position(self.state)
            
        # Paddle collisions
        for is_left in (True, False):
            paddle_pos = (
                self.state.left_paddle_pos 
                if is_left else 
                self.state.right_paddle_pos
            )
            
            if self.physics.check_paddle_collision(new_pos, paddle_pos, is_left):
                # Calculate deflection angle based on hit position
                hit_pos = (new_pos[1] - paddle_pos) / self.config.paddle_height
                angle = (hit_pos - 0.5) * np.pi / 3
                
                # Update velocity with increased speed
                speed = min(
                    self.state.ball_speed * self.config.speed_increment,
                    self.config.max_speed
                )
                self.state.ball_speed = speed
                self.state.ball_vel = (
                    -speed * np.cos(angle) if is_left else speed * np.cos(angle),
                    speed * np.sin(angle)
                )
                new_pos = self.physics.update_ball_position(self.state)
                
        # Scoring
        if new_pos[0] <= 0:
            self.state.ai_score += 1
            self._reset_ball(serve_left=True)
        elif new_pos[0] + self.config.ball_size >= self.config.width:
            self.state.player_score += 1
            self._reset_ball(serve_left=False)
        else:
            self.state.ball_pos = new_pos
            
    def _reset_ball(self, serve_left: bool) -> None:
        """Reset ball position after scoring."""
        self.state.ball_pos = (self.config.width/2, self.config.height/2)
        self.state.ball_speed = self.config.base_speed
        angle = np.random.uniform(-np.pi/4, np.pi/4)
        self.state.ball_vel = (
            -self.config.base_speed * np.cos(angle) if serve_left
            else self.config.base_speed * np.cos(angle),
            self.config.base_speed * np.sin(angle)
        )
        
    def move_paddle(self, is_left: bool, amount: float) -> None:
        """Move a paddle while keeping it within bounds."""
        if is_left:
            new_pos = self.state.left_paddle_pos + amount
            self.state.left_paddle_pos = np.clip(
                new_pos,
                0,
                self.config.height - self.config.paddle_height
            )
        else:
            new_pos = self.state.right_paddle_pos + amount
            self.state.right_paddle_pos = np.clip(
                new_pos,
                0,
                self.config.height - self.config.paddle_height
            )
            
    def get_game_state(self) -> Dict:
        """Return current game state for AI or rendering."""
        return {
            'ball_pos': self.state.ball_pos,
            'ball_vel': self.state.ball_vel,
            'left_paddle': self.state.left_paddle_pos,
            'right_paddle': self.state.right_paddle_pos,
            'scores': (self.state.player_score, self.state.ai_score),
            'ball_speed': self.state.ball_speed
        }
        
    def is_game_over(self) -> bool:
        """Check if game is over."""
        return (
            self.state.player_score >= self.config.winning_score
            or self.state.ai_score >= self.config.winning_score
        )

# TODO: Add replay system for game state recording
# TODO: Implement more sophisticated physics (spin, friction)
# Power-up types
class PowerUpType(Enum):
    SPEED_BOOST = "speed_boost"
    PADDLE_SIZE = "paddle_size"
    MULTI_BALL = "multi_ball"

@dataclass
class PowerUp:
    """Represents a power-up on the field."""
    type: PowerUpType
    pos: Tuple[float, float]
    active: bool = True
    duration: int = 300  # frames

class PowerUpManager:
    """Handles spawning and applying power-ups."""
    def __init__(self, config: GameConfig):
        self.config = config
        self.active_powerups: Dict[str, PowerUp] = {}

    def spawn_powerup(self) -> Optional[PowerUp]:
        # Randomly spawn a power-up in the field
        powerup_type = np.random.choice(list(PowerUpType))
        pos = (
            np.random.uniform(self.config.width * 0.25, self.config.width * 0.75),
            np.random.uniform(self.config.height * 0.2, self.config.height * 0.8)
        )
        powerup = PowerUp(type=powerup_type, pos=pos)
        self.active_powerups[str(pos)] = powerup
        return powerup

    def check_collision(self, ball_pos: Tuple[float, float]) -> Optional[PowerUp]:
        for key, powerup in self.active_powerups.items():
            if powerup.active:
                px, py = powerup.pos
                if (
                    abs(ball_pos[0] - px) < 20 and
                    abs(ball_pos[1] - py) < 20
                ):
                    powerup.active = False
                    return powerup
        return None

    def update(self):
        # Remove expired power-ups
        for powerup in list(self.active_powerups.values()):
            if not powerup.active:
                continue
            powerup.duration -= 1
            if powerup.duration <= 0:
                powerup.active = False

# Extend GameEngine for power-ups and special modes
class GameEngineWithPowerUps(GameEngine):
    def __init__(self, config: GameConfig):
        super().__init__(config)
        self.powerup_manager = PowerUpManager(config)
        self.special_mode_active = False

    def update(self) -> None:
        super().update()
        # Randomly spawn power-ups
        if np.random.rand() < 0.005:
            self.powerup_manager.spawn_powerup()
        self.powerup_manager.update()
        # Check for power-up collision
        powerup = self.powerup_manager.check_collision(self.state.ball_pos)
        if powerup:
            self.apply_powerup(powerup)

    def apply_powerup(self, powerup: PowerUp):
        if powerup.type == PowerUpType.SPEED_BOOST:
            self.state.ball_speed = min(self.state.ball_speed * 1.5, self.config.max_speed)
        elif powerup.type == PowerUpType.PADDLE_SIZE:
            self.config.paddle_height = min(self.config.paddle_height * 1.5, self.config.height / 2)
        elif powerup.type == PowerUpType.MULTI_BALL:
            # Example: activate special mode
            self.special_mode_active = True

    def get_game_state(self) -> Dict:
        state = super().get_game_state()
        state['powerups'] = [
            {'type': p.type.value, 'pos': p.pos, 'active': p.active}
            for p in self.powerup_manager.active_powerups.values()
        ]
        state['special_mode'] = self.special_mode_active
        return state

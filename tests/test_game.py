import pytest
from pongverse.game.engine import GameEngine, GameConfig, GameState, GameMode
import numpy as np

@pytest.fixture
def game():
    """Create a fresh game instance for each test."""
    config = GameConfig()
    return GameEngine(config)

def test_paddle_movement(game):
    """Test paddle movement and bounds checking."""
    initial_pos = game.state.left_paddle_pos
    
    # Move up
    game.move_paddle(True, -50)
    assert game.state.left_paddle_pos < initial_pos
    
    # Move down
    game.move_paddle(True, 100)
    assert game.state.left_paddle_pos > initial_pos
    
    # Test upper bound
    game.move_paddle(True, -1000)
    assert game.state.left_paddle_pos == 0
    
    # Test lower bound
    game.move_paddle(True, 1000)
    assert game.state.left_paddle_pos == game.config.height - game.config.paddle_height

def test_ball_physics(game):
    """Test ball movement and collision physics."""
    initial_speed = np.sqrt(
        game.state.ball_vel[0]**2 + 
        game.state.ball_vel[1]**2
    )
    
    # Let ball move for a few frames
    for _ in range(10):
        game.update()
    
    # Verify speed remains constant without collisions
    current_speed = np.sqrt(
        game.state.ball_vel[0]**2 + 
        game.state.ball_vel[1]**2
    )
    assert abs(current_speed - initial_speed) < 0.001

def test_scoring(game):
    """Test score tracking."""
    # Move ball past right paddle
    game.state.ball_pos = (
        game.config.width + 10,
        game.config.height / 2
    )
    game.update()
    assert game.state.player_score == 1
    assert game.state.ball_pos[0] == game.config.width / 2
    
    # Move ball past left paddle
    game.state.ball_pos = (-10, game.config.height / 2)
    game.update()
    assert game.state.ai_score == 1

def test_paddle_collision(game):
    """Test paddle-ball collision detection and response."""
    # Position ball near left paddle
    game.state.ball_pos = (
        game.config.paddle_width + 5,
        game.state.left_paddle_pos + game.config.paddle_height / 2
    )
    game.state.ball_vel = (-5, 0)
    
    # Update should detect collision
    game.update()
    assert game.state.ball_vel[0] > 0  # Ball should bounce

def test_game_over(game):
    """Test game over condition."""
    game.state.player_score = game.config.winning_score - 1
    assert not game.is_game_over()
    
    game.state.player_score = game.config.winning_score
    assert game.is_game_over()

# TODO: Add tests for AI behavior
# TODO: Test different difficulty levels
def test_ai_paddle_tracks_ball(game):
    """Test that AI paddle moves towards the ball."""
    # Place ball above AI paddle
    game.state.ball_pos = (game.config.width / 2, 10)
    ai_initial = game.state.right_paddle_pos
    game.update()
    assert game.state.right_paddle_pos < ai_initial or game.state.right_paddle_pos == 0

    # Place ball below AI paddle
    game.state.ball_pos = (game.config.width / 2, game.config.height - 10)
    ai_initial = game.state.right_paddle_pos
    game.update()
    assert game.state.right_paddle_pos > ai_initial or game.state.right_paddle_pos == game.config.height - game.config.paddle_height

def test_ai_difficulty_easy(game):
    """Test AI behavior on easy difficulty."""
    game.set_mode(GameMode.AI_EASY)
    game.state.ball_pos = (game.config.width / 2, 10)
    ai_initial = game.state.right_paddle_pos
    game.update()
    # Easy AI should move slowly
    assert abs(game.state.right_paddle_pos - ai_initial) <= game.config.ai_easy_speed

def test_ai_difficulty_hard(game):
    """Test AI behavior on hard difficulty."""
    game.set_mode(GameMode.AI_HARD)
    game.state.ball_pos = (game.config.width / 2, game.config.height - 10)
    ai_initial = game.state.right_paddle_pos
    game.update()
    # Hard AI should move faster
    assert abs(game.state.right_paddle_pos - ai_initial) >= game.config.ai_hard_speed

def test_ai_paddle_bounds(game):
    """Test AI paddle does not move out of bounds."""
    game.state.ball_pos = (game.config.width / 2, -100)
    for _ in range(5):
        game.update()
    assert 0 <= game.state.right_paddle_pos <= game.config.height - game.config.paddle_height
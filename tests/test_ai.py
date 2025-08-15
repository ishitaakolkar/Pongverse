import pytest
import torch
import numpy as np
from pongverse.ai.dqn_agent import DQNAgent, DQNConfig, PrioritizedReplayBuffer

@pytest.fixture
def agent():
    """Create a fresh DQN agent for each test."""
    config = DQNConfig()
    return DQNAgent(config)

@pytest.fixture
def replay_buffer():
    """Create a fresh replay buffer for each test."""
    return PrioritizedReplayBuffer(1000, 0.6)

def test_agent_initialization(agent):
    """Test proper agent initialization."""
    assert agent.policy_net is not None
    assert agent.target_net is not None
    assert agent.memory is not None
    assert 0 <= agent.epsilon <= 1

def test_action_selection(agent):
    """Test action selection mechanism."""
    state = np.random.random(agent.config.state_dim)
    action = agent.select_action(state)
    assert 0 <= action < agent.config.action_dim

def test_experience_replay(replay_buffer):
    """Test experience replay buffer operations."""
    # Add some experiences
    for _ in range(10):
        state = np.random.random(6)
        next_state = np.random.random(6)
        replay_buffer.push(
            state,
            0,
            1.0,
            next_state,
            False
        )
    
    # Sample batch
    batch, indices, weights = replay_buffer.sample(5, 0.4)
    assert len(batch) == 5
    assert len(indices) == 5
    assert len(weights) == 5

def test_model_save_load(agent, tmp_path):
    """Test model checkpoint operations."""
    # Save model
    save_path = tmp_path / "model.pt"
    agent.save_model(str(save_path))
    assert save_path.exists()
    
    # Load model
    new_agent = DQNAgent(agent.config)
    new_agent.load_model(str(save_path))
    
    # Compare weights
    for p1, p2 in zip(agent.policy_net.parameters(),
                      new_agent.policy_net.parameters()):
        assert torch.allclose(p1, p2)

def test_optimization_step(agent):
    """Test single optimization step."""
    # Fill buffer with some experiences
    for _ in range(agent.config.batch_size):
        state = np.random.random(agent.config.state_dim)
        next_state = np.random.random(agent.config.state_dim)
        agent.memory.push(
            state,
            0,
            1.0,
            next_state,
            False
        )
    
    # Perform optimization
    loss = agent.optimize_model()
    assert isinstance(loss, float)
    assert not np.isnan(loss)

def test_epsilon_decay(agent):
    """Test epsilon-greedy exploration decay."""
    initial_epsilon = agent.epsilon
    
    # Simulate some training steps
    for _ in range(100):
        state = np.random.random(agent.config.state_dim)
        agent.select_action(state)
        agent.optimize_model()
    
    assert agent.epsilon < initial_epsilon
    assert agent.epsilon >= agent.config.epsilon_end
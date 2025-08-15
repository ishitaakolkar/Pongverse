"""
Deep Q-Network Agent implementation for Pongverse.

This module implements a Double DQN with Prioritized Experience Replay
for the AI paddle control in Pongverse.

Author: @ishitaakolkar
Date: 2025-08-15
"""

from typing import Tuple, List, Optional, Dict
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from dataclasses import dataclass
from collections import namedtuple
import random
import logging
from torch.utils.tensorboard import SummaryWriter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type definitions
Transition = namedtuple('Transition', 
    ['state', 'action', 'reward', 'next_state', 'done'])
State = np.ndarray
Action = int

@dataclass
class DQNConfig:
    """Configuration for DQN hyperparameters."""
    state_dim: int = 6  # ball_x, ball_y, ball_vx, ball_vy, paddle_y, paddle_vy
    action_dim: int = 3  # up, stay, down
    hidden_dim: int = 128
    learning_rate: float = 0.001
    gamma: float = 0.99
    buffer_size: int = 100000
    batch_size: int = 64
    target_update: int = 1000
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay: float = 0.995
    priority_alpha: float = 0.6
    priority_beta: float = 0.4
    priority_epsilon: float = 1e-6

class PrioritizedReplayBuffer:
    """Implements prioritized experience replay for more efficient learning."""
    
    def __init__(self, capacity: int, alpha: float):
        self.capacity = capacity
        self.alpha = alpha
        self.priorities = np.zeros((capacity,), dtype=np.float32)
        self.buffer: List[Transition] = []
        self.position = 0
        
    def push(self, *args) -> None:
        """Save a transition with maximum priority."""
        max_priority = max(self.priorities) if self.buffer else 1.0
        
        if len(self.buffer) < self.capacity:
            self.buffer.append(Transition(*args))
        else:
            self.buffer[self.position] = Transition(*args)
        
        self.priorities[self.position] = max_priority
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size: int, beta: float) -> Tuple[List[Transition], np.ndarray, np.ndarray]:
        """Sample a batch of transitions based on their priorities."""
        if len(self.buffer) == 0:
            raise ValueError("Cannot sample from empty buffer")
            
        priorities = self.priorities[:len(self.buffer)]
        probabilities = priorities ** self.alpha
        probabilities /= probabilities.sum()
        
        indices = np.random.choice(len(self.buffer), batch_size, p=probabilities)
        weights = (len(self.buffer) * probabilities[indices]) ** (-beta)
        weights /= weights.max()
        
        batch = [self.buffer[idx] for idx in indices]
        return batch, indices, weights
    
    def update_priorities(self, indices: np.ndarray, priorities: np.ndarray) -> None:
        """Update priorities for sampled transitions."""
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority

class DQNetwork(nn.Module):
    """Neural network architecture for DQN."""
    
    def __init__(self, config: DQNConfig):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(config.state_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Linear(config.hidden_dim, config.action_dim)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)

class DQNAgent:
    """
    Double DQN agent with prioritized experience replay.
    
    Implements the AI paddle control using advanced deep reinforcement learning
    techniques for improved performance and stability.
    """
    
    def __init__(self, config: DQNConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Networks
        self.policy_net = DQNetwork(config).to(self.device)
        self.target_net = DQNetwork(config).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        
        # Optimizer
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=config.learning_rate)
        
        # Replay buffer
        self.memory = PrioritizedReplayBuffer(
            config.buffer_size, 
            config.priority_alpha
        )
        
        # Training parameters
        self.epsilon = config.epsilon_start
        self.steps = 0
        
    def select_action(self, state: State) -> Action:
        """Select an action using epsilon-greedy policy."""
        if random.random() < self.epsilon:
            return random.randrange(self.config.action_dim)
            
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.policy_net(state_tensor)
            return q_values.max(1)[1].item()
    
    def optimize_model(self) -> float:
        """Perform one step of optimization on the DQN."""
        if len(self.memory.buffer) < self.config.batch_size:
            return 0.0
            
        # Sample batch with priorities
        batch, indices, weights = self.memory.sample(
            self.config.batch_size,
            self.config.priority_beta
        )
        
        # Prepare batch tensors
        state_batch = torch.FloatTensor([t.state for t in batch]).to(self.device)
        action_batch = torch.LongTensor([t.action for t in batch]).to(self.device)
        reward_batch = torch.FloatTensor([t.reward for t in batch]).to(self.device)
        next_state_batch = torch.FloatTensor([t.next_state for t in batch]).to(self.device)
        done_batch = torch.FloatTensor([t.done for t in batch]).to(self.device)
        
        # Double Q-learning update
        with torch.no_grad():
            next_actions = self.policy_net(next_state_batch).max(1)[1].unsqueeze(1)
            next_state_values = self.target_net(next_state_batch).gather(1, next_actions)
            expected_q_values = reward_batch + (1 - done_batch) * self.config.gamma * next_state_values
        
        # Compute loss with importance sampling weights
        current_q_values = self.policy_net(state_batch).gather(1, action_batch.unsqueeze(1))
        td_errors = (expected_q_values - current_q_values).abs()
        loss = (torch.FloatTensor(weights).to(self.device) * F.smooth_l1_loss(
            current_q_values, 
            expected_q_values,
            reduction='none'
        )).mean()
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()
        
        # Update priorities
        self.memory.update_priorities(
            indices,
            (td_errors + self.config.priority_epsilon).detach().cpu().numpy()
        )
        
        # Update target network
        if self.steps % self.config.target_update == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
            
        # Decay epsilon
        self.epsilon = max(
            self.config.epsilon_end,
            self.epsilon * self.config.epsilon_decay
        )
        
        self.steps += 1
        return loss.item()
    
    def save_model(self, path: str) -> None:
        """Save model checkpoint."""
        torch.save({
            'policy_net': self.policy_net.state_dict(),
            'target_net': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'steps': self.steps,
            'config': self.config
        }, path)
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str) -> None:
        """Load model checkpoint."""
        try:
            checkpoint = torch.load(path)
            self.policy_net.load_state_dict(checkpoint['policy_net'])
            self.target_net.load_state_dict(checkpoint['target_net'])
            self.optimizer.load_state_dict(checkpoint['optimizer'])
            self.epsilon = checkpoint['epsilon']
            self.steps = checkpoint['steps']
            logger.info(f"Model loaded from {path}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

# TODO: Add support for different network architectures
# TODO: Implement Dueling DQN variant
class DQNAgent:
    # ... (rest of the class unchanged)

    def __init__(self, config: DQNConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy_net = DQNetwork(config).to(self.device)
        self.target_net = DQNetwork(config).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=config.learning_rate)
        self.memory = PrioritizedReplayBuffer(config.buffer_size, config.priority_alpha)
        self.epsilon = config.epsilon_start
        self.steps = 0
        self.writer = SummaryWriter()  # TensorBoard writer

    def optimize_model(self) -> float:
        if len(self.memory.buffer) < self.config.batch_size:
            return 0.0
        batch, indices, weights = self.memory.sample(self.config.batch_size, self.config.priority_beta)
        state_batch = torch.FloatTensor([t.state for t in batch]).to(self.device)
        action_batch = torch.LongTensor([t.action for t in batch]).to(self.device)
        reward_batch = torch.FloatTensor([t.reward for t in batch]).to(self.device)
        next_state_batch = torch.FloatTensor([t.next_state for t in batch]).to(self.device)
        done_batch = torch.FloatTensor([t.done for t in batch]).to(self.device)
        with torch.no_grad():
            next_actions = self.policy_net(next_state_batch).max(1)[1].unsqueeze(1)
            next_state_values = self.target_net(next_state_batch).gather(1, next_actions)
            expected_q_values = reward_batch + (1 - done_batch) * self.config.gamma * next_state_values
        current_q_values = self.policy_net(state_batch).gather(1, action_batch.unsqueeze(1))
        td_errors = (expected_q_values - current_q_values).abs()
        loss = (torch.FloatTensor(weights).to(self.device) * F.smooth_l1_loss(
            current_q_values, 
            expected_q_values,
            reduction='none'
        )).mean()
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()
        self.memory.update_priorities(indices, (td_errors + self.config.priority_epsilon).detach().cpu().numpy())
        if self.steps % self.config.target_update == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
        self.epsilon = max(self.config.epsilon_end, self.epsilon * self.config.epsilon_decay)
        self.steps += 1

        # TensorBoard logging
        self.writer.add_scalar("Loss", loss.item(), self.steps)
        self.writer.add_scalar("Epsilon", self.epsilon, self.steps)
        self.writer.add_scalar("Buffer Size", len(self.memory.buffer), self.steps)

        return loss.item()

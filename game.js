// Pong ML - Clear Vision Edition
const canvas = document.getElementById('pongCanvas');
const ctx = canvas.getContext('2d');
const menu = document.getElementById('menu');
const gameScreen = document.getElementById('game');
const endScreen = document.getElementById('end');
const scoreDisplay = document.getElementById('scoreDisplay');
const difficultyDisplay = document.getElementById('difficultyDisplay');
const aiDisplay = document.getElementById('aiDisplay');
const smartBarFill = document.getElementById('smartBarFill');

// Settings and Constants
const GAME_W = 960, GAME_H = 600;
const PADDLE_W = 16, PADDLE_H = 100;
const BALL_SIZE = 16;
const BASE_SPEED = 7;
const MAX_SPEED = 15;
const SPEED_INC = 1.04;

// Game State
let game = {
  running: false,
  paused: false,
  difficulty: 'medium',
  aiMode: 'dqn',
  soundOn: true,
  visualEffects: false,
  smartness: 40,
  playerScore: 0,
  aiScore: 0,
  ball: {
    x: GAME_W/2,
    y: GAME_H/2,
    vx: BASE_SPEED,
    vy: 0,
    speed: BASE_SPEED
  },
  leftPaddle: {
    x: 30,
    y: GAME_H/2 - PADDLE_H/2
  },
  rightPaddle: {
    x: GAME_W - 30 - PADDLE_W,
    y: GAME_H/2 - PADDLE_H/2
  }
};

// Initialize Controls
const playBtn = document.getElementById('playBtn');
const playAgainBtn = document.getElementById('playAgainBtn');
const backMenuBtn = document.getElementById('backMenuBtn');
const pauseBtn = document.getElementById('pauseBtn');
const resetBtn = document.getElementById('resetBtn');
const soundBtn = document.getElementById('soundBtn');
const soundToggle = document.getElementById('soundToggle');
const effectsToggle = document.getElementById('effectsToggle');
const helpBtn = document.getElementById('helpBtn');
const closeHelp = document.getElementById('closeHelp');
const difficultySelector = document.getElementById('difficulty');
const aiModeSelector = document.getElementById('aiMode');

// Audio Elements
const bgMusic = document.getElementById('bgMusic');
const hitSound = document.getElementById('hitSound');
const wallSound = document.getElementById('wallSound');
const scoreSound = document.getElementById('scoreSound');

function resetGame() {
  game.ball = {
    x: GAME_W/2,
    y: GAME_H/2,
    vx: BASE_SPEED * (Math.random() > 0.5 ? 1 : -1),
    vy: (Math.random() * 2 - 1) * BASE_SPEED/2,
    speed: BASE_SPEED
  };
  game.leftPaddle.y = GAME_H/2 - PADDLE_H/2;
  game.rightPaddle.y = GAME_H/2 - PADDLE_H/2;
  game.playerScore = 0;
  game.aiScore = 0;
  game.smartness = game.aiMode === "dqn" ? 50 : 30;
  updateHUD();
}

function updateHUD() {
  scoreDisplay.innerHTML = `<span style="color:#fff">Player: ${game.playerScore} | AI: ${game.aiScore}</span>`;
  difficultyDisplay.textContent = `Difficulty: ${game.difficulty}`;
  aiDisplay.textContent = `AI: ${game.aiMode.toUpperCase()}`;
  smartBarFill.style.width = `${(game.smartness/100)*100}%`;
}

function drawGame() {
  // Clear canvas
  ctx.fillStyle = '#0a0a0f';
  ctx.fillRect(0, 0, GAME_W, GAME_H);

  // Draw center line
  ctx.strokeStyle = '#333';
  ctx.setLineDash([10, 15]);
  ctx.beginPath();
  ctx.moveTo(GAME_W/2, 0);
  ctx.lineTo(GAME_W/2, GAME_H);
  ctx.stroke();
  ctx.setLineDash([]);

  // Draw paddles (solid white)
  ctx.fillStyle = '#fff';
  ctx.fillRect(game.leftPaddle.x, game.leftPaddle.y, PADDLE_W, PADDLE_H);
  ctx.fillRect(game.rightPaddle.x, game.rightPaddle.y, PADDLE_W, PADDLE_H);

  // Draw ball (solid white)
  ctx.fillStyle = '#fff';
  ctx.fillRect(game.ball.x, game.ball.y, BALL_SIZE, BALL_SIZE);

  // Optional visual effects
  if (game.visualEffects) {
    // Minimal paddle highlight on hit
    if (game.ball.vx < 0) {
      ctx.strokeStyle = '#0ff4';
      ctx.strokeRect(game.rightPaddle.x, game.rightPaddle.y, PADDLE_W, PADDLE_H);
    } else {
      ctx.strokeStyle = '#0ff4';
      ctx.strokeRect(game.leftPaddle.x, game.leftPaddle.y, PADDLE_W, PADDLE_H);
    }
  }
}

function updateGame() {
  // Ball movement
  game.ball.x += game.ball.vx;
  game.ball.y += game.ball.vy;

  // Wall collisions
  if (game.ball.y <= 0 || game.ball.y + BALL_SIZE >= GAME_H) {
    game.ball.vy *= -1;
    if (game.soundOn) wallSound.play();
  }

  // Paddle collisions
  if (checkCollision(game.ball, game.leftPaddle)) {
    handlePaddleHit(game.leftPaddle);
  }
  if (checkCollision(game.ball, game.rightPaddle)) {
    handlePaddleHit(game.rightPaddle);
  }

  // Scoring
  if (game.ball.x <= 0) {
    game.aiScore++;
    resetBall();
    if (game.soundOn) scoreSound.play();
  }
  if (game.ball.x + BALL_SIZE >= GAME_W) {
    game.playerScore++;
    resetBall();
    if (game.soundOn) scoreSound.play();
  }

  // AI Movement
  updateAI();
  updateHUD();

  // Check for game end
  if (game.playerScore >= 10 || game.aiScore >= 10) {
    endGame();
  }
}

function checkCollision(ball, paddle) {
  return ball.x < paddle.x + PADDLE_W &&
         ball.x + BALL_SIZE > paddle.x &&
         ball.y < paddle.y + PADDLE_H &&
         ball.y + BALL_SIZE > paddle.y;
}

function handlePaddleHit(paddle) {
  // Reverse ball direction
  game.ball.vx *= -1;

  // Add spin based on where the ball hits the paddle
  const hitPos = (game.ball.y + BALL_SIZE/2) - (paddle.y + PADDLE_H/2);
  game.ball.vy = (hitPos / (PADDLE_H/2)) * game.ball.speed;

  // Increase speed
  game.ball.speed = Math.min(game.ball.speed * SPEED_INC, MAX_SPEED);
  const angle = Math.atan2(game.ball.vy, game.ball.vx);
  game.ball.vx = Math.cos(angle) * game.ball.speed;
  game.ball.vy = Math.sin(angle) * game.ball.speed;

  if (game.soundOn) hitSound.play();
}

function resetBall() {
  game.ball.x = GAME_W/2;
  game.ball.y = GAME_H/2;
  game.ball.speed = BASE_SPEED;
  const angle = (Math.random() * 0.5 - 0.25) * Math.PI;
  game.ball.vx = game.ball.speed * (game.ball.x < GAME_W/2 ? 1 : -1) * Math.cos(angle);
  game.ball.vy = game.ball.speed * Math.sin(angle);
}

function updateAI() {
  const paddleCenter = game.rightPaddle.y + PADDLE_H/2;
  const ballCenter = game.ball.y + BALL_SIZE/2;
  
  // AI difficulty affects reaction time and accuracy
  let moveSpeed = 8;
  if (game.difficulty === 'easy') moveSpeed = 6;
  if (game.difficulty === 'hard') moveSpeed = 10;

  if (Math.abs(paddleCenter - ballCenter) > 10) {
    if (paddleCenter < ballCenter) {
      game.rightPaddle.y += moveSpeed;
    } else {
      game.rightPaddle.y -= moveSpeed;
    }
  }

  // Keep paddle in bounds
  game.rightPaddle.y = Math.max(0, Math.min(GAME_H - PADDLE_H, game.rightPaddle.y));
}

function gameLoop() {
  if (!game.running || game.paused) return;
  updateGame();
  drawGame();
  requestAnimationFrame(gameLoop);
}

// Event Listeners
canvas.addEventListener('mousemove', (e) => {
  if (!game.running || game.paused) return;
  const rect = canvas.getBoundingClientRect();
  const mouseY = (e.clientY - rect.top) * (GAME_H / rect.height);
  game.leftPaddle.y = Math.max(0, Math.min(GAME_H - PADDLE_H, mouseY - PADDLE_H/2));
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'p') game.paused = !game.paused;
  if (e.key === 'r') resetGame();
  if (!game.paused && game.running) {
    if (e.key === 'ArrowUp') game.leftPaddle.y = Math.max(0, game.leftPaddle.y - 20);
    if (e.key === 'ArrowDown') game.leftPaddle.y = Math.min(GAME_H - PADDLE_H, game.leftPaddle.y + 20);
  }
  if (game.paused) drawPauseScreen();
  else gameLoop();
});

// Mobile touch support
canvas.addEventListener('touchmove', (e) => {
  e.preventDefault();
  const rect = canvas.getBoundingClientRect();
  const touch = e.touches[0];
  const touchY = (touch.clientY - rect.top) * (GAME_H / rect.height);
  game.leftPaddle.y = Math.max(0, Math.min(GAME_H - PADDLE_H, touchY - PADDLE_H/2));
}, { passive: false });

// UI Controls
playBtn.onclick = () => {
  game.difficulty = difficultySelector.value;
  game.aiMode = aiModeSelector.value;
  startGame();
};

effectsToggle.onclick = () => {
  game.visualEffects = !game.visualEffects;
  effectsToggle.textContent = game.visualEffects ? "On" : "Off";
  effectsToggle.classList.toggle('active');
};

soundToggle.onclick = () => {
  game.soundOn = !game.soundOn;
  soundToggle.textContent = game.soundOn ? "On" : "Off";
  soundToggle.classList.toggle('active');
  if (!game.soundOn) bgMusic.pause();
  else if (game.running) bgMusic.play();
};

pauseBtn.onclick = () => {
  game.paused = !game.paused;
  if (!game.paused) gameLoop();
  else drawPauseScreen();
};

resetBtn.onclick = resetGame;
helpBtn.onclick = () => helpPopup.style.display = "block";
closeHelp.onclick = () => helpPopup.style.display = "none";

function startGame() {
  menu.classList.add('hidden');
  gameScreen.classList.remove('hidden');
  resetGame();
  game.running = true;
  game.paused = false;
  if (game.soundOn) {
    bgMusic.volume = 0.4;
    bgMusic.play();
  }
  gameLoop();
}

function drawPauseScreen() {
  ctx.fillStyle = 'rgba(0,0,0,0.5)';
  ctx.fillRect(0, 0, GAME_W, GAME_H);
  ctx.fillStyle = '#fff';
  ctx.font = '30px Arial';
  ctx.textAlign = 'center';
  ctx.fillText('PAUSED', GAME_W/2, GAME_H/2);
}

function endGame() {
  game.running = false;
  endScreen.classList.remove('hidden');
  gameScreen.classList.add('hidden');
  const endMsg = document.getElementById('endMsg');
  const finalScore = document.getElementById('finalScore');
  endMsg.textContent = game.playerScore > game.aiScore ? "You Win!" : "AI Wins!";
  finalScore.textContent = `Final Score: ${game.playerScore} - ${game.aiScore}`;
}

// Initialize game
updateHUD();
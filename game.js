// Modern Pong ML Frontend -- supports touch, pause, resume, reset, leaderboard, AI level display
let canvas = document.getElementById('pong-canvas');
let ctx = canvas.getContext('2d');
let menu = document.getElementById('main-menu');
let gameContainer = document.getElementById('game-container');
let scoreDisplay = document.getElementById('score');
let aiLevelDisplay = document.getElementById('ai-level');
let difficultyDisplay = document.getElementById('difficulty');
let leaderboardDiv = document.getElementById('leaderboard');

let state = {
  running: false,
  paused: false,
  multiplayer: false,
  aiDifficulty: 'medium',
  aiLevel: 1,
  playerScore: 0,
  aiScore: 0,
  ballSpeed: 8,
  winningScore: 10,
  leftPaddle: { x: 30, y: 260, vy: 0 },
  rightPaddle: { x: 856, y: 260, vy: 0 },
  ball: { x: 450, y: 260, vx: 8, vy: 3, spin: 0 },
  touchId: null
};

// --- Leaderboard ---
function getLeaderboard() {
  let lb = localStorage.getItem('pong_leaderboard');
  return lb ? JSON.parse(lb) : [];
}
function setLeaderboard(lb) {
  localStorage.setItem('pong_leaderboard', JSON.stringify(lb));
}
function updateLeaderboard() {
  let lb = getLeaderboard();
  leaderboardDiv.innerHTML = '<strong>Leaderboard</strong><br>' +
    lb.slice(-5).reverse().map(e => `${e.name}: ${e.score}`).join('<br>');
}

// --- Menu & Controls ---
function setDifficulty(diff) {
  state.aiDifficulty = diff;
  state.aiLevel = { 'easy': 1, 'medium': 2, 'hard': 3 }[diff] || 2;
  difficultyDisplay.textContent = 'Difficulty: ' + diff.charAt(0).toUpperCase() + diff.slice(1);
  aiLevelDisplay.textContent = 'AI Level: ' + state.aiLevel;
}
function toggleMultiplayer() {
  state.multiplayer = !state.multiplayer;
}
function startGame() {
  menu.classList.add('hidden');
  gameContainer.classList.remove('hidden');
  resetGame();
  state.running = true;
  loop();
}
function pauseGame() { state.paused = true; }
function resumeGame() { state.paused = false; loop(); }
function resetGame() {
  state.playerScore = 0;
  state.aiScore = 0;
  state.ballSpeed = 8;
  state.leftPaddle.y = 260;
  state.rightPaddle.y = 260;
  resetBall();
  scoreDisplay.textContent = `Player: 0 | AI: 0`;
  aiLevelDisplay.textContent = 'AI Level: ' + state.aiLevel;
}
function showMenu() {
  state.running = false;
  gameContainer.classList.add('hidden');
  menu.classList.remove('hidden');
  updateLeaderboard();
}

// --- Game Mechanics ---
function resetBall() {
  state.ball.x = 450; state.ball.y = 260;
  let angle = (Math.random() * 0.8 - 0.4) * Math.PI;
  let dir = (Math.random() < 0.5) ? -1 : 1;
  state.ball.vx = state.ballSpeed * dir * Math.cos(angle);
  state.ball.vy = state.ballSpeed * Math.sin(angle);
  state.ball.spin = 0;
}
function loop() {
  if (!state.running || state.paused) return;
  update();
  draw();
  requestAnimationFrame(loop);
}
function update() {
  // Ball movement
  state.ball.x += state.ball.vx;
  state.ball.y += state.ball.vy;
  state.ball.vy *= 0.99;
  // Ball physics
  if (state.ball.y <= 0 || state.ball.y + 20 >= 520) {
    state.ball.vy *= -0.94;
    state.ball.vy += (Math.random() - 0.5) * 0.6;
    // bounce sound
  }
  // Left paddle collision
  if (collide(state.ball, state.leftPaddle)) {
    let offset = (state.ball.y+10) - (state.leftPaddle.y+55);
    let norm = offset / 55;
    state.ball.vx = Math.abs(state.ball.vx) * 0.94;
    state.ball.vy += norm * state.ballSpeed * 0.3;
    state.ball.x = state.leftPaddle.x + 14 + 1;
    // bounce sound
  }
  // Right paddle collision
  if (collide(state.ball, state.rightPaddle)) {
    let offset = (state.ball.y+10) - (state.rightPaddle.y+55);
    let norm = offset / 55;
    state.ball.vx = -Math.abs(state.ball.vx) * 0.94;
    state.ball.vy += norm * state.ballSpeed * 0.3;
    state.ball.x = state.rightPaddle.x - 20 - 1;
    // bounce sound
  }
  // Scoring
  if (state.ball.x <= 0) { state.aiScore++; score(); }
  if (state.ball.x + 20 >= 900) { state.playerScore++; score(); }
  // Ball speed increases over time
  if ((state.playerScore + state.aiScore) > 0 && (state.playerScore + state.aiScore) % 5 === 0)
    state.ballSpeed = Math.min(state.ballSpeed + 1, 15);

  // Paddle AI/Movement
  if (!state.multiplayer) {
    let ai_y = state.rightPaddle.y + 55;
    let target = state.ball.y + 10;
    let diff = target - ai_y;
    let move = 0;
    if (Math.abs(diff) > 10) move = diff > 0 ? 1 : -1;
    // DQN simulation: difficulty affects reaction time
    if (state.aiDifficulty === 'easy' && Math.random() < 0.1) move = 0;
    else if (state.aiDifficulty === 'medium' && Math.random() < 0.05) move = 0;
    state.rightPaddle.y += move * 8;
    state.rightPaddle.y = Math.max(0, Math.min(520-110, state.rightPaddle.y));
  }
  // Player paddle (mouse/touch)
  // Touch: move paddle to touch Y
  if (state.touchId !== null) {
    state.leftPaddle.y = state.touchY-55;
    state.leftPaddle.y = Math.max(0, Math.min(520-110, state.leftPaddle.y));
  }
}
function score() {
  scoreDisplay.textContent = `Player: ${state.playerScore} | AI: ${state.aiScore}`;
  resetBall();
  if (state.playerScore >= state.winningScore || state.aiScore >= state.winningScore) {
    state.running = false;
    // Save leaderboard
    let lb = getLeaderboard();
    lb.push({ name: 'Player', score: state.playerScore });
    setLeaderboard(lb);
    showMenu();
  }
}
function collide(ball, paddle) {
  return ball.x < paddle.x + 14 && ball.x + 20 > paddle.x &&
    ball.y < paddle.y + 110 && ball.y + 20 > paddle.y;
}

// --- Drawing ---
function draw() {
  ctx.clearRect(0,0,900,520);
  // Middle dotted line
  ctx.strokeStyle = "#444";
  ctx.setLineDash([10, 18]);
  ctx.beginPath(); ctx.moveTo(450,0); ctx.lineTo(450,520); ctx.stroke();
  ctx.setLineDash([]);
  // Paddles
  ctx.fillStyle = "#fff";
  ctx.fillRect(state.leftPaddle.x, state.leftPaddle.y, 14, 110);
  ctx.fillRect(state.rightPaddle.x, state.rightPaddle.y, 14, 110);
  // Ball
  ctx.fillStyle = "#0ff";
  ctx.beginPath();
  ctx.ellipse(state.ball.x, state.ball.y, 10, 10, 0, 0, 2 * Math.PI);
  ctx.fill();
  // AI Progress
  ctx.fillStyle = "#0ff9";
  ctx.fillRect(900-60, 10, 40, 16);
  ctx.fillStyle = "#222";
  ctx.font = "15px Arial";
  ctx.fillText("Lv."+state.aiLevel, 900-50, 23);
}

// --- Touch Controls ---
canvas.addEventListener('touchstart', function(e){
  if (e.touches.length) {
    state.touchId = e.touches[0].identifier;
    state.touchY = e.touches[0].clientY / window.devicePixelRatio;
  }
});
canvas.addEventListener('touchmove', function(e){
  for (let i=0;i<e.touches.length;i++) {
    if (e.touches[i].identifier === state.touchId) {
      state.touchY = e.touches[i].clientY / window.devicePixelRatio;
      break;
    }
  }
});
canvas.addEventListener('touchend', function(e){
  state.touchId = null;
});
canvas.addEventListener('mousedown', function(e){
  let rect = canvas.getBoundingClientRect();
  let mouseY = (e.clientY - rect.top);
  state.leftPaddle.y = mouseY-55;
});
canvas.addEventListener('mousemove', function(e){
  if (e.buttons) {
    let rect = canvas.getBoundingClientRect();
    let mouseY = (e.clientY - rect.top);
    state.leftPaddle.y = mouseY-55;
  }
});

// Keyboard for player
document.addEventListener('keydown', function(e){
  if (!state.running) return;
  if (e.key === 'ArrowUp') { state.leftPaddle.y -= 16; }
  if (e.key === 'ArrowDown') { state.leftPaddle.y += 16; }
  state.leftPaddle.y = Math.max(0, Math.min(520-110, state.leftPaddle.y));
});

// Init leaderboard on load
updateLeaderboard();
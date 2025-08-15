// Pong Neon ML - Progressive Ball, Neon Visuals, UI/UX
const canvas = document.getElementById('pongCanvas');
const ctx = canvas.getContext('2d');
const menu = document.getElementById('menu');
const gameScreen = document.getElementById('game');
const endScreen = document.getElementById('end');
const playBtn = document.getElementById('playBtn');
const playAgainBtn = document.getElementById('playAgainBtn');
const backMenuBtn = document.getElementById('backMenuBtn');
const pauseBtn = document.getElementById('pauseBtn');
const resetBtn = document.getElementById('resetBtn');
const helpBtn = document.getElementById('helpBtn');
const helpPopup = document.getElementById('helpPopup');
const closeHelp = document.getElementById('closeHelp');
const scoreDisplay = document.getElementById('scoreDisplay');
const difficultyDisplay = document.getElementById('difficultyDisplay');
const aiDisplay = document.getElementById('aiDisplay');
const smartBarFill = document.getElementById('smartBarFill');
const soundBtn = document.getElementById('soundBtn');
const soundToggle = document.getElementById('soundToggle');
const difficultySelector = document.getElementById('difficulty');
const aiModeSelector = document.getElementById('aiMode');
const endMsg = document.getElementById('endMsg');
const finalScore = document.getElementById('finalScore');
const floatingText = document.getElementById('floatingText');
const bgMusic = document.getElementById('bgMusic');
const hitSound = document.getElementById('hitSound');
const wallSound = document.getElementById('wallSound');
const scoreSound = document.getElementById('scoreSound');
const bgParticles = document.getElementById('bg-particles');

// ======= Settings =======
const GAME_W = 960, GAME_H = 600;
const PADDLE_W = 18, PADDLE_H = 110;
const BALL_SIZE = 22;
const BASE_SPEED = 7, MAX_SPEED = 17;
const SPEED_INC = 1.05;
const STREAK_FLAME = 10;
const SMARTNESS_MAX = 100;
// UI State
let game = {
  running: false,
  paused: false,
  streak: 0,
  difficulty: 'medium',
  aiMode: 'dqn',
  soundOn: true,
  smartness: 40,
  playerScore: 0,
  aiScore: 0,
  ball: { x: GAME_W/2, y: GAME_H/2, vx: BASE_SPEED, vy: 2, speed: BASE_SPEED, spin: 0 },
  leftPaddle: { x: 32, y: GAME_H/2-PADDLE_H/2, vy: 0, glow: 0 },
  rightPaddle: { x: GAME_W-50, y: GAME_H/2-PADDLE_H/2, vy: 0, glow: 0, halo: 0 },
  floating: null,
  shake: 0,
  flameTrail: [],
  aiThinking: 0,
  end: false,
  mobileTouch: false,
};
// ======= UI/UX Animations =======
function showMenu() {
  gameScreen.classList.add('hidden');
  endScreen.classList.add('hidden');
  menu.classList.remove('hidden');
  game.running = false;
}
function showGame() {
  menu.classList.add('hidden');
  endScreen.classList.add('hidden');
  gameScreen.classList.remove('hidden');
  game.running = true;
}
function showEnd(msg) {
  endMsg.textContent = msg;
  finalScore.textContent = `Player: ${game.playerScore} | AI: ${game.aiScore}`;
  menu.classList.add('hidden');
  gameScreen.classList.add('hidden');
  endScreen.classList.remove('hidden');
  game.running = false;
}
function showFloatingText(txt, color="#0ff") {
  floatingText.innerText = txt;
  floatingText.style.color = color;
  floatingText.style.opacity = 1;
  floatingText.style.transform = "translate(-50%,0) scale(1.12)";
  setTimeout(()=>{ floatingText.style.opacity = 0; floatingText.style.transform = "translate(-50%,0) scale(0.98)"; }, 1200);
}
function shakeScreen(n=10) { game.shake = n; }
function updateHUD() {
  scoreDisplay.innerHTML = `<span style="color:#0ff">Player:</span> ${game.playerScore} <span style="color:#ff00cc;margin-left:18px">AI:</span> ${game.aiScore}`;
  difficultyDisplay.innerHTML = `Difficulty: <b>${game.difficulty[0].toUpperCase()+game.difficulty.slice(1)}</b>`;
  aiDisplay.innerHTML = `AI: <span style="color:#ff00cc">${game.aiMode==="dqn"?"DQN":"Q-Learn"}</span>`;
  smartBarFill.style.width = `${(game.smartness/SMARTNESS_MAX)*100}%`;
  smartBarFill.style.background = `linear-gradient(90deg,#0ff,${game.smartness>80?"#ff00cc":"#00ff99"})`;
}
// ======= Game Mechanics =======
function resetGame() {
  game.ball = { x: GAME_W/2, y: GAME_H/2, vx: BASE_SPEED, vy: (Math.random()*2-1)*BASE_SPEED/2, speed: BASE_SPEED, spin: 0 };
  game.leftPaddle.y = GAME_H/2-PADDLE_H/2;
  game.rightPaddle.y = GAME_H/2-PADDLE_H/2;
  game.playerScore = 0; game.aiScore = 0; game.streak = 0;
  game.smartness = game.aiMode==="dqn"?50:30;
  game.flameTrail = [];
  updateHUD();
}
function startGame() {
  resetGame();
  showGame();
  if (game.soundOn) { bgMusic.volume=0.46; bgMusic.play();}
  requestAnimationFrame(mainLoop);
}
function mainLoop() {
  if (!game.running) return;
  if (game.paused) { drawPause(); return; }
  updateGame();
  drawGame();
  requestAnimationFrame(mainLoop);
}
function updateGame() {
  // Ball movement
  game.ball.x += game.ball.vx;
  game.ball.y += game.ball.vy;
  game.ball.vy *= 0.992;
  // Wall bounce
  if (game.ball.y <= 0 || game.ball.y+BALL_SIZE >= GAME_H) {
    game.ball.vy *= -0.97;
    game.ball.y = Math.max(0, Math.min(GAME_H-BALL_SIZE, game.ball.y));
    playSFX(wallSound);
    shakeScreen(7);
    // Streak reset
    game.streak = 0;
  }
  // Paddle collisions
  let paddleHit = false;
  // Left
  if (collide(game.ball, game.leftPaddle)) {
    let offset = ((game.ball.y+BALL_SIZE/2)-(game.leftPaddle.y+PADDLE_H/2));
    let norm = offset/(PADDLE_H/2);
    let spin = norm*game.ball.speed*0.31;
    game.ball.vx = Math.abs(game.ball.vx)*1.02;
    game.ball.vy += spin;
    game.ball.x = game.leftPaddle.x+PADDLE_W+2;
    paddleHit = true;
    game.leftPaddle.glow = 1;
    game.streak++;
    if (game.streak>=STREAK_FLAME) startFlame();
    playSFX(hitSound);
    if (Math.abs(norm)>0.65) clutchSlowmo();
  }
  // Right
  if (collide(game.ball, game.rightPaddle)) {
    let offset = ((game.ball.y+BALL_SIZE/2)-(game.rightPaddle.y+PADDLE_H/2));
    let norm = offset/(PADDLE_H/2);
    let spin = norm*game.ball.speed*0.31;
    game.ball.vx = -Math.abs(game.ball.vx)*1.02;
    game.ball.vy += spin;
    game.ball.x = game.rightPaddle.x-BALL_SIZE-2;
    paddleHit = true;
    game.rightPaddle.glow = 1;
    game.aiThinking = 1;
    game.streak++;
    if (game.streak>=STREAK_FLAME) startFlame();
    playSFX(hitSound);
    if (Math.abs(norm)>0.65) clutchSlowmo();
  }
  if (paddleHit) {
    // Progressive speed
    game.ball.speed = Math.min(game.ball.speed*SPEED_INC, MAX_SPEED);
    // Recalculate vx/vy based on speed
    let curAngle = Math.atan2(game.ball.vy, game.ball.vx);
    let newVx = Math.cos(curAngle)*game.ball.speed;
    let newVy = Math.sin(curAngle)*game.ball.speed;
    game.ball.vx = newVx;
    game.ball.vy = newVy;
    showFloatingText("+speed", "#0ff");
    shakeScreen(10);
    if (game.ball.speed>BASE_SPEED+4) {
      bgMusic.volume = Math.min(0.62, 0.36+game.ball.speed/25);
    }
  }
  // Score
  if (game.ball.x<0) { scorePoint('ai'); }
  if (game.ball.x+BALL_SIZE>GAME_W) { scorePoint('player'); }
  // AI movement (simulate “thinking” with halo)
  let aiTarget = game.ball.y+BALL_SIZE/2;
  let aiCenter = game.rightPaddle.y+PADDLE_H/2;
  let aiDiff = aiTarget-aiCenter;
  let aiMove = Math.abs(aiDiff)>12 ? (aiDiff>0?1:-1) : 0;
  if (game.aiMode==="dqn") {
    // “Smartness” increases at higher ball speed
    game.smartness = Math.min(SMARTNESS_MAX, game.smartness+game.ball.speed/120);
    // Hard: perfect prediction, Medium: some error, Easy: more miss
    if (game.difficulty==="hard" && Math.random()<0.02) aiMove=0;
    if (game.difficulty==="medium" && Math.random()<0.05) aiMove=0;
    if (game.difficulty==="easy" && Math.random()<0.12) aiMove=0;
  } else {
    // Q-learning: more random
    if (Math.random()<0.16) aiMove=0;
    game.smartness = Math.max(15, game.smartness-0.10);
  }
  game.rightPaddle.y += aiMove*11;
  game.rightPaddle.y = Math.max(0, Math.min(GAME_H-PADDLE_H, game.rightPaddle.y));
  // Right paddle “halo” pulses when thinking
  game.rightPaddle.halo = Math.max(0, game.aiThinking-0.02);
  game.aiThinking *= 0.97;
  // Glow animation fade
  game.leftPaddle.glow *= 0.85;
  game.rightPaddle.glow *= 0.85;
  // Flame trail for streak
  updateFlame();
  updateHUD();
}
function scorePoint(who) {
  if (who==="player") game.playerScore++;
  else game.aiScore++;
  playSFX(scoreSound);
  shakeScreen(18);
  showFloatingText(who==="player"?"Score!":"AI Scores!","#ff00cc");
  game.streak = 0; stopFlame();
  game.ball = { x: GAME_W/2, y: GAME_H/2, vx: BASE_SPEED*(who==="player"?-1:1), vy: (Math.random()*2-1)*BASE_SPEED/2, speed: BASE_SPEED, spin: 0 };
  if (game.playerScore>=8 || game.aiScore>=8) {
    setTimeout(() => showEnd(game.playerScore>game.aiScore?"Victory!":"Defeat!"), 500);
  }
}
function collide(ball, paddle) {
  return ball.x < paddle.x+PADDLE_W && ball.x+BALL_SIZE > paddle.x &&
         ball.y < paddle.y+PADDLE_H && ball.y+BALL_SIZE > paddle.y;
}
function clutchSlowmo() {
  // Animate slow-motion
  canvas.classList.add('clutch');
  setTimeout(()=>canvas.classList.remove('clutch'), 160);
}
canvas.classList.add('clutch');
canvas.addEventListener('animationend',()=>canvas.classList.remove('clutch'));
// ======= Flame Trail on Ball =======
function startFlame() {
  game.flameTrail = [];
}
function updateFlame() {
  if (game.streak<STREAK_FLAME) return;
  game.flameTrail.push({x:game.ball.x+BALL_SIZE/2, y:game.ball.y+BALL_SIZE/2, r:12, alpha:1});
  if (game.flameTrail.length>18) game.flameTrail.shift();
  for (let f of game.flameTrail) f.alpha *= 0.93;
}
function stopFlame() { game.flameTrail = []; }
// ======= Drawing =======
function drawGame() {
  // Particle background
  drawParticles();
  ctx.save();
  if (game.shake>0) {
    ctx.translate(Math.random()*game.shake-2, Math.random()*game.shake-2);
    game.shake *= 0.9;
  }
  // Neon center line
  ctx.strokeStyle = "#0ff9";
  ctx.shadowColor = "#0ff";
  ctx.shadowBlur = 18;
  ctx.setLineDash([16, 24]);
  ctx.beginPath(); ctx.moveTo(GAME_W/2,0); ctx.lineTo(GAME_W/2,GAME_H); ctx.stroke();
  ctx.setLineDash([]);
  ctx.shadowBlur = 0;
  // Flame trail
  for (let f of game.flameTrail) {
    ctx.save();
    ctx.globalAlpha = f.alpha*0.6;
    let grad = ctx.createRadialGradient(f.x,f.y,4,f.x,f.y,20); grad.addColorStop(0,"#ff00cc"); grad.addColorStop(1,"#0ff0");
    ctx.fillStyle=grad;
    ctx.beginPath(); ctx.arc(f.x,f.y,15,0,Math.PI*2); ctx.fill();
    ctx.restore();
  }
  // Ball
  ctx.save();
  ctx.shadowColor = "#0ff";
  ctx.shadowBlur = 18;
  ctx.beginPath(); ctx.arc(game.ball.x+BALL_SIZE/2, game.ball.y+BALL_SIZE/2, BALL_SIZE/2, 0, Math.PI*2);
  ctx.fillStyle = "rgba(0,255,255,0.98)";
  ctx.fill();
  ctx.shadowBlur = 0;
  ctx.restore();
  // Left paddle
  ctx.save();
  ctx.shadowColor = "#0ff";
  ctx.shadowBlur = 12*game.leftPaddle.glow;
  ctx.fillStyle = "#0ff";
  ctx.fillRect(game.leftPaddle.x, game.leftPaddle.y, PADDLE_W, PADDLE_H);
  ctx.shadowBlur = 0;
  ctx.restore();
  // Right paddle
  ctx.save();
  ctx.shadowColor = "#ff00cc";
  ctx.shadowBlur = 12*game.rightPaddle.glow;
  ctx.fillStyle = "#ff00cc";
  ctx.fillRect(game.rightPaddle.x, game.rightPaddle.y, PADDLE_W, PADDLE_H);
  // AI "thinking" halo
  if (game.rightPaddle.halo>0.05) {
    ctx.globalAlpha = game.rightPaddle.halo*0.5;
    ctx.beginPath();
    ctx.arc(game.rightPaddle.x+PADDLE_W/2, game.rightPaddle.y+PADDLE_H/2, 42, 0, Math.PI*2);
    ctx.strokeStyle = "#ff00cc";
    ctx.lineWidth = 6;
    ctx.shadowColor="#ff00cc"; ctx.shadowBlur=16;
    ctx.stroke();
    ctx.shadowBlur=0; ctx.globalAlpha=1;
  }
  ctx.restore();
  ctx.restore();
}
function drawPause() {
  ctx.save();
  ctx.fillStyle = "rgba(20,20,30,0.82)";
  ctx.fillRect(0,0,GAME_W,GAME_H);
  ctx.font = "2.3em Segoe UI";
  ctx.textAlign = "center";
  ctx.fillStyle = "#0ff";
  ctx.fillText("Paused", GAME_W/2, GAME_H/2-10);
  ctx.font = "1.3em Segoe UI";
  ctx.fillStyle = "#fff";
  ctx.fillText("Press P or Resume", GAME_W/2, GAME_H/2+36);
  ctx.restore();
}
// ======= Particle Background =======
let particles = [];
function drawParticles() {
  if (!particles.length) generateParticles();
  let ctx2d = ctx;
  for (let p of particles) {
    p.y += p.vy;
    if (p.y>GAME_H) p.y = -24, p.x = Math.random()*GAME_W;
    ctx2d.save();
    ctx2d.globalAlpha = p.alpha;
    ctx2d.beginPath(); ctx2d.arc(p.x,p.y,p.r,0,Math.PI*2);
    ctx2d.fillStyle = p.color;
    ctx2d.shadowColor = p.color; ctx2d.shadowBlur = 18;
    ctx2d.fill(); ctx2d.shadowBlur = 0; ctx2d.restore();
  }
}
function generateParticles() {
  particles = [];
  for (let i=0;i<44;i++) {
    particles.push({
      x: Math.random()*GAME_W,
      y: Math.random()*GAME_H,
      r: Math.random()*3+3,
      alpha: Math.random()*0.3+0.15,
      color: i%2==0?"#0ff":"#ff00cc",
      vy: Math.random()*0.9+0.2
    });
  }
}
// ======= Sound & Music =======
function playSFX(audio) {
  if (!game.soundOn || !audio) return;
  audio.currentTime=0; audio.volume=0.58; audio.play();
}
// ======= Controls =======
canvas.addEventListener('mousedown', function(e){
  let rect = canvas.getBoundingClientRect();
  let mouseY = (e.clientY - rect.top);
  game.leftPaddle.y = mouseY-PADDLE_H/2;
});
canvas.addEventListener('mousemove', function(e){
  if (e.buttons) {
    let rect = canvas.getBoundingClientRect();
    let mouseY = (e.clientY - rect.top);
    game.leftPaddle.y = mouseY-PADDLE_H/2;
  }
});
canvas.addEventListener('touchstart', function(e){
  game.mobileTouch = true;
  if (e.touches.length) {
    let touchY = e.touches[0].clientY / window.devicePixelRatio;
    game.leftPaddle.y = touchY-PADDLE_H/2;
  }
});
canvas.addEventListener('touchmove', function(e){
  if (!game.mobileTouch) return;
  for (let i=0;i<e.touches.length;i++) {
    let touchY = e.touches[i].clientY / window.devicePixelRatio;
    game.leftPaddle.y = touchY-PADDLE_H/2;
  }
});
document.addEventListener('keydown', function(e){
  if (!game.running) return;
  if (game.paused && e.key==="p") { game.paused=false; mainLoop(); }
  if (!game.paused && e.key==="p") { game.paused=true; }
  if (e.key==="r") { resetGame(); }
  if (e.key==="ArrowUp") { game.leftPaddle.y -= 22; }
  if (e.key==="ArrowDown") { game.leftPaddle.y += 22; }
  game.leftPaddle.y = Math.max(0, Math.min(GAME_H-PADDLE_H, game.leftPaddle.y));
});
pauseBtn.onclick = ()=>{ game.paused=true; };
resetBtn.onclick = ()=>{ resetGame(); };
soundBtn.onclick = ()=>{ game.soundOn=!game.soundOn; if (!game.soundOn) bgMusic.pause(); else bgMusic.play();}
soundToggle.onclick = ()=>{ game.soundOn=!game.soundOn; soundToggle.innerText=game.soundOn?"On":"Off"; if (!game.soundOn) bgMusic.pause(); else bgMusic.play(); };
playBtn.onclick = ()=>{ game.difficulty=difficultySelector.value; game.aiMode=aiModeSelector.value; startGame(); };
playAgainBtn.onclick = ()=>{ startGame(); };
backMenuBtn.onclick = ()=>{ showMenu(); };
helpBtn.onclick = ()=>{ helpPopup.style.display="block"; };
closeHelp.onclick = ()=>{ helpPopup.style.display="none"; };
difficultySelector.onchange = ()=>{ game.difficulty=difficultySelector.value; };
aiModeSelector.onchange = ()=>{ game.aiMode=aiModeSelector.value; };
// ======= Init =======
showMenu(); updateHUD(); generateParticles();
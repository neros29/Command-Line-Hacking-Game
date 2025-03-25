const { Game } = require('../src/game');

describe('Game Mechanics', () => {
  let game;
  
  beforeEach(() => {
    game = new Game();
  });
  
  test('should initialize game with correct default state', () => {
    expect(game.isRunning).toBeFalsy();
    expect(game.score).toBe(0);
    expect(game.level).toBe(1);
  });
  
  test('should start game properly', () => {
    game.start();
    expect(game.isRunning).toBeTruthy();
  });
  
  test('should increase level when player completes a hack', () => {
    game.start();
    const initialLevel = game.level;
    game.completeHack();
    expect(game.level).toBe(initialLevel + 1);
  });
});

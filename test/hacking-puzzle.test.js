const { HackingPuzzle } = require('../src/hacking-puzzle');

describe('Hacking Puzzle', () => {
  let puzzle;
  
  beforeEach(() => {
    puzzle = new HackingPuzzle({ difficulty: 'easy' });
  });
  
  test('should generate appropriate puzzle based on difficulty', () => {
    expect(puzzle.words.length).toBeGreaterThan(0);
    expect(puzzle.password).toBeDefined();
    
    const hardPuzzle = new HackingPuzzle({ difficulty: 'hard' });
    expect(hardPuzzle.words.length).toBeGreaterThan(puzzle.words.length);
  });
  
  test('should correctly validate password attempts', () => {
    const correctPassword = puzzle.password;
    expect(puzzle.checkPassword(correctPassword)).toBeTruthy();
    expect(puzzle.checkPassword('wrong_password')).toBeFalsy();
  });
  
  test('should provide hints when requested', () => {
    const hint = puzzle.getHint();
    expect(hint).toBeDefined();
    expect(typeof hint).toBe('string');
  });
});

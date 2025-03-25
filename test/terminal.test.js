const { Terminal } = require('../src/terminal');

describe('Terminal Functions', () => {
  let terminal;
  
  beforeEach(() => {
    terminal = new Terminal();
  });
  
  test('should display correct welcome message', () => {
    const consoleSpy = jest.spyOn(console, 'log');
    terminal.displayWelcomeMessage();
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Welcome to Terminal Hacking Game'));
    consoleSpy.mockRestore();
  });
  
  test('should parse user commands correctly', () => {
    expect(terminal.parseCommand('help')).toEqual({
      command: 'help',
      args: []
    });
    
    expect(terminal.parseCommand('hack 192.168.1.1')).toEqual({
      command: 'hack',
      args: ['192.168.1.1']
    });
  });
});

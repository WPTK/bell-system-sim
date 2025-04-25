import { commands, Command } from './commands';
import { VirtualFileSystem } from './filesystem';
import { User } from './users';

export interface ParsedCommand {
  command: string;
  args: string[];
  redirectOutput?: string;
  appendOutput?: string;
  redirectInput?: string;
  pipe?: ParsedCommand;
}

export interface ShellEnvironment {
  PATH: string;
  HOME: string;
  USER: string;
  PWD: string;
  PS1: string;
  SHELL: string;
  TERM: string;
  [key: string]: string;
}

export interface CommandResult {
  output: string;
  error?: string;
  exitCode: number;
}

export class Shell {
  private fs: VirtualFileSystem;
  private user: User;
  private env: ShellEnvironment;
  private history: string[] = [];
  private maxHistoryLength = 1000;
  
  constructor(fs: VirtualFileSystem, user: User) {
    this.fs = fs;
    this.user = user;
    this.env = {
      PATH: '/bin:/usr/bin',
      HOME: `/usr/${user.username}`,
      USER: user.username,
      PWD: fs.currentDirectory,
      PS1: '$ ',
      SHELL: '/bin/sh',
      TERM: 'vt100'
    };
  }
  
  // Get the current environment
  getEnvironment(): ShellEnvironment {
    // Update PWD to reflect current directory
    this.env.PWD = this.fs.currentDirectory;
    return { ...this.env };
  }
  
  // Set an environment variable
  setEnv(name: string, value: string): void {
    this.env[name] = value;
  }
  
  // Get command history
  getHistory(): string[] {
    return [...this.history];
  }
  
  // Add command to history
  addToHistory(command: string): void {
    // Don't add empty commands or duplicates of the most recent command
    if (!command.trim() || (this.history.length > 0 && this.history[this.history.length - 1] === command)) {
      return;
    }
    
    this.history.push(command);
    
    // Limit history size
    if (this.history.length > this.maxHistoryLength) {
      this.history.shift();
    }
    
    // Add to server history
    apiRequest('/api/history', {
      username: this.user.username,
      command
    }).catch(error => {
      console.error('Failed to add command to history:', error);
    });
  }
  
  // Parse a command line into command, arguments and redirections
  parseCommandLine(line: string): ParsedCommand {
    // Trim leading/trailing whitespace
    line = line.trim();
    
    // Handle empty input
    if (!line) {
      return { command: '', args: [] };
    }
    
    // Check for pipes
    const pipeIndex = line.indexOf('|');
    if (pipeIndex !== -1) {
      const leftCommand = line.substring(0, pipeIndex).trim();
      const rightCommand = line.substring(pipeIndex + 1).trim();
      
      return {
        ...this.parseCommandLine(leftCommand),
        pipe: this.parseCommandLine(rightCommand)
      };
    }
    
    // Split command line into tokens, respecting quotes
    const tokens: string[] = [];
    let currentToken = '';
    let inQuotes = false;
    let quoteChar = '';
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      
      if (char === '"' || char === "'") {
        if (!inQuotes) {
          inQuotes = true;
          quoteChar = char;
        } else if (char === quoteChar) {
          inQuotes = false;
          quoteChar = '';
        } else {
          currentToken += char;
        }
      } else if (!inQuotes && (char === ' ' || char === '\t')) {
        if (currentToken) {
          tokens.push(currentToken);
          currentToken = '';
        }
      } else {
        currentToken += char;
      }
    }
    
    if (currentToken) {
      tokens.push(currentToken);
    }
    
    // Process redirections
    let command = '';
    const args: string[] = [];
    let redirectOutput: string | undefined;
    let appendOutput: string | undefined;
    let redirectInput: string | undefined;
    
    for (let i = 0; i < tokens.length; i++) {
      const token = tokens[i];
      
      if (token === '>' && i < tokens.length - 1) {
        redirectOutput = tokens[i + 1];
        i++; // Skip the next token (filename)
      } else if (token === '>>' && i < tokens.length - 1) {
        appendOutput = tokens[i + 1];
        i++; // Skip the next token (filename)
      } else if (token === '<' && i < tokens.length - 1) {
        redirectInput = tokens[i + 1];
        i++; // Skip the next token (filename)
      } else if (!command) {
        command = token;
      } else {
        args.push(token);
      }
    }
    
    return { 
      command, 
      args, 
      redirectOutput, 
      appendOutput, 
      redirectInput 
    };
  }
  
  // Execute a parsed command
  async executeCommand(parsedCommand: ParsedCommand): Promise<CommandResult> {
    const { command, args, redirectOutput, appendOutput, redirectInput, pipe } = parsedCommand;
    
    // Handle empty command
    if (!command) {
      return { output: '', exitCode: 0 };
    }
    
    // Check for built-in commands
    if (command === 'exit') {
      return { output: 'logout\n', exitCode: 0 };
    }
    
    if (command === 'export') {
      if (args.length === 0) {
        // List all environment variables
        let output = '';
        for (const [key, value] of Object.entries(this.env)) {
          output += `${key}=${value}\n`;
        }
        return { output, exitCode: 0 };
      } else {
        // Set environment variables
        for (const arg of args) {
          const [name, value] = arg.split('=');
          if (name && value) {
            this.setEnv(name, value);
          }
        }
        return { output: '', exitCode: 0 };
      }
    }
    
    // Look for command in available commands
    const commandImpl = commands[command];
    
    if (!commandImpl) {
      return {
        output: '',
        error: `${command}: command not found`,
        exitCode: 127
      };
    }
    
    // Handle input redirection
    let inputContent = '';
    if (redirectInput) {
      try {
        inputContent = await this.fs.readFile(redirectInput);
      } catch (error) {
        return {
          output: '',
          error: `${command}: ${redirectInput}: No such file or directory`,
          exitCode: 1
        };
      }
    }
    
    // Execute command
    const result = await commandImpl.execute(args, {
      fs: this.fs,
      currentUser: this.user,
      env: this.env
    });
    
    // Handle output redirection
    if (redirectOutput) {
      try {
        await this.fs.writeFile(redirectOutput, result.output);
        result.output = ''; // Clear output since it's been redirected
      } catch (error) {
        return {
          output: '',
          error: `${command}: Cannot write to ${redirectOutput}: ${error instanceof Error ? error.message : String(error)}`,
          exitCode: 1
        };
      }
    } else if (appendOutput) {
      try {
        let existingContent = '';
        try {
          existingContent = await this.fs.readFile(appendOutput);
        } catch (error) {
          // File doesn't exist, will be created
        }
        
        await this.fs.writeFile(appendOutput, existingContent + result.output);
        result.output = ''; // Clear output since it's been redirected
      } catch (error) {
        return {
          output: '',
          error: `${command}: Cannot append to ${appendOutput}: ${error instanceof Error ? error.message : String(error)}`,
          exitCode: 1
        };
      }
    }
    
    // Handle pipe
    if (pipe) {
      // Set up the piped command with the output of this command as its input
      const pipedResult = await this.executeCommand({
        ...pipe,
        // Any redirectInput in the pipe is ignored, as it gets input from the previous command
        redirectInput: undefined
      });
      
      return pipedResult;
    }
    
    return result;
  }
  
  // Execute a command line
  async execute(commandLine: string): Promise<CommandResult> {
    // Add to history
    this.addToHistory(commandLine);
    
    // Parse the command line
    const parsedCommand = this.parseCommandLine(commandLine);
    
    // Execute the parsed command
    return await this.executeCommand(parsedCommand);
  }
}

// Helper function for API requests
async function apiRequest(url: string, data: any): Promise<Response> {
  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  });
}

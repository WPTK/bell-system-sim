import { useState, useEffect, useCallback } from 'react';
import { VirtualFileSystem, File } from '@/lib/filesystem';
import { Shell } from '@/lib/shell';
import { userSystem, User } from '@/lib/users';
import { apiRequest } from '@/lib/queryClient';

interface UseTerminalOptions {
  initialDirectory?: string;
  autoLogin?: boolean;
}

interface TerminalState {
  fs: VirtualFileSystem;
  user: User | null;
  shell: Shell | null;
  output: string[];
  prompt: string;
  isLoggedIn: boolean;
  isLoading: boolean;
  currentDirectory: string;
  loginStep: 'username' | 'password';
  loginUsername: string;
}

interface TerminalActions {
  executeCommand: (command: string) => Promise<void>;
  handleLogin: (input: string) => Promise<void>;
  setPrompt: (newPrompt: string) => void;
  clearOutput: () => void;
  readFile: (path: string) => Promise<string>;
  writeFile: (path: string, content: string) => Promise<void>;
  getCurrentDirectory: () => string;
  logout: () => void;
}

/**
 * Custom hook for managing terminal state and operations
 */
export function useTerminal(options: UseTerminalOptions = {}): [TerminalState, TerminalActions] {
  const { initialDirectory = '/usr/you', autoLogin = true } = options;
  
  // Terminal state
  const [fs] = useState(() => new VirtualFileSystem(initialDirectory));
  const [user, setUser] = useState<User | null>(null);
  const [shell, setShell] = useState<Shell | null>(null);
  const [output, setOutput] = useState<string[]>([]);
  const [prompt, setPrompt] = useState('$ ');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [loginStep, setLoginStep] = useState<'username' | 'password'>('username');
  const [loginUsername, setLoginUsername] = useState('');
  
  // Initialize the terminal
  useEffect(() => {
    const initialize = async () => {
      setIsLoading(true);
      
      try {
        if (autoLogin) {
          // Auto-login as 'you'
          await performLogin('you', 'password');
        } else {
          setOutput(['UNIX Time-Sharing System, Version 7', 'Bell Laboratories, January 1979', '', 'login: ']);
          setIsLoading(false);
        }
      } catch (error) {
        console.error('Terminal initialization failed:', error);
        setOutput(['Login failed. Please try again.', '', 'login: ']);
        setIsLoading(false);
      }
    };
    
    initialize();
  }, [autoLogin, initialDirectory]);
  
  // Perform login
  const performLogin = async (username: string, password: string) => {
    try {
      // Login as the specified user
      const loggedInUser = await userSystem.login(username, password);
      
      // Create shell with logged in user
      const newShell = new Shell(fs, loggedInUser);
      
      setUser(loggedInUser);
      setShell(newShell);
      setIsLoggedIn(true);
      
      // Update prompt
      const env = newShell.getEnvironment();
      setPrompt(env.PS1);
      
      // Show welcome message
      const welcomeOutput = [
        'UNIX Time-Sharing System, Version 7',
        'Bell Laboratories, January 1979',
        '',
        `Last login: ${new Date().toLocaleDateString()} on tty01`,
        ''
      ];
      setOutput(welcomeOutput);
      setIsLoading(false);
      
      return loggedInUser;
    } catch (error) {
      throw new Error('Login failed');
    }
  };
  
  // Handle login sequence
  const handleLogin = useCallback(async (input: string): Promise<void> => {
    if (loginStep === 'username') {
      setLoginUsername(input);
      setOutput(prev => [...prev, `login: ${input}`, 'Password: ']);
      setLoginStep('password');
    } else if (loginStep === 'password') {
      try {
        await performLogin(loginUsername, input);
      } catch (error) {
        setOutput(prev => [...prev, '', 'Login incorrect', '', 'login: ']);
        setLoginStep('username');
      }
    }
  }, [loginStep, loginUsername]);
  
  // Execute a command
  const executeCommand = useCallback(async (command: string): Promise<void> => {
    if (!isLoggedIn) {
      await handleLogin(command);
      return;
    }
    
    if (!shell) return;
    
    // Add command to output
    setOutput(prev => [...prev, `${prompt}${command}`]);
    
    // Handle empty command
    if (!command.trim()) {
      return;
    }
    
    // Execute command
    const result = await shell.execute(command);
    
    // Update output
    const newOutput = [...output, `${prompt}${command}`];
    
    if (result.output) {
      newOutput.push(result.output.trimEnd());
    }
    
    if (result.error) {
      newOutput.push(result.error);
    }
    
    setOutput(newOutput);
    
    // Special handling for 'cd' command to update prompt directory
    if (command.trim().startsWith('cd') && result.exitCode === 0) {
      // Update environment after directory change
      const env = shell.getEnvironment();
      setPrompt(env.PS1);
    }
  }, [isLoggedIn, shell, prompt, output, handleLogin]);
  
  // Read a file
  const readFile = useCallback(async (path: string): Promise<string> => {
    if (!fs) throw new Error('File system not initialized');
    return await fs.readFile(path);
  }, [fs]);
  
  // Write to a file
  const writeFile = useCallback(async (path: string, content: string): Promise<void> => {
    if (!fs) throw new Error('File system not initialized');
    if (!user) throw new Error('Not logged in');
    
    await fs.writeFile(path, content, {
      owner: user.username,
      group: user.primaryGroup
    });
  }, [fs, user]);
  
  // Clear the terminal output
  const clearOutput = useCallback(() => {
    setOutput([]);
  }, []);
  
  // Get current directory
  const getCurrentDirectory = useCallback(() => {
    return fs.currentDirectory;
  }, [fs]);
  
  // Logout
  const logout = useCallback(() => {
    userSystem.logout();
    setUser(null);
    setShell(null);
    setIsLoggedIn(false);
    setLoginStep('username');
    setOutput(['UNIX Time-Sharing System, Version 7', 'Bell Laboratories, January 1979', '', 'login: ']);
  }, []);
  
  const state: TerminalState = {
    fs,
    user,
    shell,
    output,
    prompt,
    isLoggedIn,
    isLoading,
    currentDirectory: fs.currentDirectory,
    loginStep,
    loginUsername
  };
  
  const actions: TerminalActions = {
    executeCommand,
    handleLogin,
    setPrompt,
    clearOutput,
    readFile,
    writeFile,
    getCurrentDirectory,
    logout
  };
  
  return [state, actions];
}

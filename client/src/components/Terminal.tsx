import React, { useEffect, useState, useRef } from 'react';
import { Shell } from '@/lib/shell';
import { VirtualFileSystem } from '@/lib/filesystem';
import { userSystem, User } from '@/lib/users';
import CommandInput from './CommandInput';
import TerminalOutput from './TerminalOutput';

interface TerminalProps {
  initialFs?: VirtualFileSystem;
  className?: string;
}

const Terminal: React.FC<TerminalProps> = ({ initialFs, className }) => {
  const [fs] = useState(() => initialFs || new VirtualFileSystem('/usr/you'));
  const [user, setUser] = useState<User | null>(null);
  const [shell, setShell] = useState<Shell | null>(null);
  const [output, setOutput] = useState<string[]>([]);
  const [prompt, setPrompt] = useState('$ ');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loginStep, setLoginStep] = useState<'username' | 'password'>('username');
  const [loginUsername, setLoginUsername] = useState('');
  const outputRef = useRef<HTMLDivElement>(null);

  // Auto-login on component mount
  useEffect(() => {
    const autoLogin = async () => {
      try {
        // Auto-login as 'you'
        const loggedInUser = await userSystem.login('you', 'password');
        
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
      } catch (error) {
        console.error('Auto-login failed:', error);
        setOutput(['Login failed. Please try again.']);
      }
    };
    
    autoLogin();
  }, [fs]);

  // Scroll to bottom when output changes
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

  // Handle command execution
  const executeCommand = async (command: string) => {
    if (!isLoggedIn) {
      handleLogin(command);
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
  };

  // Handle login sequence
  const handleLogin = async (input: string) => {
    if (loginStep === 'username') {
      setLoginUsername(input);
      setOutput(prev => [...prev, `login: ${input}`, 'Password: ']);
      setLoginStep('password');
    } else if (loginStep === 'password') {
      try {
        const loggedInUser = await userSystem.login(loginUsername, input);
        
        // Create shell with logged in user
        const newShell = new Shell(fs, loggedInUser);
        
        setUser(loggedInUser);
        setShell(newShell);
        setIsLoggedIn(true);
        
        // Update prompt
        const env = newShell.getEnvironment();
        setPrompt(env.PS1);
        
        // Show welcome message
        setOutput(prev => [
          ...prev,
          '',
          `Last login: ${new Date().toLocaleDateString()} on tty01`,
          ''
        ]);
      } catch (error) {
        setOutput(prev => [...prev, '', 'Login incorrect', '', 'login: ']);
        setLoginStep('username');
      }
    }
  };

  return (
    <div className={`flex flex-col h-full ${className}`}>
      <div 
        ref={outputRef}
        className="flex-1 p-3 overflow-y-auto terminal-custom-scrollbar"
      >
        <TerminalOutput lines={output} />
      </div>
      
      <div className="border-t border-ring p-3 bg-card">
        <CommandInput 
          prompt={isLoggedIn ? prompt : (loginStep === 'username' ? 'login: ' : 'Password: ')}
          onSubmit={executeCommand}
          hideInput={loginStep === 'password'}
        />
      </div>
    </div>
  );
};

export default Terminal;

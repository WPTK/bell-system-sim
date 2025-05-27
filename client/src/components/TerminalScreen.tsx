import { useState, useRef, useEffect } from "react";
import { useTerminal } from "@/hooks/useTerminal";

interface TerminalScreenProps {
  currentDirectory: string;
  onDirectoryChange: (dir: string) => void;
  onManualRequest: (command: string) => void;
}

interface TerminalLine {
  type: 'command' | 'output' | 'error';
  content: string;
  timestamp?: Date;
}

export default function TerminalScreen({ 
  currentDirectory, 
  onDirectoryChange, 
  onManualRequest 
}: TerminalScreenProps) {
  const [terminalLines, setTerminalLines] = useState<TerminalLine[]>([
    { type: 'output', content: 'UNIX V7 (Bell Telephone Laboratories)' },
    { type: 'output', content: 'login: root' },
    { type: 'output', content: 'password: ' },
    { type: 'output', content: '' },
    { type: 'output', content: 'Welcome to UNIX Version 7' },
    { type: 'output', content: 'Copyright (c) 1976 Bell Telephone Laboratories, Inc.' },
    { type: 'output', content: '' },
    { type: 'output', content: 'You have mail.' },
    { type: 'output', content: '' },
  ]);
  
  const [currentInput, setCurrentInput] = useState("");
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const terminalRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  const { executeCommand } = useTerminal();

  useEffect(() => {
    // Auto-focus input and scroll to bottom
    inputRef.current?.focus();
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [terminalLines]);

  useEffect(() => {
    // Handle keyboard shortcuts
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'F1') {
        e.preventDefault();
        handleCommand('help');
      } else if (e.key === 'F2') {
        e.preventDefault();
        onManualRequest('ls');
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onManualRequest]);

  const addTerminalLine = (line: TerminalLine) => {
    setTerminalLines(prev => [...prev, line]);
  };

  const handleCommand = async (command: string) => {
    if (!command.trim()) return;

    // Add command to terminal
    addTerminalLine({ 
      type: 'command', 
      content: `$ ${command}`,
      timestamp: new Date()
    });

    // Add to history
    setCommandHistory(prev => [...prev, command]);
    setHistoryIndex(-1);

    try {
      const result = await executeCommand(command, currentDirectory);
      
      // Handle special commands
      if (command.trim() === 'clear') {
        setTerminalLines([
          { type: 'output', content: 'UNIX V7 (Bell Telephone Laboratories)' },
          { type: 'output', content: '' },
        ]);
        return;
      }

      if (command.startsWith('cd ')) {
        const newDir = command.substring(3).trim();
        if (newDir && result.exitCode === 0) {
          onDirectoryChange(newDir.startsWith('/') ? newDir : `${currentDirectory}/${newDir}`);
        }
      }

      if (command.startsWith('man ')) {
        const manCommand = command.substring(4).trim();
        onManualRequest(manCommand);
      }

      // Add output to terminal
      if (result.output) {
        result.output.split('\n').forEach(line => {
          addTerminalLine({ 
            type: result.exitCode === 0 ? 'output' : 'error', 
            content: line 
          });
        });
      }
    } catch (error) {
      addTerminalLine({ 
        type: 'error', 
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}` 
      });
    }
  };

  const handleInputKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleCommand(currentInput);
      setCurrentInput("");
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (commandHistory.length > 0) {
        const newIndex = historyIndex === -1 ? commandHistory.length - 1 : Math.max(0, historyIndex - 1);
        setHistoryIndex(newIndex);
        setCurrentInput(commandHistory[newIndex]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex >= 0) {
        const newIndex = historyIndex + 1;
        if (newIndex >= commandHistory.length) {
          setHistoryIndex(-1);
          setCurrentInput("");
        } else {
          setHistoryIndex(newIndex);
          setCurrentInput(commandHistory[newIndex]);
        }
      }
    } else if (e.key === 'Tab') {
      e.preventDefault();
      // Basic tab completion for common commands
      const commonCommands = ['ls', 'cat', 'grep', 'ps', 'who', 'date', 'pwd', 'man', 'clear', 'help'];
      const matches = commonCommands.filter(cmd => cmd.startsWith(currentInput));
      if (matches.length === 1) {
        setCurrentInput(matches[0] + ' ');
      }
    }
  };

  const getLineClass = (type: string) => {
    switch (type) {
      case 'command':
        return 'text-terminal-green';
      case 'error':
        return 'text-red-400';
      case 'output':
      default:
        return 'text-phosphor';
    }
  };

  return (
    <div className="flex-1 crt-screen flex flex-col relative z-0">
      {/* Terminal output area */}
      <div 
        ref={terminalRef}
        className="flex-1 p-4 overflow-auto terminal-output"
      >
        <div className="space-y-1">
          {terminalLines.map((line, index) => (
            <div 
              key={index} 
              className={`${getLineClass(line.type)} text-sm font-mono leading-tight`}
            >
              {line.content || '\u00A0'}
            </div>
          ))}
        </div>
      </div>

      {/* Command input area */}
      <div className="border-t border-terminal-green bg-terminal-black p-4">
        <div className="flex items-center space-x-2">
          <span className="text-terminal-amber">$</span>
          <input 
            ref={inputRef}
            type="text" 
            value={currentInput}
            onChange={(e) => setCurrentInput(e.target.value)}
            onKeyDown={handleInputKeyDown}
            className="flex-1 bg-transparent text-terminal-green border-none outline-none font-mono"
            placeholder="Enter UNIX command..."
            autoComplete="off"
          />
          <span className="animate-blink text-terminal-green">█</span>
        </div>
        
        {/* Command suggestions */}
        <div className="mt-2 text-xs text-phosphor">
          Common commands: ls, ps, who, date, cat, grep, sed, awk, cp, mv, rm, mkdir, rmdir, cd, pwd, man
        </div>
      </div>
    </div>
  );
}

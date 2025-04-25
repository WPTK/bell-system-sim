import React, { useState, useRef, useEffect } from 'react';

interface CommandInputProps {
  prompt: string;
  onSubmit: (command: string) => void;
  hideInput?: boolean;
  className?: string;
}

const CommandInput: React.FC<CommandInputProps> = ({ 
  prompt, 
  onSubmit, 
  hideInput = false,
  className
}) => {
  const [command, setCommand] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Focus input on mount and when clicked outside
  useEffect(() => {
    inputRef.current?.focus();
    
    const handleClick = () => {
      inputRef.current?.focus();
    };
    
    document.addEventListener('click', handleClick);
    
    return () => {
      document.removeEventListener('click', handleClick);
    };
  }, []);

  // Handle command submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(command);
    setCommand('');
  };

  // Prevent clicks from propagating outside the input wrapper
  const handleWrapperClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    inputRef.current?.focus();
  };

  return (
    <form onSubmit={handleSubmit} className={className}>
      <div 
        ref={wrapperRef}
        className="flex items-center" 
        onClick={handleWrapperClick}
      >
        <span className="text-primary mr-2">{prompt}</span>
        <input
          ref={inputRef}
          type="text"
          className="bg-transparent flex-1 outline-none"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          autoComplete="off"
          spellCheck="false"
          autoFocus
          aria-label="Command input"
          style={{ 
            color: hideInput ? 'transparent' : 'inherit',
            caretColor: 'white' 
          }}
        />
        <span className="terminal-cursor">|</span>
      </div>
    </form>
  );
};

export default CommandInput;

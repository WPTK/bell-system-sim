import React from 'react';

interface TerminalOutputProps {
  lines: string[];
  className?: string;
}

const TerminalOutput: React.FC<TerminalOutputProps> = ({ lines, className }) => {
  // Function to colorize output based on content
  const colorizeOutput = (line: string) => {
    // Colorize command prompt lines
    if (line.startsWith('$ ')) {
      const promptPart = line.substring(0, 2);
      const commandPart = line.substring(2);
      
      return (
        <>
          <span>{promptPart}</span>
          <span className="text-accent">{commandPart}</span>
        </>
      );
    }
    
    // Colorize error messages (typically start with a command name followed by colon)
    if (/^[a-z]+: /.test(line) && line.includes('error') || line.includes('not found') || line.includes('No such')) {
      return <span className="text-error">{line}</span>;
    }
    
    // Colorize login prompt
    if (line.startsWith('login: ')) {
      const promptPart = line.substring(0, 7);
      const userPart = line.substring(7);
      
      return (
        <>
          <span>{promptPart}</span>
          <span className="text-accent">{userPart}</span>
        </>
      );
    }
    
    // Default - no special coloring
    return line;
  };

  return (
    <pre className={`terminal-output font-mono text-sm m-0 whitespace-pre-wrap ${className}`}>
      {lines.map((line, index) => (
        <div key={index} className="leading-tight">
          {colorizeOutput(line)}
        </div>
      ))}
    </pre>
  );
};

export default TerminalOutput;

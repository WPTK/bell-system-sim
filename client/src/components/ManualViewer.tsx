import React, { useState } from 'react';
import { getManPage } from '@/lib/manpages';

interface ManualViewerProps {
  initialCommand?: string;
  onClose?: () => void;
  className?: string;
}

const ManualViewer: React.FC<ManualViewerProps> = ({ 
  initialCommand, 
  onClose,
  className 
}) => {
  const [command, setCommand] = useState(initialCommand || '');
  const [manPage, setManPage] = useState<string | null>(
    initialCommand ? getManPage(initialCommand) : null
  );
  const [error, setError] = useState<string | null>(null);

  // Load manual page
  const loadManPage = () => {
    if (!command.trim()) {
      setError('Please enter a command name');
      setManPage(null);
      return;
    }
    
    const page = getManPage(command.trim());
    
    if (page) {
      setManPage(page);
      setError(null);
    } else {
      setError(`No manual entry for ${command.trim()}`);
      setManPage(null);
    }
  };

  return (
    <div className={`bg-card border border-ring rounded-md overflow-hidden flex flex-col ${className}`}>
      <div className="p-3 border-b border-ring flex justify-between items-center">
        <h2 className="text-lg font-bold">Manual Viewer</h2>
        {onClose && (
          <button 
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
            aria-label="Close"
          >
            ×
          </button>
        )}
      </div>
      
      <div className="p-3 border-b border-ring flex">
        <input
          type="text"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          className="flex-1 bg-background border border-ring p-1 px-2 rounded mr-2"
          placeholder="Enter command name"
        />
        <button 
          onClick={loadManPage}
          className="bg-primary text-primary-foreground px-3 py-1 rounded hover:opacity-90"
        >
          View
        </button>
      </div>
      
      <div className="flex-1 p-3 overflow-y-auto terminal-custom-scrollbar">
        {error && (
          <div className="text-error mb-3">{error}</div>
        )}
        
        {manPage && (
          <pre className="whitespace-pre-wrap font-mono text-sm">{manPage}</pre>
        )}
        
        {!manPage && !error && (
          <div className="text-center py-4 text-muted-foreground">
            Enter a command name to view its manual page
          </div>
        )}
      </div>
    </div>
  );
};

export default ManualViewer;

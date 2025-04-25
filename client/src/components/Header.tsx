import React from 'react';

interface HeaderProps {
  onHelpClick?: () => void;
  onSettingsClick?: () => void;
}

const Header: React.FC<HeaderProps> = ({ onHelpClick, onSettingsClick }) => {
  return (
    <header className="bg-card border-b border-ring p-2 flex justify-between items-center">
      <div className="flex items-center">
        <h1 className="text-xl font-bold mr-4">UNIX V7 Simulator</h1>
        <div className="text-xs text-muted-foreground">Bell Laboratories, 1979</div>
      </div>
      
      <div className="flex space-x-4">
        <button 
          onClick={onHelpClick}
          className="px-3 py-1 text-sm border border-ring rounded hover:bg-ring"
        >
          Help
        </button>
        <button 
          onClick={onSettingsClick}
          className="px-3 py-1 text-sm border border-ring rounded hover:bg-ring"
        >
          Settings
        </button>
      </div>
    </header>
  );
};

export default Header;

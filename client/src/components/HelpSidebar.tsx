import React from 'react';

interface HelpSidebarProps {
  className?: string;
}

const HelpSidebar: React.FC<HelpSidebarProps> = ({ className }) => {
  return (
    <aside className={`w-64 bg-card border-l border-ring overflow-y-auto terminal-custom-scrollbar ${className}`}>
      <div className="p-3 border-b border-ring">
        <h2 className="text-sm font-bold">Quick Reference</h2>
      </div>
      
      <div className="p-3">
        <h3 className="text-xs font-bold mb-2">Common Commands</h3>
        <ul className="text-xs space-y-2">
          <li><span className="text-accent">ls</span> - list directory contents</li>
          <li><span className="text-accent">cd</span> - change directory</li>
          <li><span className="text-accent">pwd</span> - print working directory</li>
          <li><span className="text-accent">cp</span> - copy files</li>
          <li><span className="text-accent">mv</span> - move files</li>
          <li><span className="text-accent">rm</span> - remove files</li>
          <li><span className="text-accent">cat</span> - concatenate files</li>
          <li><span className="text-accent">grep</span> - search text</li>
          <li><span className="text-accent">man</span> - manual pages</li>
        </ul>
        
        <h3 className="text-xs font-bold mt-4 mb-2">Special Characters</h3>
        <ul className="text-xs space-y-2">
          <li><span className="text-accent">|</span> - pipe output</li>
          <li><span className="text-accent">&gt;</span> - redirect output</li>
          <li><span className="text-accent">&gt;&gt;</span> - append output</li>
          <li><span className="text-accent">&lt;</span> - input from file</li>
          <li><span className="text-accent">*</span> - wildcard</li>
          <li><span className="text-accent">^D</span> - end of input</li>
          <li><span className="text-accent">^C</span> - interrupt</li>
        </ul>
      </div>
    </aside>
  );
};

export default HelpSidebar;

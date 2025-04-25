import React from 'react';
import FileExplorer from './FileExplorer';
import { VirtualFileSystem } from '@/lib/filesystem';

interface SidebarProps {
  fs: VirtualFileSystem;
  onFileSelect?: (path: string) => void;
  className?: string;
}

const Sidebar: React.FC<SidebarProps> = ({ fs, onFileSelect, className }) => {
  return (
    <aside className={`w-56 bg-card border-r border-ring overflow-y-auto terminal-custom-scrollbar ${className}`}>
      <FileExplorer 
        fs={fs} 
        onFileSelect={onFileSelect}
      />
    </aside>
  );
};

export default Sidebar;

import React, { useState, useEffect } from 'react';
import { VirtualFileSystem, FileSystemEntry } from '@/lib/filesystem';

interface FileExplorerProps {
  fs: VirtualFileSystem;
  onFileSelect?: (path: string) => void;
  className?: string;
}

const FileExplorer: React.FC<FileExplorerProps> = ({ 
  fs, 
  onFileSelect,
  className
}) => {
  const [currentPath, setCurrentPath] = useState('/');
  const [entries, setEntries] = useState<FileSystemEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load directory contents when path changes
  useEffect(() => {
    const loadDirectory = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const dirEntries = await fs.readdir(currentPath);
        setEntries(dirEntries);
      } catch (err) {
        setError(`Failed to read directory: ${err instanceof Error ? err.message : String(err)}`);
        setEntries([]);
      } finally {
        setLoading(false);
      }
    };
    
    loadDirectory();
  }, [currentPath, fs]);

  // Navigate to a directory
  const navigateToDirectory = (dirPath: string) => {
    setCurrentPath(dirPath);
  };

  // Navigate to parent directory
  const navigateToParent = () => {
    if (currentPath === '/') return;
    
    const parentPath = currentPath.split('/').slice(0, -1).join('/') || '/';
    setCurrentPath(parentPath);
  };

  // Handle file/directory click
  const handleEntryClick = (entry: FileSystemEntry) => {
    if (entry.isDirectory) {
      navigateToDirectory(entry.path);
    } else if (onFileSelect) {
      onFileSelect(entry.path);
    }
  };

  return (
    <div className={`p-3 bg-card ${className}`}>
      <div className="border-b border-border pb-2 mb-3">
        <h2 className="text-sm font-bold mb-2">File System</h2>
        <div className="flex items-center text-xs text-muted-foreground">
          <span>Current: </span>
          <span className="ml-1 text-foreground">{currentPath}</span>
        </div>
      </div>
      
      {loading ? (
        <div className="text-center py-4 text-muted-foreground">Loading...</div>
      ) : error ? (
        <div className="text-error py-2 text-sm">{error}</div>
      ) : (
        <div>
          {currentPath !== '/' && (
            <div 
              className="py-1 px-2 cursor-pointer hover:bg-ring text-sm"
              onClick={navigateToParent}
            >
              ..
            </div>
          )}
          
          <div className="mb-4">
            <h3 className="text-xs text-muted-foreground mb-1">Directories</h3>
            <ul className="text-sm">
              {entries
                .filter(entry => entry.isDirectory)
                .map(entry => (
                  <li 
                    key={entry.path}
                    className="py-1 px-2 hover:bg-ring cursor-pointer"
                    onClick={() => handleEntryClick(entry)}
                  >
                    {entry.name}
                  </li>
                ))}
            </ul>
          </div>
          
          <div>
            <h3 className="text-xs text-muted-foreground mb-1">Files</h3>
            <ul className="text-sm">
              {entries
                .filter(entry => !entry.isDirectory)
                .map(entry => (
                  <li 
                    key={entry.path}
                    className="py-1 px-2 hover:bg-ring cursor-pointer"
                    onClick={() => handleEntryClick(entry)}
                  >
                    {entry.name}
                  </li>
                ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileExplorer;

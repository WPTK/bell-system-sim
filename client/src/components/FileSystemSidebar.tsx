import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import type { File } from "@shared/schema";

interface FileSystemSidebarProps {
  currentDirectory: string;
  onDirectoryChange: (dir: string) => void;
}

export default function FileSystemSidebar({ 
  currentDirectory, 
  onDirectoryChange 
}: FileSystemSidebarProps) {
  const [expandedDirectories, setExpandedDirectories] = useState<Set<string>>(new Set(["/"]));
  const [systemStats, setSystemStats] = useState({
    users: 3,
    load: 0.15,
    uptime: "2 days",
    memory: "128K"
  });

  // Fetch files for the current directory
  const { data: files = [], isLoading } = useQuery<File[]>({
    queryKey: ['/api/files', currentDirectory],
  });

  // Fetch root directory files for the tree view
  const { data: rootFiles = [] } = useQuery<File[]>({
    queryKey: ['/api/files', '/'],
  });

  useEffect(() => {
    // Simulate changing system stats
    const interval = setInterval(() => {
      setSystemStats(prev => ({
        ...prev,
        load: Math.max(0.05, Math.random() * 2),
        users: Math.floor(Math.random() * 5) + 1,
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const toggleDirectory = (path: string) => {
    const newExpanded = new Set(expandedDirectories);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedDirectories(newExpanded);
  };

  const handleDirectoryClick = (path: string) => {
    onDirectoryChange(path);
    if (!expandedDirectories.has(path)) {
      toggleDirectory(path);
    }
  };

  const renderFileTree = (files: File[], parentPath: string = "/", level: number = 0) => {
    return files
      .filter(file => file.parentPath === parentPath)
      .sort((a, b) => {
        // Directories first, then alphabetical
        if (a.isDirectory && !b.isDirectory) return -1;
        if (!a.isDirectory && b.isDirectory) return 1;
        return a.name.localeCompare(b.name);
      })
      .map(file => (
        <div key={file.path} className={`ml-${level * 4}`}>
          <div 
            className={`cursor-pointer hover:text-terminal-amber flex items-center py-1 ${
              currentDirectory === file.path ? 'text-terminal-amber' : ''
            }`}
            onClick={() => file.isDirectory ? handleDirectoryClick(file.path) : null}
          >
            <span className="mr-1">
              {file.isDirectory ? 
                (expandedDirectories.has(file.path) ? '📂' : '📁') : 
                '📄'
              }
            </span>
            <span className="text-xs">{file.name || '/'}</span>
          </div>
          {file.isDirectory && expandedDirectories.has(file.path) && (
            <div className="ml-2">
              {renderFileTree(files, file.path, level + 1)}
            </div>
          )}
        </div>
      ));
  };

  const quickCommands = [
    { name: 'ls -la', description: 'list files' },
    { name: 'ps', description: 'processes' },
    { name: 'who', description: 'users' },
    { name: 'date', description: 'time' },
    { name: 'cat /etc/motd', description: 'motd - message' },
  ];

  return (
    <div className="w-1/4 border-r border-terminal-green bg-crt-dark p-4 overflow-auto">
      <div className="mb-4">
        <h3 className="text-terminal-green font-bold mb-2">FILE SYSTEM</h3>
        <div className="text-xs text-phosphor">
          {isLoading ? (
            <div>Loading...</div>
          ) : (
            renderFileTree([...rootFiles, ...files])
          )}
        </div>
      </div>
      
      <div className="mb-4">
        <h3 className="text-terminal-green font-bold mb-2">SYSTEM INFO</h3>
        <div className="text-xs text-phosphor space-y-1">
          <div>Users: <span>{systemStats.users}</span></div>
          <div>Load: <span>{systemStats.load.toFixed(2)}</span></div>
          <div>Uptime: <span>{systemStats.uptime}</span></div>
          <div>Free: <span>{systemStats.memory}</span></div>
        </div>
      </div>

      <div>
        <h3 className="text-terminal-green font-bold mb-2">COMMANDS</h3>
        <div className="text-xs text-phosphor space-y-1">
          {quickCommands.map((cmd, index) => (
            <div 
              key={index}
              className="cursor-pointer hover:text-terminal-amber" 
              onClick={() => {
                // Trigger command execution
                const event = new CustomEvent('quick-command', { detail: cmd.name });
                document.dispatchEvent(event);
              }}
            >
              {cmd.description}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

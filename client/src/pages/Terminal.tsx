import { useState } from "react";
import TerminalScreen from "@/components/TerminalScreen";
import FileSystemSidebar from "@/components/FileSystemSidebar";
import ManualPanel from "@/components/ManualPanel";

export default function Terminal() {
  const [showManual, setShowManual] = useState(false);
  const [currentDirectory, setCurrentDirectory] = useState("/root");
  const [selectedCommand, setSelectedCommand] = useState<string | null>(null);

  const handleManualToggle = () => {
    setShowManual(!showManual);
  };

  const handleCommandSelect = (command: string) => {
    setSelectedCommand(command);
    setShowManual(true);
  };

  return (
    <div className="h-screen bg-terminal-black text-terminal-green font-mono overflow-hidden">
      {/* Header with Bell Labs branding */}
      <header className="bg-black border-b border-terminal-green p-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="text-terminal-green text-lg font-bold">UNIX V7 Terminal</div>
            <div className="text-terminal-amber text-sm">Bell Telephone Laboratories</div>
          </div>
          <div className="flex items-center space-x-4 text-sm">
            <span>Version 7</span>
            <span>March 10, 1976</span>
            <span className="text-yellow-400">root</span>
          </div>
        </div>
      </header>

      {/* Main terminal interface */}
      <div className="flex h-full bg-terminal-black">
        {/* File system sidebar */}
        <FileSystemSidebar 
          currentDirectory={currentDirectory}
          onDirectoryChange={setCurrentDirectory}
        />

        {/* Main terminal area */}
        <div className="flex-1 flex flex-col relative">
          {/* CRT screen effect overlay */}
          <div className="scanlines absolute inset-0 pointer-events-none z-10"></div>
          
          <TerminalScreen 
            currentDirectory={currentDirectory}
            onDirectoryChange={setCurrentDirectory}
            onManualRequest={handleCommandSelect}
          />
        </div>

        {/* Manual/Help panel (toggleable) */}
        {showManual && (
          <ManualPanel 
            selectedCommand={selectedCommand}
            onClose={() => setShowManual(false)}
          />
        )}
      </div>

      {/* Footer with system status */}
      <footer className="bg-black border-t border-terminal-green p-2">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center space-x-4">
            <span>Bell System Technical Journal, March 1976</span>
            <span className="text-terminal-amber">F1: Help</span>
            <span className="text-terminal-amber">F2: Manual</span>
            <span className="text-terminal-amber">F3: Files</span>
          </div>
          <div className="flex items-center space-x-4">
            <span>{new Date().toLocaleTimeString()}</span>
            <span className="text-green-400">●</span>
            <span>Connected</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

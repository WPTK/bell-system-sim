import React, { useState, useRef, useEffect } from 'react';
import Terminal from '@/components/Terminal';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import Sidebar from '@/components/Sidebar';
import HelpSidebar from '@/components/HelpSidebar';
import HelpModal from '@/components/HelpModal';
import ManualViewer from '@/components/ManualViewer';
import { VirtualFileSystem } from '@/lib/filesystem';
import { useTerminal } from '@/hooks/useTerminal';
import { useMobile } from '@/hooks/use-mobile';

const Home: React.FC = () => {
  const [fs] = useState(() => new VirtualFileSystem('/usr/you'));
  const [isHelpModalOpen, setIsHelpModalOpen] = useState(false);
  const [isManualOpen, setIsManualOpen] = useState(false);
  const [manualCommand, setManualCommand] = useState('');
  const isMobile = useMobile();
  const terminalRef = useRef<HTMLDivElement>(null);

  // Initialize terminal state and actions
  const [terminalState, terminalActions] = useTerminal({
    autoLogin: true,
    initialDirectory: '/usr/you'
  });

  // Focus terminal on click anywhere in the page
  useEffect(() => {
    const handleClick = () => {
      if (terminalRef.current) {
        // Find the input element within the terminal and focus it
        const input = terminalRef.current.querySelector('input');
        if (input) input.focus();
      }
    };
    
    document.addEventListener('click', handleClick);
    
    return () => {
      document.removeEventListener('click', handleClick);
    };
  }, []);

  // Handle help button click
  const handleHelpClick = () => {
    setIsHelpModalOpen(true);
  };

  // Handle settings button click (not implemented yet)
  const handleSettingsClick = () => {
    // In a real implementation, this would open a settings modal
    terminalActions.executeCommand('echo "Settings functionality not implemented"');
  };

  // Handle file selection from sidebar
  const handleFileSelect = async (path: string) => {
    try {
      const fileName = path.split('/').pop() || '';
      terminalActions.executeCommand(`cat ${fileName}`);
    } catch (error) {
      console.error('Failed to open file:', error);
    }
  };

  // Handle manual page request
  const handleManualRequest = (command: string) => {
    setManualCommand(command);
    setIsManualOpen(true);
  };

  return (
    <div className="bg-background text-foreground font-mono h-screen flex flex-col overflow-hidden">
      {/* Header */}
      <Header 
        onHelpClick={handleHelpClick} 
        onSettingsClick={handleSettingsClick} 
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - File Explorer (hidden on mobile) */}
        {!isMobile && (
          <Sidebar 
            fs={fs} 
            onFileSelect={handleFileSelect} 
            className="hidden md:block" 
          />
        )}

        {/* Main Terminal */}
        <main 
          ref={terminalRef}
          className="flex-1 flex flex-col overflow-hidden"
        >
          <Terminal 
            initialFs={fs} 
            className="flex-1" 
          />
        </main>

        {/* Right Sidebar - Help Reference (hidden on mobile) */}
        {!isMobile && (
          <HelpSidebar className="hidden lg:block" />
        )}
      </div>

      {/* Footer */}
      <Footer 
        username={terminalState.user?.username} 
        tty="tty01" 
      />

      {/* Help Modal */}
      <HelpModal 
        isOpen={isHelpModalOpen} 
        onClose={() => setIsHelpModalOpen(false)} 
      />

      {/* Manual Viewer (conditionally rendered) */}
      {isManualOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <ManualViewer 
            initialCommand={manualCommand}
            onClose={() => setIsManualOpen(false)}
            className="w-full max-w-3xl max-h-[80vh]"
          />
        </div>
      )}
    </div>
  );
};

export default Home;

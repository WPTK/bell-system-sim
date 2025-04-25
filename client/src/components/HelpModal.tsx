import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';

interface HelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const HelpModal: React.FC<HelpModalProps> = ({ isOpen, onClose }) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-card border border-ring text-foreground max-w-2xl max-h-[80vh] overflow-y-auto terminal-custom-scrollbar">
        <DialogHeader>
          <DialogTitle className="text-lg font-bold">UNIX V7 Simulator Help</DialogTitle>
        </DialogHeader>
        
        <div className="prose text-foreground">
          <h3 className="text-accent">About UNIX V7</h3>
          <p className="text-sm">
            Version 7 UNIX (released in 1979) was the last Bell Laboratories release widely distributed to educational institutions. 
            It introduced many features that became standard in later UNIX systems and derivatives.
          </p>
          
          <h3 className="text-accent mt-4">Using this Simulator</h3>
          <p className="text-sm">
            This simulator recreates the core functionality of UNIX V7. Type commands at the prompt and press Enter to execute.
            The simulator supports standard command-line utilities, I/O redirection, pipes, and file operations.
          </p>
          
          <h3 className="text-accent mt-4">Key Commands</h3>
          <div className="text-sm">
            <ul className="space-y-1">
              <li><code className="text-accent">ls</code> - List directory contents</li>
              <li><code className="text-accent">cd</code> - Change directory</li>
              <li><code className="text-accent">pwd</code> - Print working directory</li>
              <li><code className="text-accent">cat</code> - Display file contents</li>
              <li><code className="text-accent">grep</code> - Search for patterns in files</li>
              <li><code className="text-accent">mkdir</code> - Create directories</li>
              <li><code className="text-accent">rm</code> - Remove files or directories</li>
              <li><code className="text-accent">cp</code> - Copy files</li>
              <li><code className="text-accent">mv</code> - Move or rename files</li>
              <li><code className="text-accent">chmod</code> - Change file permissions</li>
              <li><code className="text-accent">man</code> - Display manual pages</li>
            </ul>
          </div>
          
          <h3 className="text-accent mt-4">I/O Redirection & Pipes</h3>
          <p className="text-sm">
            UNIX V7 pioneered many features for command input/output manipulation:
          </p>
          <div className="text-sm">
            <ul className="space-y-1">
              <li><code className="text-accent">command > file</code> - Redirect output to a file</li>
              <li><code className="text-accent">command >> file</code> - Append output to a file</li>
              <li><code className="text-accent">command < file</code> - Take input from a file</li>
              <li><code className="text-accent">command1 | command2</code> - Pipe output of command1 as input to command2</li>
            </ul>
          </div>
          
          <h3 className="text-accent mt-4">For More Information</h3>
          <p className="text-sm">
            Refer to the original Bell System Technical Journal or the UNIX Programmer's Manual for comprehensive documentation.
            Use the <code className="text-accent">man</code> command to access built-in documentation.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default HelpModal;

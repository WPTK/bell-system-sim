import React, { useState, useEffect } from 'react';

interface FooterProps {
  username?: string;
  tty?: string;
}

const Footer: React.FC<FooterProps> = ({ 
  username = 'you',
  tty = 'tty01'
}) => {
  const [time, setTime] = useState<string>('');
  
  // Update clock every second
  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      const hours = now.getHours().toString().padStart(2, '0');
      const minutes = now.getMinutes().toString().padStart(2, '0');
      const seconds = now.getSeconds().toString().padStart(2, '0');
      
      setTime(`${hours}:${minutes}:${seconds}`);
    };
    
    updateClock();
    const interval = setInterval(updateClock, 1000);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <footer className="py-1 px-3 text-xs text-muted-foreground border-t border-ring flex justify-between">
      <div>UNIX V7 Simulator - Based on Bell Labs UNIX (1979)</div>
      <div className="flex space-x-4">
        <span>{tty}</span>
        <span>user: {username}</span>
        <span>{time}</span>
      </div>
    </footer>
  );
};

export default Footer;

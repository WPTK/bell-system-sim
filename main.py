
import os
import time
from datetime import datetime

class UnixTerminal:
    def __init__(self):
        self.username = ""
        self.hostname = "pdp11"
        self.current_dir = "/usr/home"
    
    def show_login(self):
        print("\033[2J\033[H")  # Clear screen
        print("UNIX V7 Release 1")
        print(f"{self.hostname} login: ", end='', flush=True)
        self.username = input()
        print("Password: ", end='', flush=True)
        input()  # Simple password simulation
        
        # Show MOTD
        print("\nBell System UNIX/TS 1.0")
        print("Internal Use Only - AT&T Proprietary")
        print(f"Last login: {datetime.now().strftime('%a %b %d %H:%M:%S')}")
        
    def run(self):
        self.show_login()
        while True:
            print(f"$ ", end='', flush=True)
            cmd = input().strip()
            if cmd == "exit":
                break
            self.handle_command(cmd)
    
    def handle_command(self, cmd):
        if cmd == "who":
            print(f"{self.username}  tty1  {datetime.now().strftime('%b %d %H:%M')}")
        elif cmd == "pwd":
            print(self.current_dir)
        elif cmd == "date":
            print(datetime.now().strftime('%a %b %d %H:%M:%S EDT %Y'))

if __name__ == "__main__":
    terminal = UnixTerminal()
    terminal.run()

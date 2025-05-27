import type { File, Process } from "@shared/schema";

export interface CommandResult {
  output: string;
  exitCode: number;
  newDirectory?: string;
}

export interface CommandContext {
  currentDirectory: string;
  files: File[];
  processes: Process[];
  user: string;
}

export class UnixCommands {
  private static formatFileList(files: File[], longFormat: boolean = false, showAll: boolean = false): string {
    let filteredFiles = files;
    
    if (!showAll) {
      filteredFiles = files.filter(file => !file.name.startsWith('.'));
    }

    if (longFormat) {
      const lines = filteredFiles.map(file => {
        const type = file.isDirectory ? 'd' : '-';
        const perms = file.permissions.slice(1); // Remove the first character which is type
        const size = file.size.toString().padStart(8);
        const date = file.modifiedAt.toLocaleDateString('en-US', { 
          month: 'short', 
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        });
        return `${type}${perms}  1 ${file.owner.padEnd(8)} ${file.group.padEnd(8)} ${size} ${date} ${file.name}`;
      });
      
      const total = filteredFiles.reduce((sum, file) => sum + Math.ceil(file.size / 512), 0);
      return `total ${total}\n${lines.join('\n')}`;
    } else {
      return filteredFiles.map(file => file.name).join('  ');
    }
  }

  private static parsePath(path: string, currentDirectory: string): string {
    if (path.startsWith('/')) {
      return path;
    }
    if (path === '..') {
      const parts = currentDirectory.split('/').filter(p => p);
      parts.pop();
      return '/' + parts.join('/');
    }
    if (path === '.') {
      return currentDirectory;
    }
    return currentDirectory === '/' ? `/${path}` : `${currentDirectory}/${path}`;
  }

  static async ls(args: string[], context: CommandContext): Promise<CommandResult> {
    const flags = args.filter(arg => arg.startsWith('-')).join('');
    const paths = args.filter(arg => !arg.startsWith('-'));
    const targetPath = paths.length > 0 ? this.parsePath(paths[0], context.currentDirectory) : context.currentDirectory;
    
    const longFormat = flags.includes('l');
    const showAll = flags.includes('a');
    const sortByTime = flags.includes('t');
    const reverse = flags.includes('r');

    // Get files in the target directory
    const filesInDir = context.files.filter(file => file.parentPath === targetPath);
    
    if (filesInDir.length === 0 && targetPath !== '/') {
      return {
        output: `ls: ${targetPath}: No such file or directory`,
        exitCode: 1
      };
    }

    let sortedFiles = [...filesInDir];
    
    if (sortByTime) {
      sortedFiles.sort((a, b) => b.modifiedAt.getTime() - a.modifiedAt.getTime());
    } else {
      sortedFiles.sort((a, b) => a.name.localeCompare(b.name));
    }
    
    if (reverse) {
      sortedFiles.reverse();
    }

    return {
      output: this.formatFileList(sortedFiles, longFormat, showAll),
      exitCode: 0
    };
  }

  static async cat(args: string[], context: CommandContext): Promise<CommandResult> {
    if (args.length === 0) {
      return {
        output: "cat: missing file operand",
        exitCode: 1
      };
    }

    const results: string[] = [];
    for (const arg of args.filter(a => !a.startsWith('-'))) {
      const filePath = this.parsePath(arg, context.currentDirectory);
      const file = context.files.find(f => f.path === filePath);
      
      if (!file) {
        results.push(`cat: ${arg}: No such file or directory`);
        continue;
      }
      
      if (file.isDirectory) {
        results.push(`cat: ${arg}: Is a directory`);
        continue;
      }
      
      results.push(file.content || '');
    }

    return {
      output: results.join('\n'),
      exitCode: results.some(r => r.includes('No such file')) ? 1 : 0
    };
  }

  static async pwd(args: string[], context: CommandContext): Promise<CommandResult> {
    return {
      output: context.currentDirectory,
      exitCode: 0
    };
  }

  static async ps(args: string[], context: CommandContext): Promise<CommandResult> {
    const showAll = args.includes('a') || args.includes('-a');
    const longFormat = args.includes('l') || args.includes('-l');
    
    let processes = context.processes;
    if (!showAll) {
      processes = processes.filter(p => p.tty && p.tty !== '?');
    }

    const header = longFormat ? 
      "  PID TTY      TIME CMD" : 
      "  PID TTY      TIME CMD";
    
    const lines = processes.map(p => {
      const pid = p.pid.toString().padStart(5);
      const tty = (p.tty || '?').padEnd(8);
      const time = p.time.padEnd(8);
      return `${pid} ${tty} ${time} ${p.command}`;
    });

    return {
      output: `${header}\n${lines.join('\n')}`,
      exitCode: 0
    };
  }

  static async who(args: string[], context: CommandContext): Promise<CommandResult> {
    const users = [
      "root     console  Mar 10 08:30",
      "dmr      tty01    Mar 10 09:15", 
      "ken      tty02    Mar 10 07:45"
    ];

    return {
      output: users.join('\n'),
      exitCode: 0
    };
  }

  static async date(args: string[], context: CommandContext): Promise<CommandResult> {
    return {
      output: new Date().toString(),
      exitCode: 0
    };
  }

  static async grep(args: string[], context: CommandContext): Promise<CommandResult> {
    if (args.length < 1) {
      return {
        output: "grep: missing pattern",
        exitCode: 1
      };
    }

    const flags = args.filter(arg => arg.startsWith('-')).join('');
    const nonFlagArgs = args.filter(arg => !arg.startsWith('-'));
    const pattern = nonFlagArgs[0];
    const files = nonFlagArgs.slice(1);

    if (files.length === 0) {
      return {
        output: "grep: missing file operand",
        exitCode: 1
      };
    }

    const results: string[] = [];
    const showLineNumbers = flags.includes('n');
    const invert = flags.includes('v');
    const countOnly = flags.includes('c');

    for (const fileName of files) {
      const filePath = this.parsePath(fileName, context.currentDirectory);
      const file = context.files.find(f => f.path === filePath);
      
      if (!file) {
        results.push(`grep: ${fileName}: No such file or directory`);
        continue;
      }

      if (file.isDirectory) {
        results.push(`grep: ${fileName}: Is a directory`);
        continue;
      }

      const lines = (file.content || '').split('\n');
      const matches: string[] = [];
      
      lines.forEach((line, index) => {
        const matchesPattern = line.includes(pattern);
        const shouldInclude = invert ? !matchesPattern : matchesPattern;
        
        if (shouldInclude) {
          if (showLineNumbers) {
            matches.push(`${index + 1}:${line}`);
          } else {
            matches.push(line);
          }
        }
      });

      if (countOnly) {
        results.push(`${matches.length}`);
      } else if (matches.length > 0) {
        if (files.length > 1) {
          results.push(...matches.map(match => `${fileName}:${match}`));
        } else {
          results.push(...matches);
        }
      }
    }

    return {
      output: results.join('\n'),
      exitCode: results.length > 0 ? 0 : 1
    };
  }

  static async cd(args: string[], context: CommandContext): Promise<CommandResult> {
    const targetPath = args.length > 0 ? this.parsePath(args[0], context.currentDirectory) : '/root';
    
    const targetDir = context.files.find(f => f.path === targetPath && f.isDirectory);
    if (!targetDir) {
      return {
        output: `cd: ${args[0] || 'home'}: No such file or directory`,
        exitCode: 1
      };
    }

    return {
      output: '',
      exitCode: 0,
      newDirectory: targetPath
    };
  }

  static async help(args: string[], context: CommandContext): Promise<CommandResult> {
    const helpText = `Available commands:
ls      - list directory contents
cat     - display file contents  
pwd     - print working directory
ps      - show running processes
who     - show logged in users
date    - show current date and time
grep    - search text patterns
cd      - change directory
man     - display manual pages
clear   - clear terminal screen
help    - show this help message

Use 'man <command>' for detailed help on any command.
Example: man ls

Type 'man intro' for an introduction to the UNIX system.`;

    return {
      output: helpText,
      exitCode: 0
    };
  }

  static async man(args: string[], context: CommandContext): Promise<CommandResult> {
    if (args.length === 0) {
      return {
        output: "man: missing command name",
        exitCode: 1
      };
    }

    return {
      output: `Manual page for '${args[0]}' would be displayed in the manual panel.`,
      exitCode: 0
    };
  }

  static async clear(args: string[], context: CommandContext): Promise<CommandResult> {
    return {
      output: 'CLEAR_SCREEN',
      exitCode: 0
    };
  }

  static async echo(args: string[], context: CommandContext): Promise<CommandResult> {
    return {
      output: args.join(' '),
      exitCode: 0
    };
  }

  static async wc(args: string[], context: CommandContext): Promise<CommandResult> {
    if (args.length === 0) {
      return {
        output: "wc: missing file operand",
        exitCode: 1
      };
    }

    const results: string[] = [];
    for (const fileName of args.filter(a => !a.startsWith('-'))) {
      const filePath = this.parsePath(fileName, context.currentDirectory);
      const file = context.files.find(f => f.path === filePath);
      
      if (!file) {
        results.push(`wc: ${fileName}: No such file or directory`);
        continue;
      }
      
      if (file.isDirectory) {
        results.push(`wc: ${fileName}: Is a directory`);
        continue;
      }
      
      const content = file.content || '';
      const lines = content.split('\n').length - (content.endsWith('\n') ? 1 : 0);
      const words = content.trim() ? content.trim().split(/\s+/).length : 0;
      const chars = content.length;
      
      results.push(`${lines.toString().padStart(8)} ${words.toString().padStart(7)} ${chars.toString().padStart(7)} ${fileName}`);
    }

    return {
      output: results.join('\n'),
      exitCode: results.some(r => r.includes('No such file')) ? 1 : 0
    };
  }
}

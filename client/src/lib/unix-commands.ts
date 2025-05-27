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

  static async ed(args: string[], context: CommandContext): Promise<CommandResult> {
    const fileName = args[0];
    if (!fileName) {
      return {
        output: "?\n(enter 'q' to quit editor)",
        exitCode: 0
      };
    }
    
    const filePath = this.parsePath(fileName, context.currentDirectory);
    const file = context.files.find(f => f.path === filePath);
    
    if (file) {
      const lines = file.content ? file.content.split('\n').length : 0;
      return {
        output: `${lines}\n?`,
        exitCode: 0
      };
    } else {
      return {
        output: `${fileName}: No such file or directory\n?`,
        exitCode: 0
      };
    }
  }

  static async find(args: string[], context: CommandContext): Promise<CommandResult> {
    if (args.length === 0) {
      return {
        output: "find: missing path",
        exitCode: 1
      };
    }

    const searchPath = this.parsePath(args[0], context.currentDirectory);
    const namePattern = args.includes('-name') ? args[args.indexOf('-name') + 1] : null;
    const typeFilter = args.includes('-type') ? args[args.indexOf('-type') + 1] : null;

    const results: string[] = [];
    
    // Find files under the search path
    const matchingFiles = context.files.filter(file => {
      if (!file.path.startsWith(searchPath)) return false;
      
      if (namePattern && !file.name.includes(namePattern.replace('*', ''))) return false;
      
      if (typeFilter) {
        if (typeFilter === 'd' && !file.isDirectory) return false;
        if (typeFilter === 'f' && file.isDirectory) return false;
      }
      
      return true;
    });

    matchingFiles.forEach(file => results.push(file.path));

    return {
      output: results.join('\n'),
      exitCode: 0
    };
  }

  static async sort(args: string[], context: CommandContext): Promise<CommandResult> {
    if (args.length === 0) {
      return {
        output: "sort: missing file operand",
        exitCode: 1
      };
    }

    const fileName = args.filter(a => !a.startsWith('-'))[0];
    const filePath = this.parsePath(fileName, context.currentDirectory);
    const file = context.files.find(f => f.path === filePath);
    
    if (!file) {
      return {
        output: `sort: ${fileName}: No such file or directory`,
        exitCode: 1
      };
    }

    if (file.isDirectory) {
      return {
        output: `sort: ${fileName}: Is a directory`,
        exitCode: 1
      };
    }

    const content = file.content || '';
    const lines = content.split('\n').filter(line => line.length > 0);
    const reverse = args.includes('-r');
    
    lines.sort();
    if (reverse) lines.reverse();

    return {
      output: lines.join('\n'),
      exitCode: 0
    };
  }

  static async sed(args: string[], context: CommandContext): Promise<CommandResult> {
    if (args.length < 2) {
      return {
        output: "sed: missing operand",
        exitCode: 1
      };
    }

    const script = args[0];
    const fileName = args[1];
    const filePath = this.parsePath(fileName, context.currentDirectory);
    const file = context.files.find(f => f.path === filePath);
    
    if (!file) {
      return {
        output: `sed: ${fileName}: No such file or directory`,
        exitCode: 1
      };
    }

    // Simple s/old/new/ substitution
    if (script.startsWith('s/')) {
      const parts = script.split('/');
      if (parts.length >= 3) {
        const oldText = parts[1];
        const newText = parts[2];
        const content = file.content || '';
        const result = content.replace(new RegExp(oldText, 'g'), newText);
        
        return {
          output: result,
          exitCode: 0
        };
      }
    }

    return {
      output: file.content || '',
      exitCode: 0
    };
  }

  static async awk(args: string[], context: CommandContext): Promise<CommandResult> {
    if (args.length === 0) {
      return {
        output: "awk: missing program text",
        exitCode: 1
      };
    }

    const program = args[0];
    const fileName = args[1];
    
    if (!fileName) {
      return {
        output: "awk: missing file operand",
        exitCode: 1
      };
    }

    const filePath = this.parsePath(fileName, context.currentDirectory);
    const file = context.files.find(f => f.path === filePath);
    
    if (!file) {
      return {
        output: `awk: ${fileName}: No such file or directory`,
        exitCode: 1
      };
    }

    const content = file.content || '';
    const lines = content.split('\n');
    const results: string[] = [];

    // Simple pattern matching
    if (program === '{print}' || program === '{print $0}') {
      return {
        output: content,
        exitCode: 0
      };
    }

    if (program === '{print NF}') {
      lines.forEach(line => {
        const fields = line.trim().split(/\s+/);
        results.push(fields.length.toString());
      });
    } else if (program.includes('print $1')) {
      lines.forEach(line => {
        const fields = line.trim().split(/\s+/);
        results.push(fields[0] || '');
      });
    }

    return {
      output: results.join('\n'),
      exitCode: 0
    };
  }

  static async chmod(args: string[], context: CommandContext): Promise<CommandResult> {
    if (args.length < 2) {
      return {
        output: "chmod: missing operand",
        exitCode: 1
      };
    }

    const mode = args[0];
    const fileName = args[1];
    const filePath = this.parsePath(fileName, context.currentDirectory);
    const file = context.files.find(f => f.path === filePath);
    
    if (!file) {
      return {
        output: `chmod: ${fileName}: No such file or directory`,
        exitCode: 1
      };
    }

    // Simulate permission change (would update file in real system)
    return {
      output: '',
      exitCode: 0
    };
  }

  static async cp(args: string[], context: CommandContext): Promise<CommandResult> {
    if (args.length < 2) {
      return {
        output: "cp: missing operand",
        exitCode: 1
      };
    }

    const source = args[0];
    const dest = args[1];
    const sourcePath = this.parsePath(source, context.currentDirectory);
    const file = context.files.find(f => f.path === sourcePath);
    
    if (!file) {
      return {
        output: `cp: ${source}: No such file or directory`,
        exitCode: 1
      };
    }

    return {
      output: '',
      exitCode: 0
    };
  }

  static async mv(args: string[], context: CommandContext): Promise<CommandResult> {
    if (args.length < 2) {
      return {
        output: "mv: missing operand",
        exitCode: 1
      };
    }

    const source = args[0];
    const dest = args[1];
    const sourcePath = this.parsePath(source, context.currentDirectory);
    const file = context.files.find(f => f.path === sourcePath);
    
    if (!file) {
      return {
        output: `mv: ${source}: No such file or directory`,
        exitCode: 1
      };
    }

    return {
      output: '',
      exitCode: 0
    };
  }

  static async rm(args: string[], context: CommandContext): Promise<CommandResult> {
    if (args.length === 0) {
      return {
        output: "rm: missing operand",
        exitCode: 1
      };
    }

    const fileName = args.filter(a => !a.startsWith('-'))[0];
    const filePath = this.parsePath(fileName, context.currentDirectory);
    const file = context.files.find(f => f.path === filePath);
    
    if (!file) {
      return {
        output: `rm: ${fileName}: No such file or directory`,
        exitCode: 1
      };
    }

    return {
      output: '',
      exitCode: 0
    };
  }

  static async mkdir(args: string[], context: CommandContext): Promise<CommandResult> {
    if (args.length === 0) {
      return {
        output: "mkdir: missing operand",
        exitCode: 1
      };
    }

    const dirName = args[0];
    const dirPath = this.parsePath(dirName, context.currentDirectory);
    const existing = context.files.find(f => f.path === dirPath);
    
    if (existing) {
      return {
        output: `mkdir: ${dirName}: File exists`,
        exitCode: 1
      };
    }

    return {
      output: '',
      exitCode: 0
    };
  }

  static async rmdir(args: string[], context: CommandContext): Promise<CommandResult> {
    if (args.length === 0) {
      return {
        output: "rmdir: missing operand",
        exitCode: 1
      };
    }

    const dirName = args[0];
    const dirPath = this.parsePath(dirName, context.currentDirectory);
    const dir = context.files.find(f => f.path === dirPath);
    
    if (!dir) {
      return {
        output: `rmdir: ${dirName}: No such file or directory`,
        exitCode: 1
      };
    }

    if (!dir.isDirectory) {
      return {
        output: `rmdir: ${dirName}: Not a directory`,
        exitCode: 1
      };
    }

    const hasContents = context.files.some(f => f.parentPath === dirPath);
    if (hasContents) {
      return {
        output: `rmdir: ${dirName}: Directory not empty`,
        exitCode: 1
      };
    }

    return {
      output: '',
      exitCode: 0
    };
  }

  static async df(args: string[], context: CommandContext): Promise<CommandResult> {
    return {
      output: `Filesystem    512-blocks      Used Available Capacity  Mounted on
/dev/rp0a           4872      4512       360    93%    /
/dev/rp0g          42760     21736     21024    51%    /usr`,
      exitCode: 0
    };
  }

  static async du(args: string[], context: CommandContext): Promise<CommandResult> {
    const path = args.length > 0 ? this.parsePath(args[0], context.currentDirectory) : context.currentDirectory;
    
    const filesInPath = context.files.filter(f => f.path.startsWith(path));
    const totalSize = filesInPath.reduce((sum, file) => sum + Math.ceil(file.size / 512), 0);
    
    return {
      output: `${totalSize}\t${path}`,
      exitCode: 0
    };
  }

  static async file(args: string[], context: CommandContext): Promise<CommandResult> {
    if (args.length === 0) {
      return {
        output: "file: missing operand",
        exitCode: 1
      };
    }

    const results: string[] = [];
    for (const fileName of args) {
      const filePath = this.parsePath(fileName, context.currentDirectory);
      const file = context.files.find(f => f.path === filePath);
      
      if (!file) {
        results.push(`${fileName}: No such file or directory`);
        continue;
      }

      if (file.isDirectory) {
        results.push(`${fileName}: directory`);
      } else {
        const content = file.content || '';
        if (content.includes('#include') || content.includes('main(')) {
          results.push(`${fileName}: c program text`);
        } else if (content.includes('#!/bin/sh') || content.includes('#!/usr/bin/sh')) {
          results.push(`${fileName}: shell script`);
        } else if (content.match(/^[\x20-\x7E\s]*$/)) {
          results.push(`${fileName}: ascii text`);
        } else {
          results.push(`${fileName}: data`);
        }
      }
    }

    return {
      output: results.join('\n'),
      exitCode: 0
    };
  }

  static async od(args: string[], context: CommandContext): Promise<CommandResult> {
    if (args.length === 0) {
      return {
        output: "od: missing operand",
        exitCode: 1
      };
    }

    const fileName = args.filter(a => !a.startsWith('-'))[0];
    const filePath = this.parsePath(fileName, context.currentDirectory);
    const file = context.files.find(f => f.path === filePath);
    
    if (!file) {
      return {
        output: `od: ${fileName}: No such file or directory`,
        exitCode: 1
      };
    }

    const content = file.content || '';
    const results: string[] = [];
    
    for (let i = 0; i < content.length; i += 16) {
      const chunk = content.slice(i, i + 16);
      const offset = i.toString(8).padStart(7, '0');
      const hex = chunk.split('').map(c => c.charCodeAt(0).toString(8).padStart(3, '0')).join(' ');
      results.push(`${offset} ${hex}`);
    }

    return {
      output: results.join('\n'),
      exitCode: 0
    };
  }

  static async uniq(args: string[], context: CommandContext): Promise<CommandResult> {
    if (args.length === 0) {
      return {
        output: "uniq: missing operand",
        exitCode: 1
      };
    }

    const fileName = args.filter(a => !a.startsWith('-'))[0];
    const filePath = this.parsePath(fileName, context.currentDirectory);
    const file = context.files.find(f => f.path === filePath);
    
    if (!file) {
      return {
        output: `uniq: ${fileName}: No such file or directory`,
        exitCode: 1
      };
    }

    const content = file.content || '';
    const lines = content.split('\n');
    const uniqueLines: string[] = [];
    
    for (let i = 0; i < lines.length; i++) {
      if (i === 0 || lines[i] !== lines[i - 1]) {
        uniqueLines.push(lines[i]);
      }
    }

    return {
      output: uniqueLines.join('\n'),
      exitCode: 0
    };
  }

  static async tr(args: string[], context: CommandContext): Promise<CommandResult> {
    if (args.length < 2) {
      return {
        output: "tr: missing operand",
        exitCode: 1
      };
    }

    const set1 = args[0];
    const set2 = args[1];
    
    // Simple character translation (would normally read from stdin)
    return {
      output: `tr: translating '${set1}' to '${set2}' (input required)`,
      exitCode: 0
    };
  }
}

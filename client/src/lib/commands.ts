import { VirtualFileSystem, File, Directory, Permission } from './filesystem';
import { User } from './users';
import { getManPage } from './manpages';

type CommandResult = {
  output: string;
  error?: string;
  exitCode: number;
};

interface CommandOptions {
  fs: VirtualFileSystem;
  currentUser: User;
  env: Record<string, string>;
}

// Base command interface
export interface Command {
  name: string;
  execute(args: string[], options: CommandOptions): Promise<CommandResult>;
  usage: string;
  description: string;
}

// Helper functions
function formatPermissions(file: File | Directory): string {
  const fileType = file.isDirectory ? 'd' : '-';
  
  const owner = [
    (file.permissions & Permission.OWNER_READ) ? 'r' : '-',
    (file.permissions & Permission.OWNER_WRITE) ? 'w' : '-',
    (file.permissions & Permission.OWNER_EXECUTE) ? 'x' : '-'
  ].join('');
  
  const group = [
    (file.permissions & Permission.GROUP_READ) ? 'r' : '-',
    (file.permissions & Permission.GROUP_WRITE) ? 'w' : '-',
    (file.permissions & Permission.GROUP_EXECUTE) ? 'x' : '-'
  ].join('');
  
  const others = [
    (file.permissions & Permission.OTHERS_READ) ? 'r' : '-',
    (file.permissions & Permission.OTHERS_WRITE) ? 'w' : '-',
    (file.permissions & Permission.OTHERS_EXECUTE) ? 'x' : '-'
  ].join('');
  
  return fileType + owner + group + others;
}

function formatTimestamp(date: Date): string {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const month = months[date.getMonth()];
  const day = date.getDate().toString().padStart(2, ' ');
  
  // If the date is from this year, show the time, otherwise show the year
  const now = new Date();
  let timeOrYear: string;
  
  if (date.getFullYear() === now.getFullYear()) {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    timeOrYear = `${hours}:${minutes}`;
  } else {
    timeOrYear = date.getFullYear().toString();
  }
  
  return `${month} ${day} ${timeOrYear}`;
}

// Create commands
const lsCommand: Command = {
  name: 'ls',
  description: 'List directory contents',
  usage: 'ls [-acdfgilqrstu] name ...',
  async execute(args, { fs, currentUser }): Promise<CommandResult> {
    let flags = {
      all: false,    // -a: show all files including hidden ones
      long: false,   // -l: long format
      recursive: false, // -R: recursive
    };
    
    // Parse flags
    let paths: string[] = [];
    for (const arg of args) {
      if (arg.startsWith('-') && arg.length > 1) {
        for (const flag of arg.substring(1)) {
          switch (flag) {
            case 'a': flags.all = true; break;
            case 'l': flags.long = true; break;
            case 'R': flags.recursive = true; break;
          }
        }
      } else {
        paths.push(arg);
      }
    }
    
    // If no paths provided, use current directory
    if (paths.length === 0) {
      paths = [fs.currentDirectory];
    }
    
    let output = '';
    
    for (const path of paths) {
      try {
        const stats = await fs.stat(path);
        
        if (!stats.isDirectory) {
          // It's a file, just list it
          if (flags.long) {
            const permissions = formatPermissions(stats);
            const owner = stats.owner;
            const group = stats.group;
            const size = stats.size.toString().padStart(8, ' ');
            const timestamp = formatTimestamp(stats.modifiedAt);
            const name = stats.name;
            
            output += `${permissions} ${owner.padEnd(8)} ${group.padEnd(8)} ${size} ${timestamp} ${name}\n`;
          } else {
            output += `${stats.name}\n`;
          }
          continue;
        }
        
        // It's a directory, list its contents
        const entries = await fs.readdir(path);
        const filteredEntries = flags.all 
          ? entries 
          : entries.filter(entry => !entry.name.startsWith('.'));
        
        if (paths.length > 1) {
          output += `${path}:\n`;
        }
        
        if (flags.long) {
          output += `total ${filteredEntries.length}\n`;
          
          for (const entry of filteredEntries) {
            const permissions = formatPermissions(entry);
            const owner = entry.owner;
            const group = entry.group;
            const size = entry.size.toString().padStart(8, ' ');
            const timestamp = formatTimestamp(entry.modifiedAt);
            const name = entry.name;
            
            output += `${permissions} ${owner.padEnd(8)} ${group.padEnd(8)} ${size} ${timestamp} ${name}\n`;
          }
        } else {
          // Simple format, just names
          output += filteredEntries.map(entry => entry.name).join('\t') + '\n';
        }
        
        // Recursive listing if requested
        if (flags.recursive) {
          for (const entry of filteredEntries) {
            if (entry.isDirectory && entry.name !== '.' && entry.name !== '..') {
              const subpath = path === '/' ? `/${entry.name}` : `${path}/${entry.name}`;
              const subentries = await fs.readdir(subpath);
              
              output += '\n';
              output += `${subpath}:\n`;
              
              if (flags.long) {
                output += `total ${subentries.length}\n`;
                
                for (const subentry of subentries) {
                  const permissions = formatPermissions(subentry);
                  const owner = subentry.owner;
                  const group = subentry.group;
                  const size = subentry.size.toString().padStart(8, ' ');
                  const timestamp = formatTimestamp(subentry.modifiedAt);
                  const name = subentry.name;
                  
                  output += `${permissions} ${owner.padEnd(8)} ${group.padEnd(8)} ${size} ${timestamp} ${name}\n`;
                }
              } else {
                output += subentries.map(entry => entry.name).join('\t') + '\n';
              }
            }
          }
        }
      } catch (error) {
        return {
          output: '',
          error: `ls: ${path}: No such file or directory`,
          exitCode: 1
        };
      }
    }
    
    return { output, exitCode: 0 };
  }
};

const cdCommand: Command = {
  name: 'cd',
  description: 'Change the current directory',
  usage: 'cd [directory]',
  async execute(args, { fs, currentUser, env }): Promise<CommandResult> {
    // If no directory specified, go to user's home directory
    const directory = args[0] || env.HOME || `/usr/${currentUser.username}`;
    
    try {
      await fs.changeDirectory(directory);
      return { output: '', exitCode: 0 };
    } catch (error) {
      return {
        output: '',
        error: `cd: ${directory}: No such file or directory`,
        exitCode: 1
      };
    }
  }
};

const pwdCommand: Command = {
  name: 'pwd',
  description: 'Print name of current/working directory',
  usage: 'pwd',
  async execute(args, { fs }): Promise<CommandResult> {
    return { output: fs.currentDirectory, exitCode: 0 };
  }
};

const catCommand: Command = {
  name: 'cat',
  description: 'Concatenate and print files',
  usage: 'cat [-u] [file ...]',
  async execute(args, { fs }): Promise<CommandResult> {
    if (args.length === 0) {
      return {
        output: '',
        error: 'cat: Usage: cat [-u] [file ...]',
        exitCode: 1
      };
    }
    
    let output = '';
    
    for (const filePath of args) {
      try {
        const content = await fs.readFile(filePath);
        output += content;
        
        // Add newline if there isn't one at the end
        if (content.length > 0 && !content.endsWith('\n')) {
          output += '\n';
        }
      } catch (error) {
        return {
          output,
          error: `cat: ${filePath}: No such file or directory`,
          exitCode: 1
        };
      }
    }
    
    return { output, exitCode: 0 };
  }
};

const echoCommand: Command = {
  name: 'echo',
  description: 'Echo arguments',
  usage: 'echo [arg ...]',
  async execute(args, { env }): Promise<CommandResult> {
    let output = '';
    
    // Process each argument, expand environment variables
    for (let i = 0; i < args.length; i++) {
      let arg = args[i];
      
      // Expand environment variables
      arg = arg.replace(/\$([A-Za-z_][A-Za-z0-9_]*)/g, (match, varName) => {
        return env[varName] || '';
      });
      
      output += arg;
      if (i < args.length - 1) {
        output += ' ';
      }
    }
    
    output += '\n';
    return { output, exitCode: 0 };
  }
};

const touchCommand: Command = {
  name: 'touch',
  description: 'Change file access and modification times',
  usage: 'touch [-c] file ...',
  async execute(args, { fs, currentUser }): Promise<CommandResult> {
    if (args.length === 0) {
      return {
        output: '',
        error: 'touch: missing file operand',
        exitCode: 1
      };
    }
    
    let createIfMissing = true;
    let files: string[] = [];
    
    // Parse options
    for (const arg of args) {
      if (arg === '-c') {
        createIfMissing = false;
      } else {
        files.push(arg);
      }
    }
    
    for (const filePath of files) {
      try {
        // Check if file exists
        try {
          await fs.stat(filePath);
          // File exists, update timestamp
          await fs.touch(filePath);
        } catch (error) {
          // File doesn't exist
          if (createIfMissing) {
            await fs.writeFile(filePath, '', {
              owner: currentUser.username,
              group: currentUser.primaryGroup,
              permissions: Permission.DEFAULT_FILE
            });
          }
        }
      } catch (error) {
        return {
          output: '',
          error: `touch: ${filePath}: ${error instanceof Error ? error.message : String(error)}`,
          exitCode: 1
        };
      }
    }
    
    return { output: '', exitCode: 0 };
  }
};

const mkdirCommand: Command = {
  name: 'mkdir',
  description: 'Make directories',
  usage: 'mkdir [-p] directory ...',
  async execute(args, { fs, currentUser }): Promise<CommandResult> {
    if (args.length === 0) {
      return {
        output: '',
        error: 'mkdir: missing operand',
        exitCode: 1
      };
    }
    
    let createParents = false;
    let directories: string[] = [];
    
    // Parse options
    for (const arg of args) {
      if (arg === '-p') {
        createParents = true;
      } else {
        directories.push(arg);
      }
    }
    
    for (const dirPath of directories) {
      try {
        await fs.mkdir(dirPath, {
          owner: currentUser.username,
          group: currentUser.primaryGroup,
          permissions: Permission.DEFAULT_DIRECTORY,
          createParents
        });
      } catch (error) {
        return {
          output: '',
          error: `mkdir: ${dirPath}: ${error instanceof Error ? error.message : String(error)}`,
          exitCode: 1
        };
      }
    }
    
    return { output: '', exitCode: 0 };
  }
};

const rmCommand: Command = {
  name: 'rm',
  description: 'Remove files or directories',
  usage: 'rm [-f] [-r] file ...',
  async execute(args, { fs }): Promise<CommandResult> {
    if (args.length === 0) {
      return {
        output: '',
        error: 'rm: missing operand',
        exitCode: 1
      };
    }
    
    let force = false;
    let recursive = false;
    let files: string[] = [];
    
    // Parse options
    for (const arg of args) {
      if (arg === '-f') {
        force = true;
      } else if (arg === '-r' || arg === '-R') {
        recursive = true;
      } else {
        files.push(arg);
      }
    }
    
    for (const filePath of files) {
      try {
        const stats = await fs.stat(filePath);
        
        if (stats.isDirectory && !recursive) {
          return {
            output: '',
            error: `rm: ${filePath}: is a directory`,
            exitCode: 1
          };
        }
        
        await fs.remove(filePath, { recursive });
      } catch (error) {
        if (!force) {
          return {
            output: '',
            error: `rm: ${filePath}: No such file or directory`,
            exitCode: 1
          };
        }
      }
    }
    
    return { output: '', exitCode: 0 };
  }
};

const cpCommand: Command = {
  name: 'cp',
  description: 'Copy files or directories',
  usage: 'cp [-r] source_file target_file | source_file ... target_directory',
  async execute(args, { fs, currentUser }): Promise<CommandResult> {
    if (args.length < 2) {
      return {
        output: '',
        error: 'cp: missing file operand',
        exitCode: 1
      };
    }
    
    let recursive = false;
    let sources: string[] = [];
    let dest = '';
    
    // Parse options
    for (const arg of args) {
      if (arg === '-r' || arg === '-R') {
        recursive = true;
      } else {
        sources.push(arg);
      }
    }
    
    // Last argument is the destination
    dest = sources.pop() || '';
    
    if (sources.length === 0) {
      return {
        output: '',
        error: 'cp: missing file operand',
        exitCode: 1
      };
    }
    
    try {
      const destStats = await fs.stat(dest);
      
      // If destination exists and is a directory, copy each source inside it
      if (destStats.isDirectory) {
        for (const source of sources) {
          try {
            const sourceStats = await fs.stat(source);
            const sourceName = source.split('/').pop() || '';
            const targetPath = `${dest}/${sourceName}`;
            
            if (sourceStats.isDirectory && !recursive) {
              return {
                output: '',
                error: `cp: -r not specified; omitting directory '${source}'`,
                exitCode: 1
              };
            }
            
            await fs.copy(source, targetPath, { recursive });
          } catch (error) {
            return {
              output: '',
              error: `cp: cannot stat '${source}': No such file or directory`,
              exitCode: 1
            };
          }
        }
      } else if (sources.length === 1) {
        // Destination exists and is a file - only one source allowed
        await fs.copy(sources[0], dest, { recursive });
      } else {
        return {
          output: '',
          error: `cp: target '${dest}' is not a directory`,
          exitCode: 1
        };
      }
    } catch (error) {
      // Destination doesn't exist
      if (sources.length === 1) {
        // Only one source, create a new file
        await fs.copy(sources[0], dest, { recursive });
      } else {
        return {
          output: '',
          error: `cp: target '${dest}' is not a directory`,
          exitCode: 1
        };
      }
    }
    
    return { output: '', exitCode: 0 };
  }
};

const mvCommand: Command = {
  name: 'mv',
  description: 'Move (rename) files',
  usage: 'mv [-f] source_file target_file | source_file ... target_directory',
  async execute(args, { fs }): Promise<CommandResult> {
    if (args.length < 2) {
      return {
        output: '',
        error: 'mv: missing file operand',
        exitCode: 1
      };
    }
    
    let force = false;
    let sources: string[] = [];
    let dest = '';
    
    // Parse options
    for (const arg of args) {
      if (arg === '-f') {
        force = true;
      } else {
        sources.push(arg);
      }
    }
    
    // Last argument is the destination
    dest = sources.pop() || '';
    
    if (sources.length === 0) {
      return {
        output: '',
        error: 'mv: missing file operand',
        exitCode: 1
      };
    }
    
    try {
      const destStats = await fs.stat(dest);
      
      // If destination exists and is a directory, move each source inside it
      if (destStats.isDirectory) {
        for (const source of sources) {
          try {
            const sourceName = source.split('/').pop() || '';
            const targetPath = `${dest}/${sourceName}`;
            
            await fs.rename(source, targetPath, { force });
          } catch (error) {
            return {
              output: '',
              error: `mv: cannot stat '${source}': No such file or directory`,
              exitCode: 1
            };
          }
        }
      } else if (sources.length === 1) {
        // Destination exists and is a file - only one source allowed
        await fs.rename(sources[0], dest, { force });
      } else {
        return {
          output: '',
          error: `mv: target '${dest}' is not a directory`,
          exitCode: 1
        };
      }
    } catch (error) {
      // Destination doesn't exist
      if (sources.length === 1) {
        // Only one source, create a new file
        await fs.rename(sources[0], dest, { force });
      } else {
        return {
          output: '',
          error: `mv: target '${dest}' is not a directory`,
          exitCode: 1
        };
      }
    }
    
    return { output: '', exitCode: 0 };
  }
};

const chmodCommand: Command = {
  name: 'chmod',
  description: 'Change file mode bits',
  usage: 'chmod mode file ...',
  async execute(args, { fs }): Promise<CommandResult> {
    if (args.length < 2) {
      return {
        output: '',
        error: 'chmod: missing operand',
        exitCode: 1
      };
    }
    
    const mode = args[0];
    const files = args.slice(1);
    
    // Parse numeric mode (octal)
    let permissions: number;
    
    if (/^[0-7]{3,4}$/.test(mode)) {
      permissions = parseInt(mode, 8);
    } else {
      return {
        output: '',
        error: 'chmod: invalid mode: ' + mode,
        exitCode: 1
      };
    }
    
    for (const filePath of files) {
      try {
        await fs.chmod(filePath, permissions);
      } catch (error) {
        return {
          output: '',
          error: `chmod: ${filePath}: No such file or directory`,
          exitCode: 1
        };
      }
    }
    
    return { output: '', exitCode: 0 };
  }
};

const chownCommand: Command = {
  name: 'chown',
  description: 'Change file owner and group',
  usage: 'chown owner[:group] file ...',
  async execute(args, { fs }): Promise<CommandResult> {
    if (args.length < 2) {
      return {
        output: '',
        error: 'chown: missing operand',
        exitCode: 1
      };
    }
    
    const ownerInfo = args[0];
    const files = args.slice(1);
    
    // Parse owner and group
    let owner: string;
    let group: string | undefined;
    
    if (ownerInfo.includes(':')) {
      [owner, group] = ownerInfo.split(':');
    } else {
      owner = ownerInfo;
    }
    
    for (const filePath of files) {
      try {
        await fs.chown(filePath, owner, group);
      } catch (error) {
        return {
          output: '',
          error: `chown: ${filePath}: No such file or directory`,
          exitCode: 1
        };
      }
    }
    
    return { output: '', exitCode: 0 };
  }
};

const grepCommand: Command = {
  name: 'grep',
  description: 'Search for patterns in files',
  usage: 'grep [-v] pattern [file ...]',
  async execute(args, { fs }): Promise<CommandResult> {
    if (args.length < 1) {
      return {
        output: '',
        error: 'grep: missing pattern',
        exitCode: 1
      };
    }
    
    let invert = false;
    let patternIndex = 0;
    
    // Check for -v flag
    if (args[0] === '-v') {
      invert = true;
      patternIndex = 1;
      
      if (args.length < 2) {
        return {
          output: '',
          error: 'grep: missing pattern',
          exitCode: 1
        };
      }
    }
    
    const pattern = args[patternIndex];
    const files = args.slice(patternIndex + 1);
    const regexp = new RegExp(pattern);
    
    let output = '';
    let foundMatch = false;
    
    // If no files provided, grep expects input from stdin
    // For this simulation, we'll return an error
    if (files.length === 0) {
      return {
        output: '',
        error: 'grep: no input files',
        exitCode: 1
      };
    }
    
    for (const filePath of files) {
      try {
        const content = await fs.readFile(filePath);
        const lines = content.split('\n');
        
        for (const line of lines) {
          const matches = regexp.test(line);
          
          if ((!invert && matches) || (invert && !matches)) {
            // If multiple files, prepend file name
            if (files.length > 1) {
              output += `${filePath}:`;
            }
            
            output += `${line}\n`;
            foundMatch = true;
          }
        }
      } catch (error) {
        return {
          output,
          error: `grep: ${filePath}: No such file or directory`,
          exitCode: 1
        };
      }
    }
    
    return { output, exitCode: foundMatch ? 0 : 1 };
  }
};

const wcCommand: Command = {
  name: 'wc',
  description: 'Print line, word, and byte counts',
  usage: 'wc [-clw] [file ...]',
  async execute(args, { fs }): Promise<CommandResult> {
    let countLines = false;
    let countWords = false;
    let countBytes = false;
    let files: string[] = [];
    
    // Parse options
    for (const arg of args) {
      if (arg.startsWith('-') && arg.length > 1) {
        for (const flag of arg.substring(1)) {
          switch (flag) {
            case 'l': countLines = true; break;
            case 'w': countWords = true; break;
            case 'c': countBytes = true; break;
          }
        }
      } else {
        files.push(arg);
      }
    }
    
    // If no specific counts requested, count everything
    if (!countLines && !countWords && !countBytes) {
      countLines = countWords = countBytes = true;
    }
    
    // If no files provided, return error
    if (files.length === 0) {
      return {
        output: '',
        error: 'wc: no input files',
        exitCode: 1
      };
    }
    
    let output = '';
    let totalLines = 0;
    let totalWords = 0;
    let totalBytes = 0;
    
    for (const filePath of files) {
      try {
        const content = await fs.readFile(filePath);
        
        const lines = content.split('\n').length - 1; // Don't count trailing newline
        const words = content.trim().split(/\s+/).length;
        const bytes = content.length;
        
        let lineParts = [];
        
        if (countLines) {
          lineParts.push(lines.toString().padStart(7));
          totalLines += lines;
        }
        
        if (countWords) {
          lineParts.push(words.toString().padStart(7));
          totalWords += words;
        }
        
        if (countBytes) {
          lineParts.push(bytes.toString().padStart(7));
          totalBytes += bytes;
        }
        
        output += lineParts.join('') + ' ' + filePath + '\n';
      } catch (error) {
        return {
          output,
          error: `wc: ${filePath}: No such file or directory`,
          exitCode: 1
        };
      }
    }
    
    // Add totals if more than one file
    if (files.length > 1) {
      let totalParts = [];
      
      if (countLines) {
        totalParts.push(totalLines.toString().padStart(7));
      }
      
      if (countWords) {
        totalParts.push(totalWords.toString().padStart(7));
      }
      
      if (countBytes) {
        totalParts.push(totalBytes.toString().padStart(7));
      }
      
      output += totalParts.join('') + ' total\n';
    }
    
    return { output, exitCode: 0 };
  }
};

const whoCommand: Command = {
  name: 'who',
  description: 'Show who is logged on',
  usage: 'who [am i]',
  async execute(args, { currentUser }): Promise<CommandResult> {
    // Simplified who command that just shows the current user
    let output = `${currentUser.username}\ttty01\t${formatTimestamp(new Date())}\n`;
    
    // Check if "am i" was passed
    if (args.length === 2 && args[0] === 'am' && args[1] === 'i') {
      output = `${currentUser.username}\ttty01\n`;
    }
    
    return { output, exitCode: 0 };
  }
};

const manCommand: Command = {
  name: 'man',
  description: 'Display manual pages',
  usage: 'man command',
  async execute(args): Promise<CommandResult> {
    if (args.length !== 1) {
      return {
        output: '',
        error: 'man: command required',
        exitCode: 1
      };
    }
    
    const command = args[0];
    const manPage = getManPage(command);
    
    if (!manPage) {
      return {
        output: '',
        error: `man: No manual entry for ${command}`,
        exitCode: 1
      };
    }
    
    return { output: manPage, exitCode: 0 };
  }
};

const dateCommand: Command = {
  name: 'date',
  description: 'Print or set the system date and time',
  usage: 'date [+format]',
  async execute(args): Promise<CommandResult> {
    const date = new Date();
    
    // Basic date output in Unix format
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    const dayOfWeek = days[date.getDay()];
    const month = months[date.getMonth()];
    const dayOfMonth = date.getDate();
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const seconds = date.getSeconds().toString().padStart(2, '0');
    const year = date.getFullYear();
    
    let output = `${dayOfWeek} ${month} ${dayOfMonth} ${hours}:${minutes}:${seconds} EDT ${year}\n`;
    
    // Check if format is specified
    if (args.length > 0 && args[0].startsWith('+')) {
      const format = args[0].substring(1);
      
      // Very simplified format handling
      output = format
        .replace('%a', dayOfWeek)
        .replace('%b', month)
        .replace('%d', dayOfMonth.toString().padStart(2, '0'))
        .replace('%H', hours)
        .replace('%M', minutes)
        .replace('%S', seconds)
        .replace('%Y', year.toString())
        .replace('%T', `${hours}:${minutes}:${seconds}`)
        .replace('%D', `${date.getMonth() + 1}/${dayOfMonth}/${year.toString().substring(2)}`)
        + '\n';
    }
    
    return { output, exitCode: 0 };
  }
};

const mountCommand: Command = {
  name: 'mount',
  description: 'Mount file system',
  usage: 'mount [ special name [ -r ] ]',
  async execute(args): Promise<CommandResult> {
    return {
      output: "/dev/rk0 on / type rk05 (rw)\n/dev/rk1 on /usr type rk05 (rw)",
      exitCode: 0
    };
  }
};

const fsckCommand: Command = {
  name: 'fsck',
  description: 'File system consistency check',
  usage: 'fsck [ -y ] [ -n ] [ filesystem... ]',
  async execute(args): Promise<CommandResult> {
    return {
      output: "Checking /dev/rk0...\n** Phase 1 - Check Blocks and Sizes\n** Phase 2 - Check Pathnames\n** Phase 3 - Check Connectivity\n** Phase 4 - Check Reference Counts\n** Phase 5 - Check Free List\n/dev/rk0: FILES=542 USED=8714 FREE=1376\n",
      exitCode: 0
    };
  }
};

const helpCommand: Command = {
  name: 'help',
  description: 'Display help for available commands',
  usage: 'help [command]',
  async execute(args): Promise<CommandResult> {
    if (args.length === 0) {
      // List all available commands
      let output = 'Available commands:\n\n';
      
      for (const cmd of Object.values(commands)) {
        output += `${cmd.name.padEnd(12)} - ${cmd.description}\n`;
      }
      
      output += '\nUse "help <command>" for details on a specific command.\n';
      return { output, exitCode: 0 };
    } else {
      // Show help for a specific command
      const commandName = args[0];
      const command = commands[commandName];
      
      if (!command) {
        return {
          output: '',
          error: `help: no help topics match ${commandName}`,
          exitCode: 1
        };
      }
      
      let output = `${command.name} - ${command.description}\n\n`;
      output += `Usage: ${command.usage}\n`;
      
      return { output, exitCode: 0 };
    }
  }
};

// Export commands
export const commands: Record<string, Command> = {
  ls: lsCommand,
  cd: cdCommand,
  pwd: pwdCommand,
  cat: catCommand,
  echo: echoCommand,
  touch: touchCommand,
  mkdir: mkdirCommand,
  rm: rmCommand,
  cp: cpCommand,
  mv: mvCommand,
  chmod: chmodCommand,
  chown: chownCommand,
  grep: grepCommand,
  wc: wcCommand,
  who: whoCommand,
  man: manCommand,
  date: dateCommand,
  help: helpCommand,
  mount: mountCommand,
  fsck: fsckCommand
};

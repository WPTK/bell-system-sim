import { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { UnixCommands, type CommandResult, type CommandContext } from "@/lib/unix-commands";
import type { File, Process } from "@shared/schema";

export function useTerminal() {
  const [currentDirectory, setCurrentDirectory] = useState("/root");

  // Fetch files
  const { data: allFiles = [] } = useQuery<File[]>({
    queryKey: ['/api/files'],
    queryFn: async () => {
      const response = await fetch('/api/files?path=/', {
        credentials: 'include'
      });
      if (!response.ok) throw new Error('Failed to fetch files');
      return response.json();
    }
  });

  // Fetch processes
  const { data: processes = [] } = useQuery<Process[]>({
    queryKey: ['/api/processes'],
  });

  // Get current user
  const { data: currentUser } = useQuery({
    queryKey: ['/api/user'],
  });

  const executeCommand = useCallback(async (
    commandLine: string, 
    workingDirectory: string
  ): Promise<CommandResult> => {
    const trimmed = commandLine.trim();
    if (!trimmed) {
      return { output: '', exitCode: 0 };
    }

    const parts = trimmed.split(/\s+/);
    const command = parts[0];
    const args = parts.slice(1);

    const context: CommandContext = {
      currentDirectory: workingDirectory,
      files: allFiles,
      processes,
      user: currentUser?.username || 'root'
    };

    try {
      switch (command) {
        case 'ls':
          return await UnixCommands.ls(args, context);
        case 'cat':
          return await UnixCommands.cat(args, context);
        case 'pwd':
          return await UnixCommands.pwd(args, context);
        case 'ps':
          return await UnixCommands.ps(args, context);
        case 'who':
          return await UnixCommands.who(args, context);
        case 'date':
          return await UnixCommands.date(args, context);
        case 'grep':
          return await UnixCommands.grep(args, context);
        case 'cd':
          const result = await UnixCommands.cd(args, context);
          if (result.exitCode === 0 && result.newDirectory) {
            setCurrentDirectory(result.newDirectory);
          }
          return result;
        case 'help':
          return await UnixCommands.help(args, context);
        case 'man':
          return await UnixCommands.man(args, context);
        case 'clear':
          return await UnixCommands.clear(args, context);
        case 'echo':
          return await UnixCommands.echo(args, context);
        case 'wc':
          return await UnixCommands.wc(args, context);
        
        // Simulate other common UNIX commands
        case 'vi':
        case 'ed':
          return {
            output: `${command}: entering editor mode... (simulated)`,
            exitCode: 0
          };
        
        case 'cc':
        case 'make':
          return {
            output: '', // Compilers typically run silently on success
            exitCode: 0
          };
        
        case 'chmod':
          return {
            output: args.length < 2 ? 'chmod: missing operand' : '',
            exitCode: args.length < 2 ? 1 : 0
          };
        
        case 'cp':
        case 'mv':
        case 'rm':
        case 'mkdir':
        case 'rmdir':
          return {
            output: args.length === 0 ? `${command}: missing operand` : '',
            exitCode: args.length === 0 ? 1 : 0
          };
        
        case 'find':
          return {
            output: args.length === 0 ? 'find: missing path' : `find: searching for "${args.join(' ')}"...`,
            exitCode: args.length === 0 ? 1 : 0
          };
        
        case 'sort':
          return {
            output: args.length === 0 ? 'sort: missing file operand' : '',
            exitCode: args.length === 0 ? 1 : 0
          };
        
        case 'sed':
        case 'awk':
          return {
            output: args.length === 0 ? `${command}: missing operand` : `${command}: processing...`,
            exitCode: args.length === 0 ? 1 : 0
          };
        
        case 'kill':
          return {
            output: args.length === 0 ? 'kill: missing process ID' : '',
            exitCode: args.length === 0 ? 1 : 0
          };
        
        default:
          return {
            output: `${command}: command not found`,
            exitCode: 127
          };
      }
    } catch (error) {
      return {
        output: `${command}: ${error instanceof Error ? error.message : 'unknown error'}`,
        exitCode: 1
      };
    }
  }, [allFiles, processes, currentUser]);

  return {
    currentDirectory,
    setCurrentDirectory,
    executeCommand,
    files: allFiles,
    processes,
    currentUser
  };
}

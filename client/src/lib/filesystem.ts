import { apiRequest } from "./queryClient";

// Permissions (Unix-style)
export enum Permission {
  NONE = 0,
  
  OTHERS_EXECUTE = 1,
  OTHERS_WRITE = 2,
  OTHERS_READ = 4,
  
  GROUP_EXECUTE = 8,
  GROUP_WRITE = 16,
  GROUP_READ = 32,
  
  OWNER_EXECUTE = 64,
  OWNER_WRITE = 128,
  OWNER_READ = 256,
  
  DEFAULT_FILE = 0o644,      // rw-r--r--
  DEFAULT_DIRECTORY = 0o755  // rwxr-xr-x
}

// File system entry interfaces
export interface FileSystemEntry {
  id: number;
  name: string;
  path: string;
  isDirectory: boolean;
  owner: string;
  group: string;
  permissions: number;
  size: number;
  createdAt: Date;
  modifiedAt: Date;
}

export interface File extends FileSystemEntry {
  isDirectory: false;
  content: string;
}

export interface Directory extends FileSystemEntry {
  isDirectory: true;
}

// Options interfaces
export interface FileOptions {
  owner?: string;
  group?: string;
  permissions?: number;
}

export interface DirectoryOptions extends FileOptions {
  createParents?: boolean;
}

export interface CopyOptions {
  recursive?: boolean;
  force?: boolean;
}

export interface RenameOptions {
  force?: boolean;
}

export interface RemoveOptions {
  recursive?: boolean;
  force?: boolean;
}

export class VirtualFileSystem {
  private _currentDirectory: string;
  private _cache: Map<string, FileSystemEntry>;
  
  constructor(initialDirectory = "/") {
    this._currentDirectory = initialDirectory;
    this._cache = new Map();
  }
  
  get currentDirectory(): string {
    return this._currentDirectory;
  }
  
  // Path resolution
  private resolvePath(path: string): string {
    if (path.startsWith('/')) {
      // Absolute path
      return this.normalizePath(path);
    } else {
      // Relative path
      return this.normalizePath(`${this._currentDirectory}/${path}`);
    }
  }
  
  private normalizePath(path: string): string {
    // Handle . and ..
    const parts = path.split('/').filter(p => p !== '');
    const stack: string[] = [];
    
    for (const part of parts) {
      if (part === '.') {
        // Current directory, do nothing
      } else if (part === '..') {
        // Go up one level
        stack.pop();
      } else {
        stack.push(part);
      }
    }
    
    return `/${stack.join('/')}`;
  }
  
  // Cache management
  private async loadEntry(path: string): Promise<FileSystemEntry> {
    const normalizedPath = this.resolvePath(path);
    
    if (this._cache.has(normalizedPath)) {
      return this._cache.get(normalizedPath)!;
    }
    
    try {
      const response = await apiRequest('GET', `/api/files/path${normalizedPath}`);
      const entry = await response.json();
      
      // Convert dates
      entry.createdAt = new Date(entry.createdAt);
      entry.modifiedAt = new Date(entry.modifiedAt);
      
      this._cache.set(normalizedPath, entry);
      return entry;
    } catch (error) {
      throw new Error(`No such file or directory: ${normalizedPath}`);
    }
  }
  
  private invalidateCache(path?: string) {
    if (path) {
      const normalizedPath = this.resolvePath(path);
      this._cache.delete(normalizedPath);
      
      // Also invalidate parent directories
      let parent = this.getParentPath(normalizedPath);
      while (parent) {
        this._cache.delete(parent);
        parent = this.getParentPath(parent);
      }
    } else {
      // Invalidate entire cache
      this._cache.clear();
    }
  }
  
  private getParentPath(path: string): string | null {
    if (path === '/') return null;
    
    const parts = path.split('/').filter(Boolean);
    parts.pop();
    return `/${parts.join('/')}`;
  }
  
  // File system operations
  async stat(path: string): Promise<FileSystemEntry> {
    return await this.loadEntry(path);
  }
  
  async readdir(path: string): Promise<FileSystemEntry[]> {
    const dirPath = this.resolvePath(path);
    const entry = await this.loadEntry(dirPath);
    
    if (!entry.isDirectory) {
      throw new Error(`Not a directory: ${dirPath}`);
    }
    
    const response = await apiRequest('GET', `/api/files?directory=${encodeURIComponent(dirPath)}`);
    const entries = await response.json();
    
    // Convert dates and cache entries
    for (const entry of entries) {
      entry.createdAt = new Date(entry.createdAt);
      entry.modifiedAt = new Date(entry.modifiedAt);
      this._cache.set(entry.path, entry);
    }
    
    return entries;
  }
  
  async readFile(path: string): Promise<string> {
    const filePath = this.resolvePath(path);
    const entry = await this.loadEntry(filePath);
    
    if (entry.isDirectory) {
      throw new Error(`Is a directory: ${filePath}`);
    }
    
    return (entry as File).content || '';
  }
  
  async writeFile(path: string, content: string, options: FileOptions = {}): Promise<void> {
    const filePath = this.resolvePath(path);
    
    try {
      // Check if file exists
      const existing = await this.loadEntry(filePath);
      
      // Update existing file
      await apiRequest('PUT', `/api/files/${existing.id}`, {
        content,
        ...options
      });
      
      this.invalidateCache(filePath);
    } catch (error) {
      // File doesn't exist, create it
      const dirPath = this.getParentPath(filePath);
      if (!dirPath) throw new Error('Invalid path');
      
      // Make sure parent directory exists
      try {
        await this.loadEntry(dirPath);
      } catch (error) {
        throw new Error(`Directory does not exist: ${dirPath}`);
      }
      
      const fileName = filePath.split('/').pop() || '';
      
      await apiRequest('POST', '/api/files', {
        name: fileName,
        path: filePath,
        content,
        isDirectory: false,
        owner: options.owner || 'root',
        group: options.group || 'root',
        permissions: options.permissions || Permission.DEFAULT_FILE
      });
      
      this.invalidateCache(filePath);
      this.invalidateCache(dirPath);
    }
  }
  
  async mkdir(path: string, options: DirectoryOptions = {}): Promise<void> {
    const dirPath = this.resolvePath(path);
    
    // Check if directory already exists
    try {
      await this.loadEntry(dirPath);
      throw new Error(`File exists: ${dirPath}`);
    } catch (error) {
      // Expected - directory doesn't exist
    }
    
    // Create parent directories if needed
    if (options.createParents) {
      const parts = dirPath.split('/').filter(Boolean);
      let currentPath = '';
      
      for (let i = 0; i < parts.length; i++) {
        currentPath += `/${parts[i]}`;
        
        try {
          await this.loadEntry(currentPath);
        } catch (error) {
          // Directory doesn't exist, create it
          const dirName = parts[i];
          
          await apiRequest('POST', '/api/files', {
            name: dirName,
            path: currentPath,
            isDirectory: true,
            owner: options.owner || 'root',
            group: options.group || 'root',
            permissions: options.permissions || Permission.DEFAULT_DIRECTORY
          });
          
          this.invalidateCache(currentPath);
        }
      }
    } else {
      // Just create the requested directory
      const parentPath = this.getParentPath(dirPath);
      if (!parentPath) throw new Error('Invalid path');
      
      // Make sure parent directory exists
      try {
        await this.loadEntry(parentPath);
      } catch (error) {
        throw new Error(`Directory does not exist: ${parentPath}`);
      }
      
      const dirName = dirPath.split('/').pop() || '';
      
      await apiRequest('POST', '/api/files', {
        name: dirName,
        path: dirPath,
        isDirectory: true,
        owner: options.owner || 'root',
        group: options.group || 'root',
        permissions: options.permissions || Permission.DEFAULT_DIRECTORY
      });
      
      this.invalidateCache(dirPath);
      this.invalidateCache(parentPath);
    }
  }
  
  async remove(path: string, options: RemoveOptions = {}): Promise<void> {
    const targetPath = this.resolvePath(path);
    const entry = await this.loadEntry(targetPath);
    
    if (entry.isDirectory && !options.recursive) {
      throw new Error(`Is a directory: ${targetPath}`);
    }
    
    // If directory, check if it's empty or if recursive is specified
    if (entry.isDirectory) {
      const entries = await this.readdir(targetPath);
      
      if (entries.length > 0 && !options.recursive) {
        throw new Error(`Directory not empty: ${targetPath}`);
      }
      
      // Remove all entries recursively
      if (options.recursive) {
        for (const childEntry of entries) {
          if (childEntry.name === '.' || childEntry.name === '..') continue;
          
          await this.remove(`${targetPath}/${childEntry.name}`, options);
        }
      }
    }
    
    // Delete the entry
    await apiRequest('DELETE', `/api/files/${entry.id}`);
    
    // Invalidate cache
    this.invalidateCache(targetPath);
    this.invalidateCache(this.getParentPath(targetPath));
  }
  
  async copy(source: string, destination: string, options: CopyOptions = {}): Promise<void> {
    const sourcePath = this.resolvePath(source);
    const destPath = this.resolvePath(destination);
    
    // Check if source exists
    const sourceEntry = await this.loadEntry(sourcePath);
    
    if (sourceEntry.isDirectory && !options.recursive) {
      throw new Error(`Is a directory: ${sourcePath}`);
    }
    
    try {
      // Check if destination exists
      const destEntry = await this.loadEntry(destPath);
      
      if (destEntry.isDirectory) {
        // If destination is a directory, copy source inside it
        const sourceName = sourcePath.split('/').pop() || '';
        const newDestPath = `${destPath}/${sourceName}`;
        
        if (sourceEntry.isDirectory) {
          // Create directory at the destination
          await this.mkdir(newDestPath, {
            owner: sourceEntry.owner,
            group: sourceEntry.group,
            permissions: sourceEntry.permissions
          });
          
          // Copy all entries inside the directory
          if (options.recursive) {
            const entries = await this.readdir(sourcePath);
            
            for (const entry of entries) {
              if (entry.name === '.' || entry.name === '..') continue;
              
              await this.copy(
                `${sourcePath}/${entry.name}`,
                `${newDestPath}/${entry.name}`,
                options
              );
            }
          }
        } else {
          // Copy the file to the new destination
          const content = await this.readFile(sourcePath);
          await this.writeFile(newDestPath, content, {
            owner: sourceEntry.owner,
            group: sourceEntry.group,
            permissions: sourceEntry.permissions
          });
        }
      } else {
        // Destination exists and is a file
        if (sourceEntry.isDirectory) {
          throw new Error(`Cannot overwrite non-directory with directory: ${destPath}`);
        }
        
        // Overwrite the destination file
        const content = await this.readFile(sourcePath);
        await this.writeFile(destPath, content, {
          owner: sourceEntry.owner,
          group: sourceEntry.group,
          permissions: sourceEntry.permissions
        });
      }
    } catch (error) {
      // Destination doesn't exist
      if (sourceEntry.isDirectory) {
        // Create directory at the destination
        await this.mkdir(destPath, {
          owner: sourceEntry.owner,
          group: sourceEntry.group,
          permissions: sourceEntry.permissions
        });
        
        // Copy all entries inside the directory
        if (options.recursive) {
          const entries = await this.readdir(sourcePath);
          
          for (const entry of entries) {
            if (entry.name === '.' || entry.name === '..') continue;
            
            await this.copy(
              `${sourcePath}/${entry.name}`,
              `${destPath}/${entry.name}`,
              options
            );
          }
        }
      } else {
        // Copy the file to the destination
        const content = await this.readFile(sourcePath);
        await this.writeFile(destPath, content, {
          owner: sourceEntry.owner,
          group: sourceEntry.group,
          permissions: sourceEntry.permissions
        });
      }
    }
    
    // Invalidate cache
    this.invalidateCache(destPath);
    this.invalidateCache(this.getParentPath(destPath));
  }
  
  async rename(source: string, destination: string, options: RenameOptions = {}): Promise<void> {
    const sourcePath = this.resolvePath(source);
    const destPath = this.resolvePath(destination);
    
    // Check if source exists
    const sourceEntry = await this.loadEntry(sourcePath);
    
    try {
      // Check if destination exists
      await this.loadEntry(destPath);
      
      if (!options.force) {
        throw new Error(`File exists: ${destPath}`);
      }
      
      // Remove destination before renaming
      await this.remove(destPath, { recursive: true });
    } catch (error) {
      // Destination doesn't exist, which is fine
    }
    
    // Create the file/directory at the new location with the same content
    if (sourceEntry.isDirectory) {
      await this.mkdir(destPath, {
        owner: sourceEntry.owner,
        group: sourceEntry.group,
        permissions: sourceEntry.permissions
      });
      
      // Copy all entries inside the directory
      const entries = await this.readdir(sourcePath);
      
      for (const entry of entries) {
        if (entry.name === '.' || entry.name === '..') continue;
        
        await this.rename(
          `${sourcePath}/${entry.name}`,
          `${destPath}/${entry.name}`,
          options
        );
      }
    } else {
      const content = await this.readFile(sourcePath);
      await this.writeFile(destPath, content, {
        owner: sourceEntry.owner,
        group: sourceEntry.group,
        permissions: sourceEntry.permissions
      });
    }
    
    // Remove the original
    await this.remove(sourcePath, { recursive: true });
    
    // Invalidate cache
    this.invalidateCache(sourcePath);
    this.invalidateCache(destPath);
    this.invalidateCache(this.getParentPath(sourcePath));
    this.invalidateCache(this.getParentPath(destPath));
  }
  
  async chmod(path: string, mode: number): Promise<void> {
    const targetPath = this.resolvePath(path);
    const entry = await this.loadEntry(targetPath);
    
    await apiRequest('PUT', `/api/files/${entry.id}`, {
      permissions: mode
    });
    
    this.invalidateCache(targetPath);
  }
  
  async chown(path: string, owner: string, group?: string): Promise<void> {
    const targetPath = this.resolvePath(path);
    const entry = await this.loadEntry(targetPath);
    
    const updateData: Record<string, string> = { owner };
    if (group) updateData.group = group;
    
    await apiRequest('PUT', `/api/files/${entry.id}`, updateData);
    
    this.invalidateCache(targetPath);
  }
  
  async touch(path: string): Promise<void> {
    const targetPath = this.resolvePath(path);
    const entry = await this.loadEntry(targetPath);
    
    await apiRequest('PUT', `/api/files/${entry.id}`, {
      modifiedAt: new Date()
    });
    
    this.invalidateCache(targetPath);
  }
  
  async changeDirectory(path: string): Promise<void> {
    const targetPath = this.resolvePath(path);
    const entry = await this.loadEntry(targetPath);
    
    if (!entry.isDirectory) {
      throw new Error(`Not a directory: ${targetPath}`);
    }
    
    this._currentDirectory = targetPath;
  }
}

// Create a singleton instance of the file system
export const fileSystem = new VirtualFileSystem('/usr/you');

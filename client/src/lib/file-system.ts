import type { File } from "@shared/schema";

export interface FileSystemNode {
  name: string;
  path: string;
  isDirectory: boolean;
  children?: FileSystemNode[];
  content?: string;
  size: number;
  permissions: string;
  owner: string;
  group: string;
  modifiedAt: Date;
}

export class FileSystem {
  private files: Map<string, File> = new Map();

  constructor(initialFiles: File[] = []) {
    initialFiles.forEach(file => {
      this.files.set(file.path, file);
    });
  }

  getFile(path: string): File | undefined {
    return this.files.get(path);
  }

  getChildren(parentPath: string): File[] {
    return Array.from(this.files.values())
      .filter(file => file.parentPath === parentPath)
      .sort((a, b) => {
        // Directories first, then alphabetical
        if (a.isDirectory && !b.isDirectory) return -1;
        if (!a.isDirectory && b.isDirectory) return 1;
        return a.name.localeCompare(b.name);
      });
  }

  getAllFiles(): File[] {
    return Array.from(this.files.values());
  }

  addFile(file: File): void {
    this.files.set(file.path, file);
  }

  removeFile(path: string): boolean {
    return this.files.delete(path);
  }

  updateFile(path: string, updates: Partial<File>): boolean {
    const file = this.files.get(path);
    if (!file) return false;
    
    const updatedFile = { ...file, ...updates, modifiedAt: new Date() };
    this.files.set(path, updatedFile);
    return true;
  }

  exists(path: string): boolean {
    return this.files.has(path);
  }

  isDirectory(path: string): boolean {
    const file = this.files.get(path);
    return file?.isDirectory || false;
  }

  resolvePath(path: string, currentDirectory: string): string {
    if (path.startsWith('/')) {
      return path;
    }
    
    if (path === '.') {
      return currentDirectory;
    }
    
    if (path === '..') {
      const parts = currentDirectory.split('/').filter(p => p);
      parts.pop();
      return '/' + parts.join('/');
    }
    
    // Resolve relative path
    if (currentDirectory === '/') {
      return `/${path}`;
    }
    
    return `${currentDirectory}/${path}`;
  }

  getPathSegments(path: string): string[] {
    return path.split('/').filter(segment => segment.length > 0);
  }

  getParentPath(path: string): string {
    if (path === '/') return '/';
    
    const segments = this.getPathSegments(path);
    if (segments.length <= 1) return '/';
    
    segments.pop();
    return '/' + segments.join('/');
  }

  buildFileTree(rootPath: string = '/'): FileSystemNode | null {
    const rootFile = this.getFile(rootPath);
    if (!rootFile) return null;

    const node: FileSystemNode = {
      name: rootFile.name || '/',
      path: rootFile.path,
      isDirectory: rootFile.isDirectory,
      content: rootFile.content,
      size: rootFile.size,
      permissions: rootFile.permissions,
      owner: rootFile.owner,
      group: rootFile.group,
      modifiedAt: rootFile.modifiedAt,
    };

    if (rootFile.isDirectory) {
      node.children = this.getChildren(rootPath).map(child => 
        this.buildFileTree(child.path)
      ).filter((child): child is FileSystemNode => child !== null);
    }

    return node;
  }

  // Utility methods for common operations
  static formatPermissions(permissions: string): string {
    // Convert octal or string permissions to readable format
    if (permissions.length === 3 && /^\d+$/.test(permissions)) {
      // Convert octal to string format
      const octal = parseInt(permissions, 8);
      let result = '';
      
      for (let i = 0; i < 3; i++) {
        const digit = (octal >> (3 * (2 - i))) & 7;
        result += (digit & 4 ? 'r' : '-');
        result += (digit & 2 ? 'w' : '-');
        result += (digit & 1 ? 'x' : '-');
      }
      
      return result;
    }
    
    return permissions;
  }

  static formatSize(size: number): string {
    if (size < 1024) return `${size}B`;
    if (size < 1024 * 1024) return `${Math.round(size / 1024)}K`;
    if (size < 1024 * 1024 * 1024) return `${Math.round(size / (1024 * 1024))}M`;
    return `${Math.round(size / (1024 * 1024 * 1024))}G`;
  }

  static formatDate(date: Date): string {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays < 180) {
      // Recent files: show month, day, time
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    } else {
      // Older files: show month, day, year
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: '2-digit',
        year: 'numeric'
      });
    }
  }
}

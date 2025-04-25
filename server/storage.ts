import { users, files, history, type User, type InsertUser, type File, type InsertFile, type History, type InsertHistory } from "@shared/schema";

export interface IStorage {
  // User operations
  getUser(id: number): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  listUsers(): Promise<User[]>;

  // File operations
  getFile(id: number): Promise<File | undefined>;
  getFileByPath(path: string): Promise<File | undefined>;
  createFile(file: InsertFile): Promise<File>;
  updateFile(id: number, file: Partial<File>): Promise<File | undefined>;
  deleteFile(id: number): Promise<boolean>;
  listFiles(directory: string): Promise<File[]>;

  // History operations
  addHistoryEntry(entry: InsertHistory): Promise<History>;
  getHistoryByUsername(username: string, limit?: number): Promise<History[]>;
}

export class MemStorage implements IStorage {
  private users: Map<number, User>;
  private files: Map<number, File>;
  private history: Map<number, History>;
  private userIdCounter: number;
  private fileIdCounter: number;
  private historyIdCounter: number;

  constructor() {
    this.users = new Map();
    this.files = new Map();
    this.history = new Map();
    this.userIdCounter = 1;
    this.fileIdCounter = 1;
    this.historyIdCounter = 1;

    // Initialize with root user and basic directory structure
    this.initializeSystem();
  }

  private initializeSystem() {
    // Create root user
    const rootUser: InsertUser = {
      username: "root",
      password: "root",
      home: "/root",
      shell: "/bin/sh",
      isAdmin: true
    };
    this.createUser(rootUser);
    
    // Create standard user
    const standardUser: InsertUser = {
      username: "you",
      password: "password",
      home: "/usr/you",
      shell: "/bin/sh",
      isAdmin: false
    };
    this.createUser(standardUser);

    // Create basic directory structure
    const rootDirs = ["/", "/bin", "/etc", "/usr", "/tmp", "/dev", "/root"];
    rootDirs.forEach(dir => {
      this.createFile({
        name: dir.split("/").filter(Boolean).pop() || "",
        path: dir,
        isDirectory: true,
        owner: "root",
        group: "root",
        permissions: 0o755
      });
    });

    // Create user directory
    this.createFile({
      name: "you",
      path: "/usr/you",
      isDirectory: true,
      owner: "you",
      group: "users",
      permissions: 0o755
    });

    // Add some sample files
    this.createFile({
      name: ".profile",
      path: "/usr/you/.profile",
      content: "PATH=/bin:/usr/bin\nPS1='$ '",
      isDirectory: false,
      owner: "you",
      group: "users",
      permissions: 0o644
    });

    this.createFile({
      name: "hello.c",
      path: "/usr/you/hello.c",
      content: '#include <stdio.h>\n\nmain()\n{\n    printf("Hello, world\\n");\n}',
      isDirectory: false,
      owner: "you",
      group: "users",
      permissions: 0o644
    });

    this.createFile({
      name: ".mail",
      path: "/usr/you/.mail",
      content: "Welcome to UNIX V7!",
      isDirectory: false,
      owner: "you",
      group: "users",
      permissions: 0o644
    });

    this.createFile({
      name: "notes.txt",
      path: "/usr/you/notes.txt",
      content: "Some notes about UNIX V7\n- Released in 1979\n- Developed at Bell Labs\n- Influential in OS design",
      isDirectory: false,
      owner: "you",
      group: "users",
      permissions: 0o644
    });
  }

  // User operations
  async getUser(id: number): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = this.userIdCounter++;
    const user: User = { id, ...insertUser };
    this.users.set(id, user);
    return user;
  }

  async listUsers(): Promise<User[]> {
    return Array.from(this.users.values());
  }

  // File operations
  async getFile(id: number): Promise<File | undefined> {
    return this.files.get(id);
  }

  async getFileByPath(path: string): Promise<File | undefined> {
    return Array.from(this.files.values()).find(
      (file) => file.path === path
    );
  }

  async createFile(insertFile: InsertFile): Promise<File> {
    const id = this.fileIdCounter++;
    const now = new Date();
    const file: File = { 
      id, 
      ...insertFile, 
      createdAt: now, 
      modifiedAt: now 
    };
    this.files.set(id, file);
    return file;
  }

  async updateFile(id: number, partialFile: Partial<File>): Promise<File | undefined> {
    const file = this.files.get(id);
    if (!file) return undefined;

    const updatedFile: File = {
      ...file,
      ...partialFile,
      modifiedAt: new Date()
    };
    
    this.files.set(id, updatedFile);
    return updatedFile;
  }

  async deleteFile(id: number): Promise<boolean> {
    return this.files.delete(id);
  }

  async listFiles(directory: string): Promise<File[]> {
    // Normalize the directory path
    const normalizedDir = directory.endsWith("/") ? directory : `${directory}/`;
    
    return Array.from(this.files.values()).filter(file => {
      if (directory === "/") {
        // Special case for root directory
        const pathParts = file.path.split("/").filter(Boolean);
        return pathParts.length === 1;
      }
      
      // For all other directories
      return file.path.startsWith(normalizedDir) && 
             file.path.substring(normalizedDir.length).split("/").filter(Boolean).length === 1;
    });
  }

  // History operations
  async addHistoryEntry(insertHistory: InsertHistory): Promise<History> {
    const id = this.historyIdCounter++;
    const entry: History = {
      id,
      ...insertHistory,
      timestamp: new Date()
    };
    this.history.set(id, entry);
    return entry;
  }

  async getHistoryByUsername(username: string, limit = 100): Promise<History[]> {
    return Array.from(this.history.values())
      .filter(entry => entry.username === username)
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      .slice(0, limit);
  }
}

export const storage = new MemStorage();

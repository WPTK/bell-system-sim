import { users, files, processes, commandHistory, type User, type InsertUser, type File, type InsertFile, type Process, type InsertProcess, type CommandHistory, type InsertCommandHistory } from "@shared/schema";

export interface IStorage {
  // User operations
  getUser(id: number): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;

  // File system operations
  getFile(path: string): Promise<File | undefined>;
  getFilesByParentPath(parentPath: string): Promise<File[]>;
  createFile(file: InsertFile): Promise<File>;
  updateFile(path: string, updates: Partial<InsertFile>): Promise<File | undefined>;
  deleteFile(path: string): Promise<boolean>;
  getAllFiles(): Promise<File[]>;

  // Process operations
  getProcesses(): Promise<Process[]>;
  getProcessByPid(pid: number): Promise<Process | undefined>;
  createProcess(process: InsertProcess): Promise<Process>;
  updateProcess(pid: number, updates: Partial<InsertProcess>): Promise<Process | undefined>;
  deleteProcess(pid: number): Promise<boolean>;

  // Command history operations
  getCommandHistory(userId?: number): Promise<CommandHistory[]>;
  addCommandHistory(history: InsertCommandHistory): Promise<CommandHistory>;
}

export class MemStorage implements IStorage {
  private users: Map<number, User>;
  private files: Map<string, File>;
  private processes: Map<number, Process>;
  private commandHistoryMap: Map<number, CommandHistory>;
  private currentUserId: number;
  private currentFileId: number;
  private currentProcessId: number;
  private currentHistoryId: number;
  private currentPid: number;

  constructor() {
    this.users = new Map();
    this.files = new Map();
    this.processes = new Map();
    this.commandHistoryMap = new Map();
    this.currentUserId = 1;
    this.currentFileId = 1;
    this.currentProcessId = 1;
    this.currentHistoryId = 1;
    this.currentPid = 100;

    this.initializeDefaultData();
  }

  private initializeDefaultData() {
    // Create default root user
    const rootUser: User = {
      id: this.currentUserId++,
      username: "root",
      password: "root",
      homeDirectory: "/root",
      shell: "/bin/sh",
      createdAt: new Date(),
    };
    this.users.set(rootUser.id, rootUser);

    // Create default file system structure
    const defaultFiles: File[] = [
      { id: this.currentFileId++, name: "", path: "/", content: "", permissions: "drwxr-xr-x", owner: "root", group: "wheel", size: 512, isDirectory: true, parentPath: null, modifiedAt: new Date(), createdAt: new Date() },
      { id: this.currentFileId++, name: "bin", path: "/bin", content: "", permissions: "drwxr-xr-x", owner: "root", group: "wheel", size: 64, isDirectory: true, parentPath: "/", modifiedAt: new Date(), createdAt: new Date() },
      { id: this.currentFileId++, name: "dev", path: "/dev", content: "", permissions: "drwxr-xr-x", owner: "root", group: "wheel", size: 64, isDirectory: true, parentPath: "/", modifiedAt: new Date(), createdAt: new Date() },
      { id: this.currentFileId++, name: "etc", path: "/etc", content: "", permissions: "drwxr-xr-x", owner: "root", group: "wheel", size: 128, isDirectory: true, parentPath: "/", modifiedAt: new Date(), createdAt: new Date() },
      { id: this.currentFileId++, name: "lib", path: "/lib", content: "", permissions: "drwxr-xr-x", owner: "root", group: "wheel", size: 96, isDirectory: true, parentPath: "/", modifiedAt: new Date(), createdAt: new Date() },
      { id: this.currentFileId++, name: "tmp", path: "/tmp", content: "", permissions: "drwxrwxrwx", owner: "root", group: "wheel", size: 64, isDirectory: true, parentPath: "/", modifiedAt: new Date(), createdAt: new Date() },
      { id: this.currentFileId++, name: "usr", path: "/usr", content: "", permissions: "drwxr-xr-x", owner: "root", group: "wheel", size: 128, isDirectory: true, parentPath: "/", modifiedAt: new Date(), createdAt: new Date() },
      { id: this.currentFileId++, name: "home", path: "/home", content: "", permissions: "drwxr-xr-x", owner: "root", group: "wheel", size: 64, isDirectory: true, parentPath: "/", modifiedAt: new Date(), createdAt: new Date() },
      { id: this.currentFileId++, name: "root", path: "/root", content: "", permissions: "drwx------", owner: "root", group: "wheel", size: 128, isDirectory: true, parentPath: "/", modifiedAt: new Date(), createdAt: new Date() },
      { id: this.currentFileId++, name: "motd", path: "/etc/motd", content: "Welcome to UNIX Version 7\nBell Telephone Laboratories\n\nFor assistance, contact your system administrator.\nCurrent system load: light", permissions: "-rw-r--r--", owner: "root", group: "wheel", size: 156, isDirectory: false, parentPath: "/etc", modifiedAt: new Date(), createdAt: new Date() },
      { id: this.currentFileId++, name: "hello.c", path: "/root/hello.c", content: "#include <stdio.h>\n\nmain()\n{\n    printf(\"hello, world\\n\");\n}", permissions: "-rw-r--r--", owner: "root", group: "wheel", size: 78, isDirectory: false, parentPath: "/root", modifiedAt: new Date(), createdAt: new Date() },
      { id: this.currentFileId++, name: ".profile", path: "/root/.profile", content: "# User profile for root\nexport PATH=/bin:/usr/bin\nexport HOME=/root\nexport SHELL=/bin/sh", permissions: "-rw-r--r--", owner: "root", group: "wheel", size: 87, isDirectory: false, parentPath: "/root", modifiedAt: new Date(), createdAt: new Date() },
    ];

    defaultFiles.forEach(file => this.files.set(file.path, file));

    // Create default processes
    const defaultProcesses: Process[] = [
      { id: this.currentProcessId++, pid: 1, command: "init", tty: "?", time: "0:02", status: "running", createdAt: new Date() },
      { id: this.currentProcessId++, pid: 23, command: "update", tty: "?", time: "0:01", status: "running", createdAt: new Date() },
      { id: this.currentProcessId++, pid: 45, command: "sh", tty: "co", time: "0:00", status: "running", createdAt: new Date() },
      { id: this.currentProcessId++, pid: 67, command: "login", tty: "01", time: "0:00", status: "running", createdAt: new Date() },
      { id: this.currentProcessId++, pid: 89, command: "sh", tty: "01", time: "0:00", status: "running", createdAt: new Date() },
    ];

    defaultProcesses.forEach(process => this.processes.set(process.pid, process));
  }

  async getUser(id: number): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(user => user.username === username);
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const user: User = {
      ...insertUser,
      id: this.currentUserId++,
      createdAt: new Date(),
    };
    this.users.set(user.id, user);
    return user;
  }

  async getFile(path: string): Promise<File | undefined> {
    return this.files.get(path);
  }

  async getFilesByParentPath(parentPath: string): Promise<File[]> {
    return Array.from(this.files.values()).filter(file => file.parentPath === parentPath);
  }

  async createFile(insertFile: InsertFile): Promise<File> {
    const file: File = {
      ...insertFile,
      id: this.currentFileId++,
      modifiedAt: new Date(),
      createdAt: new Date(),
    };
    this.files.set(file.path, file);
    return file;
  }

  async updateFile(path: string, updates: Partial<InsertFile>): Promise<File | undefined> {
    const file = this.files.get(path);
    if (!file) return undefined;
    
    const updatedFile: File = {
      ...file,
      ...updates,
      modifiedAt: new Date(),
    };
    this.files.set(path, updatedFile);
    return updatedFile;
  }

  async deleteFile(path: string): Promise<boolean> {
    return this.files.delete(path);
  }

  async getAllFiles(): Promise<File[]> {
    return Array.from(this.files.values());
  }

  async getProcesses(): Promise<Process[]> {
    return Array.from(this.processes.values());
  }

  async getProcessByPid(pid: number): Promise<Process | undefined> {
    return this.processes.get(pid);
  }

  async createProcess(insertProcess: InsertProcess): Promise<Process> {
    const process: Process = {
      ...insertProcess,
      id: this.currentProcessId++,
      createdAt: new Date(),
    };
    this.processes.set(process.pid, process);
    return process;
  }

  async updateProcess(pid: number, updates: Partial<InsertProcess>): Promise<Process | undefined> {
    const process = this.processes.get(pid);
    if (!process) return undefined;
    
    const updatedProcess: Process = {
      ...process,
      ...updates,
    };
    this.processes.set(pid, updatedProcess);
    return updatedProcess;
  }

  async deleteProcess(pid: number): Promise<boolean> {
    return this.processes.delete(pid);
  }

  async getCommandHistory(userId?: number): Promise<CommandHistory[]> {
    const history = Array.from(this.commandHistoryMap.values());
    if (userId) {
      return history.filter(h => h.userId === userId);
    }
    return history;
  }

  async addCommandHistory(insertHistory: InsertCommandHistory): Promise<CommandHistory> {
    const history: CommandHistory = {
      ...insertHistory,
      id: this.currentHistoryId++,
      executedAt: new Date(),
    };
    this.commandHistoryMap.set(history.id, history);
    return history;
  }

  getNextPid(): number {
    return ++this.currentPid;
  }
}

export const storage = new MemStorage();

import { apiRequest } from "./queryClient";

export interface User {
  id: number;
  username: string;
  password: string;
  home: string;
  shell: string;
  isAdmin: boolean;
  primaryGroup: string;
}

export interface UserGroup {
  name: string;
  members: string[];
}

// User authentication system
class UserSystem {
  private currentUser: User | null = null;
  private groups: Map<string, UserGroup> = new Map();
  
  constructor() {
    // Initialize standard groups
    this.groups.set("root", { name: "root", members: ["root"] });
    this.groups.set("users", { name: "users", members: ["you"] });
  }
  
  // Authenticate a user
  async login(username: string, password: string): Promise<User> {
    try {
      const response = await apiRequest('GET', `/api/users/${username}`);
      const user = await response.json();
      
      if (user.password !== password) {
        throw new Error("Invalid password");
      }
      
      // Add primary group information
      this.currentUser = {
        ...user,
        primaryGroup: username === "root" ? "root" : "users"
      };
      
      return this.currentUser;
    } catch (error) {
      throw new Error("Authentication failed");
    }
  }
  
  // Get the current logged in user
  getCurrentUser(): User | null {
    return this.currentUser;
  }
  
  // Log out the current user
  logout(): void {
    this.currentUser = null;
  }
  
  // Get a group by name
  getGroup(name: string): UserGroup | undefined {
    return this.groups.get(name);
  }
  
  // Get all groups
  getAllGroups(): UserGroup[] {
    return Array.from(this.groups.values());
  }
  
  // Check if a user is a member of a group
  isUserInGroup(username: string, groupName: string): boolean {
    const group = this.groups.get(groupName);
    return group ? group.members.includes(username) : false;
  }
}

// Export a singleton instance
export const userSystem = new UserSystem();

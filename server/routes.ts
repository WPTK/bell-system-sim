import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertUserSchema, insertFileSchema, insertHistorySchema } from "@shared/schema";
import { z } from "zod";

export async function registerRoutes(app: Express): Promise<Server> {
  // API routes
  app.get("/api/users", async (req, res) => {
    const users = await storage.listUsers();
    res.json(users);
  });

  app.get("/api/users/:username", async (req, res) => {
    const user = await storage.getUserByUsername(req.params.username);
    if (!user) {
      return res.status(404).json({ message: "User not found" });
    }
    res.json(user);
  });

  app.post("/api/users", async (req, res) => {
    try {
      const userData = insertUserSchema.parse(req.body);
      const existingUser = await storage.getUserByUsername(userData.username);
      if (existingUser) {
        return res.status(409).json({ message: "Username already exists" });
      }
      const user = await storage.createUser(userData);
      res.status(201).json(user);
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ message: "Invalid user data", errors: error.errors });
      }
      res.status(500).json({ message: "Failed to create user" });
    }
  });

  // File API routes
  app.get("/api/files", async (req, res) => {
    const directory = req.query.directory as string || "/";
    const files = await storage.listFiles(directory);
    res.json(files);
  });

  app.get("/api/files/:id", async (req, res) => {
    const id = parseInt(req.params.id);
    if (isNaN(id)) {
      return res.status(400).json({ message: "Invalid file ID" });
    }
    
    const file = await storage.getFile(id);
    if (!file) {
      return res.status(404).json({ message: "File not found" });
    }
    
    res.json(file);
  });

  app.get("/api/files/path/*", async (req, res) => {
    const path = req.params[0] ? `/${req.params[0]}` : "/";
    const file = await storage.getFileByPath(path);
    
    if (!file) {
      return res.status(404).json({ message: "File not found" });
    }
    
    res.json(file);
  });

  app.post("/api/files", async (req, res) => {
    try {
      const fileData = insertFileSchema.parse(req.body);
      
      // Check if parent directory exists
      const parentPath = fileData.path.split("/").slice(0, -1).join("/") || "/";
      const parentDir = await storage.getFileByPath(parentPath);
      
      if (!parentDir || !parentDir.isDirectory) {
        return res.status(400).json({ message: "Parent directory does not exist" });
      }
      
      // Check if file already exists
      const existingFile = await storage.getFileByPath(fileData.path);
      if (existingFile) {
        return res.status(409).json({ message: "File already exists" });
      }
      
      const file = await storage.createFile(fileData);
      res.status(201).json(file);
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ message: "Invalid file data", errors: error.errors });
      }
      res.status(500).json({ message: "Failed to create file" });
    }
  });

  app.put("/api/files/:id", async (req, res) => {
    const id = parseInt(req.params.id);
    if (isNaN(id)) {
      return res.status(400).json({ message: "Invalid file ID" });
    }
    
    try {
      const file = await storage.updateFile(id, req.body);
      if (!file) {
        return res.status(404).json({ message: "File not found" });
      }
      
      res.json(file);
    } catch (error) {
      res.status(500).json({ message: "Failed to update file" });
    }
  });

  app.delete("/api/files/:id", async (req, res) => {
    const id = parseInt(req.params.id);
    if (isNaN(id)) {
      return res.status(400).json({ message: "Invalid file ID" });
    }
    
    const success = await storage.deleteFile(id);
    if (!success) {
      return res.status(404).json({ message: "File not found" });
    }
    
    res.status(204).send();
  });

  // History API routes
  app.get("/api/history/:username", async (req, res) => {
    const limit = req.query.limit ? parseInt(req.query.limit as string) : 100;
    const history = await storage.getHistoryByUsername(req.params.username, limit);
    res.json(history);
  });

  app.post("/api/history", async (req, res) => {
    try {
      const historyData = insertHistorySchema.parse(req.body);
      const entry = await storage.addHistoryEntry(historyData);
      res.status(201).json(entry);
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ message: "Invalid history data", errors: error.errors });
      }
      res.status(500).json({ message: "Failed to add history entry" });
    }
  });

  // Create HTTP server
  const httpServer = createServer(app);
  return httpServer;
}

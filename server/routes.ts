import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertCommandHistorySchema } from "@shared/schema";
import { z } from "zod";

export async function registerRoutes(app: Express): Promise<Server> {
  
  // Get file system structure
  app.get("/api/files", async (req, res) => {
    try {
      const parentPath = req.query.path as string || "/";
      const files = await storage.getFilesByParentPath(parentPath);
      res.json(files);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch files" });
    }
  });

  // Get file content
  app.get("/api/files/content", async (req, res) => {
    try {
      const path = req.query.path as string;
      if (!path) {
        return res.status(400).json({ error: "Path is required" });
      }
      const file = await storage.getFile(path);
      if (!file) {
        return res.status(404).json({ error: "File not found" });
      }
      res.json({ content: file.content, file });
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch file content" });
    }
  });

  // Create file or directory
  app.post("/api/files", async (req, res) => {
    try {
      const { name, path, content, isDirectory, parentPath } = req.body;
      const size = content ? content.length : (isDirectory ? 64 : 0);
      
      const file = await storage.createFile({
        name,
        path,
        content: content || "",
        isDirectory: isDirectory || false,
        parentPath,
        size,
        permissions: isDirectory ? "drwxr-xr-x" : "-rw-r--r--",
        owner: "root",
        group: "wheel",
      });
      
      res.json(file);
    } catch (error) {
      res.status(500).json({ error: "Failed to create file" });
    }
  });

  // Get processes
  app.get("/api/processes", async (req, res) => {
    try {
      const processes = await storage.getProcesses();
      res.json(processes);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch processes" });
    }
  });

  // Execute command
  app.post("/api/execute", async (req, res) => {
    try {
      const { command, userId } = req.body;
      
      // This would normally execute the actual command
      // For now, we'll simulate command execution
      const response = {
        command,
        output: `Command '${command}' executed`,
        exitCode: 0,
      };

      // Add to command history
      if (userId) {
        await storage.addCommandHistory({
          userId,
          command,
          output: response.output,
          exitCode: response.exitCode,
        });
      }

      res.json(response);
    } catch (error) {
      res.status(500).json({ error: "Failed to execute command" });
    }
  });

  // Get command history
  app.get("/api/history", async (req, res) => {
    try {
      const userId = req.query.userId ? parseInt(req.query.userId as string) : undefined;
      const history = await storage.getCommandHistory(userId);
      res.json(history);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch command history" });
    }
  });

  // Get current user (for demo purposes, always return root)
  app.get("/api/user", async (req, res) => {
    try {
      const user = await storage.getUserByUsername("root");
      res.json(user);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch user" });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}

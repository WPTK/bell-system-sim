import { pgTable, text, serial, integer, boolean, timestamp } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
  homeDirectory: text("home_directory").notNull().default("/home/user"),
  shell: text("shell").notNull().default("/bin/sh"),
  createdAt: timestamp("created_at").defaultNow(),
});

export const files = pgTable("files", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  path: text("path").notNull().unique(),
  content: text("content").default(""),
  permissions: text("permissions").notNull().default("rw-r--r--"),
  owner: text("owner").notNull().default("root"),
  group: text("group").notNull().default("wheel"),
  size: integer("size").notNull().default(0),
  isDirectory: boolean("is_directory").notNull().default(false),
  parentPath: text("parent_path"),
  modifiedAt: timestamp("modified_at").defaultNow(),
  createdAt: timestamp("created_at").defaultNow(),
});

export const processes = pgTable("processes", {
  id: serial("id").primaryKey(),
  pid: integer("pid").notNull().unique(),
  command: text("command").notNull(),
  tty: text("tty"),
  time: text("time").notNull().default("0:00"),
  status: text("status").notNull().default("running"),
  createdAt: timestamp("created_at").defaultNow(),
});

export const commandHistory = pgTable("command_history", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").references(() => users.id),
  command: text("command").notNull(),
  output: text("output"),
  exitCode: integer("exit_code").notNull().default(0),
  executedAt: timestamp("executed_at").defaultNow(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
  homeDirectory: true,
  shell: true,
});

export const insertFileSchema = createInsertSchema(files).pick({
  name: true,
  path: true,
  content: true,
  permissions: true,
  owner: true,
  group: true,
  size: true,
  isDirectory: true,
  parentPath: true,
});

export const insertProcessSchema = createInsertSchema(processes).pick({
  pid: true,
  command: true,
  tty: true,
  time: true,
  status: true,
});

export const insertCommandHistorySchema = createInsertSchema(commandHistory).pick({
  userId: true,
  command: true,
  output: true,
  exitCode: true,
});

export type User = typeof users.$inferSelect;
export type InsertUser = z.infer<typeof insertUserSchema>;
export type File = typeof files.$inferSelect;
export type InsertFile = z.infer<typeof insertFileSchema>;
export type Process = typeof processes.$inferSelect;
export type InsertProcess = z.infer<typeof insertProcessSchema>;
export type CommandHistory = typeof commandHistory.$inferSelect;
export type InsertCommandHistory = z.infer<typeof insertCommandHistorySchema>;

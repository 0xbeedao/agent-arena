import { createLogger } from "@mastra/core/logger";

export const mastraLogger = createLogger({
  name: "Mastra",
  level: "info",
});

export const arenaLogger = createLogger({
  name: "Arena",
  level: "info",
});

export const contestLogger = createLogger({
  name: "Contest",
  level: "debug",
});

export const judgeLogger = createLogger({
  name: "Judge",
  level: "info",
});

export const playerLogger = createLogger({
  name: "Player",
  level: "debug",
});

export const systemLogger = createLogger({
  name: "System",
  level: "debug",
});

export const testLogger = createLogger({
  name: "Test",
  level: "debug",
});

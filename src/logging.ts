import { createLogger } from "@mastra/core/logger";

export const mastraLogger = createLogger({
  name: "Mastra",
  level: "debug",
});

export const arenaLogger = createLogger({
  name: "Arena",
  level: "info",
});

export const contestLogger = createLogger({
  name: "Contest",
  level: "info",
});

export const judgeLogger = createLogger({
  name: "Judge",
  level: "info",
});

export const playerLogger = createLogger({
  name: "Player",
  level: "debug",
});

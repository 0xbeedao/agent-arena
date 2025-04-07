import { createLogger } from "@mastra/core/logger";

export const mastraLogger = createLogger({
  name: "Mastra",
  level: "info",
});

export const arenaLogger = createLogger({
  name: "Arena",
  level: "debug",
});

export const contestLogger = createLogger({
  name: "Contest",
  level: "debug",
});

export const judgeLogger = createLogger({
  name: "Judge",
  level: "debug",
});

export const playerLogger = createLogger({
  name: "Player",
  level: "debug",
});

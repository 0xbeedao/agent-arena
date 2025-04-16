import { Mastra } from "@mastra/core";
import { LibSQLStore } from "@mastra/core/storage/libsql";
import { makeContestWorkflow } from "./workflows/contest";
import { mastraLogger } from "../logging";
import { playerAgent1, playerAgent2 } from "./agents/player";
import { arenaAgent } from "./agents/arena";
import { judgeAgent } from "./agents/judge";

export const mastra = new Mastra({
  workflows: {
    contest: makeContestWorkflow(),
  },
  agents: {
    arena: arenaAgent,
    judge: judgeAgent,
    player1: playerAgent1,
    player2: playerAgent2,
  },
  logger: mastraLogger,
  storage: new LibSQLStore({
    config: {
      url: process.env.DATABASE_URL || "file:./arenagent.db",
    },
  }),
});

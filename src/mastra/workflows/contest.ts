import { Workflow, Step } from "@mastra/core/workflows";
import {
  contestWorkflowSchema,
  contestWorkflowSetupSchema,
} from "../../types/schemas.d";
import { makeArenaAgent } from "../agents/arena";
import { makeJudgeAgent } from "../agents/judge";
import { makePlayerAgent } from "../agents/player";
import { AgentCache } from "../agents/util/agentcache";
import { generateGrid } from "../agents/util/stadium";
import { contestLogger } from "../../logging";

export function makeContestWorkflow() {
  const workflow = new Workflow({
    name: "Contest",
    triggerSchema: contestWorkflowSetupSchema,
  });
  workflow.step(startContestStep).commit();
  return workflow;
}

/**
 * This step is responsible for starting the contest.
 * It will create the arena, judge, and players.
 * It will also determine the setup locations for the players.
 */
const startContestStep = new Step({
  id: "startContest",
  outputSchema: contestWorkflowSchema,
  execute: async ({ context }) => {
    contestLogger.debug("starting");
    const { arena, judge, players, arenaDescription, rules } =
      context.triggerData;
    const arenaAgent = makeArenaAgent(arena, players, arenaDescription);
    contestLogger.debug("generating grid");
    const grid = await generateGrid(
      arena.width,
      arena.height,
      arena.maxFeatures,
      arenaDescription,
      players,
      arenaAgent
    );
    contestLogger.debug("grid generated");
    contestLogger.debug(JSON.stringify(grid, null, 2));

    const agentCache = new AgentCache();
    agentCache.addAgent("arena", arenaAgent);
    agentCache.addAgent("judge", makeJudgeAgent(judge, players, rules));
    for (const player of players) {
      agentCache.addAgent(
        `player-${player.id}`,
        makePlayerAgent(player, players, rules)
      );
    }
    console.log("agents added");

    const rv = {
      agentCache,
      arena,
      judge,
      players,
      arenaDescription,
      rules,
      roundHistory: [
        {
          arenaDescription: "",
          grid: grid,
          actions: [],
          round: 0,
        },
      ],
    };
    contestLogger.info(JSON.stringify(rv, null, 2));
    return rv;
  },
});

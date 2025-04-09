import { Workflow, Step } from "@mastra/core/workflows";
import {
  contestWorkflowRoundSchema,
  contestWorkflowSetupSchema,
  PlayerActionSchema,
} from "../../types/schemas.d";
import { makeArenaAgent } from "../agents/arena";
import { makeJudgeAgent } from "../agents/judge";
import { makePlayerAgent } from "../agents/player";
import { AgentCache } from "../agents/util/agentcache";
import { describeRoundForPlayer, generateGrid } from "../agents/util/stadium";
import { contestLogger } from "../../logging";
import { ContestRound } from "../../types/types";

export function makeContestWorkflow() {
  const workflow = new Workflow({
    name: "Contest",
    triggerSchema: contestWorkflowSetupSchema,
  });
  workflow.step(startContestStep).then(startRoundStep).commit();
  return workflow;
}

/**
 * This step is responsible for starting the contest.
 * It will create the arena, judge, and players.
 * It will also determine the setup locations for the players.
 */
const startContestStep = new Step({
  id: "startContest",
  outputSchema: contestWorkflowRoundSchema,
  execute: async ({ context }) => {
    const {
      arena,
      judge,
      players,
      arenaDescription,
      rules,
      arenaHeight,
      arenaWidth,
      maxFeatures,
      requiredFeatures,
    } = context.triggerData;
    const arenaAgent = makeArenaAgent(arena, players, arenaDescription);
    const grid = await generateGrid(
      arenaWidth,
      arenaHeight,
      maxFeatures,
      requiredFeatures,
      arenaDescription,
      players,
      arenaAgent
    );

    const agentCache = new AgentCache();
    agentCache.addAgent("arena", arenaAgent);
    agentCache.addAgent("judge", makeJudgeAgent(judge, players, rules));
    for (const player of players) {
      agentCache.addAgent(
        `player-${player.id}`,
        makePlayerAgent(player, players, rules)
      );
    }

    const rv = {
      agentCache,
      roundHistory: [
        {
          arenaDescription: "",
          grid: grid,
          actions: [],
        },
      ],
      roundNumber: 0,
    };
    contestLogger.debug("Setup results: " + JSON.stringify(rv, null, 2));
    return rv;
  },
});

const startRoundStep = new Step({
  id: "startRound",
  outputSchema: contestWorkflowRoundSchema,
  execute: async ({ context }) => {
    const { arena, judge, players, arenaDescription, rules } =
      context.triggerData;
    if (context.steps.startContest.status !== "success") {
      throw new Error("Failed to start contest");
    }
    const { agentCache, roundHistory, roundNumber } =
      context.steps.startContest?.output;

    contestLogger.info(
      "Starting round: " + JSON.stringify(roundHistory, null, 2)
    );
    const round: ContestRound = roundHistory[roundHistory.length - 1];
    const newRound: ContestRound = {
      actions: {},
      arenaDescription,
      grid: round.grid,
      status: {},
    };
    // collect actions from each player
    for (const player of players) {
      const playerStatus = {
        health: 100,
        inventory: [],
        status: "fresh",
      };
      const agent = agentCache.getAgent("arena");
      const roundDescription = await describeRoundForPlayer({
        agent,
        arenaDescription: arenaDescription + "\n" + round.arenaDescription,
        extraInstructions: "First round!",
        grid: round.grid,
        player,
        playerStatus,
        roundNumber: roundNumber + 1,
      });
      const prompt = [
        roundDescription,
        'Please respond with your action in the following json format: {"action": <action>, "narration": <narration>}',
      ].join("\n");
      const playerAgent = agentCache.getAgent(`player-${player.id}`);
      const response = await playerAgent.generate(prompt, {
        output: PlayerActionSchema,
      });
      contestLogger.info("Player action: " + JSON.stringify(response, null, 2));
      const playerAction = response.output;
      newRound.actions[player.id] = playerAction;
    }
    contestLogger.info("New round: " + JSON.stringify(newRound, null, 2));
    return {
      agentCache,
      arena,
      judge,
      players,
      arenaDescription,
      rules,
      roundHistory: [...roundHistory, newRound],
    };
  },
});

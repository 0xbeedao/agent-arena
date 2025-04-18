import { Workflow, Step } from "@mastra/core/workflows";
import {
  contestWorkflowRoundSchema,
  contestWorkflowSetupSchema,
  PlayerActionSchema,
} from "../../types/schemas.d";
import { contestLogger } from "../../logging";
import {
  ContestRound,
  ContestWorkflowRound,
  ContestWorkflowSetup,
  PlayerStatus,
} from "../../types/types";
import { AgentCache } from "../agents/util/agentcache";
import { judgeAgent } from "../agents/judge";
import { arenaAgent } from "../agents/arena";
import { mastra } from "..";
import { makePlayerAgent } from "../agents/player";
import { generateGrid, generateJudgement, generatePlayerAction } from "../core";

export function makeContestWorkflow() {
  const workflow = new Workflow({
    name: "Contest",
    triggerSchema: contestWorkflowSetupSchema,
  });
  workflow
    .step(startContestStep)
    .then(startRoundStep)
    .then(collectPlayerActionsStep)
    .then(generateJudgeResponseStep)
    .commit();
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
      players,
      arenaDescription,
      arenaHeight,
      arenaWidth,
      maxFeatures,
      requiredFeatures,
    } = context.triggerData as ContestWorkflowSetup;
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
    for (const player of players) {
      agentCache.addAgent(player.id, makePlayerAgent(player));
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
    const { agentCache, roundHistory, roundNumber } = context.steps.startContest
      ?.output as ContestWorkflowRound;

    contestLogger.info(
      "Starting round: " + JSON.stringify(roundHistory, null, 2)
    );
    const round: ContestRound = {
      actions: {},
      arenaDescription,
      positions: {},
      results: {},
      status: {},
    };

    return {
      agentCache,
      roundHistory: [...roundHistory, round],
      roundNumber: roundNumber + 1,
    };
  },
});

const collectPlayerActionsStep = new Step({
  id: "collectPlayerActions",
  outputSchema: contestWorkflowRoundSchema,
  execute: async ({ context }) => {
    const { players, arenaDescription, rules } = context.triggerData;
    if (context.steps.startRound.status !== "success") {
      throw new Error("Failed to start round");
    }
    const { agentCache, roundHistory, roundNumber } = context.steps.startRound
      ?.output as ContestWorkflowRound;
    const round = roundHistory[roundHistory.length - 1];

    // collect actions from each player
    for (const player of players) {
      const playerStatus = {
        health: 100,
        inventory: [],
        status: "fresh",
      };

      const extraInstructions =
        roundNumber === 1 ? `The rules are: ${rules.join("\n")}` : "";

      const playerAction = await generatePlayerAction({
        agentCache,
        arenaDescription,
        extraInstructions,
        player,
        playerStatus,
        round,
        roundNumber,
      });
      round.actions[player.id] = playerAction;
    }
    contestLogger.info(
      "New round after players: " + JSON.stringify(round, null, 2)
    );

    return {
      agentCache,
      roundHistory,
      roundNumber,
    };
  },
});

const generateJudgeResponseStep = new Step({
  id: "generateJudgeResponse",
  outputSchema: contestWorkflowRoundSchema,
  execute: async ({ context }) => {
    const { arena, judge, players, arenaDescription, rules } =
      context.triggerData;
    if (context.steps.collectPlayerActions.status !== "success") {
      throw new Error("Failed to collect player actions");
    }
    const { roundHistory, roundNumber } = context.steps.collectPlayerActions
      ?.output as ContestWorkflowRound;
    const round = roundHistory[roundHistory.length - 1];
    const extraInstructions =
      roundNumber === 1 ? `The rules are: ${rules.join("\n")}` : "";
    const judgeResponse = await generateJudgement({
      judgeAgent,
      arenaDescription,
      extraInstructions,
      round,
    });
    contestLogger.info(
      "Judge response: " + JSON.stringify(judgeResponse, null, 2)
    );

    round.arenaDescription = judgeResponse.arenaDescription;
    round.grid = judgeResponse.grid;
    round.status = judgeResponse.results.reduce(
      (acc, result) => {
        acc[result.playerId] = result.status;
        return acc;
      },
      {} as Record<string, PlayerStatus>
    );

    return {
      agentCache,
      roundHistory,
      roundNumber,
    };
  },
});

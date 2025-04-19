import { Workflow, Step } from "@mastra/core/workflows";
import {
  contestWorkflowRoundSchema,
  contestWorkflowSetupSchema,
} from "../../types/schemas.d";
import { contestLogger } from "../../logging";
import {
  ContestRound,
  ContestWorkflowRound,
  ContestWorkflowSetup,
  JudgeResult,
  JudgeResultList,
  PlayerResult,
  PlayerStatus,
} from "../../types/types";
import { generateGrid, generateJudgement, generateNarrativeForJudgement, generatePlayerAction, generatePlayerStatusUpdates, generatePositionUpdates} from "../core";

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
  inputSchema: contestWorkflowSetupSchema,
  outputSchema: contestWorkflowRoundSchema,
  execute: async ({ context, mastra }) => {
    if (!mastra) {
      throw new Error("Can't get Mastra Instance");
    }
    const {
      arena,
      judge,
      players,
      arenaDescription,
      arenaHeight,
      arenaWidth,
      maxFeatures,
      requiredFeatures,
      rules,
    } = context.triggerData as ContestWorkflowSetup;

    
    // test agents to make sure they exist
    for (const key of [arena, judge, ...players]) {
      const agent = mastra.getAgent(key);
      if (!agent) {
        throw new Error(`Could not load agent: "${key}`);
      }
    }

    const arenaAgent = mastra.getAgent(arena);

    const {description, features: positions} = await generateGrid(
      arenaWidth,
      arenaHeight,
      maxFeatures,
      requiredFeatures,
      arenaDescription,
      players,
      arenaAgent
    );    

    const status:{ [key: string]: PlayerStatus } = {};
    for (const player of players) {
      status[player] = {
        status: "Fresh",
        health: 100,
        inventory: [],
      } as PlayerStatus;
    }

    const narrative = `This is the first round, all players are in position. Rules: ${rules}`;
   
    const rv = {
      roundHistory: [
        {
          actions: {},
          arenaDescription: description,
          narrative,
          positions,
          results: {},
          status,
        } as ContestRound,
      ],
      roundNumber: 0,
    } as ContestWorkflowRound;
    contestLogger.debug("Setup results: " + JSON.stringify(rv, null, 2));
    return rv;
  },
});


/**
 * Adds a new ContestRound to history.
 */
const startRoundStep = new Step({
  id: "startRound",
  inputSchema: contestWorkflowRoundSchema,
  outputSchema: contestWorkflowRoundSchema,
  execute: async ({ context, mastra }) => {
    
    if (!mastra) {
      throw new Error("Can't get Mastra Instance");
    }

    if (context.steps.startContest.status !== "success") {
      throw new Error("Failed to start round");
    }

    const { roundHistory, roundNumber } = context.steps.startContest
      ?.output as ContestWorkflowRound;

    // skip the first round, we already added that
    if (roundNumber > 0) {
      contestLogger.debug("First round, skipping addround");
      return {
        roundHistory,
        roundNumber: 1, // 1-based counting for rounds
      }
    }
    
    const { arena } = context.triggerData;
    const arenaAgent = mastra.getAgent(arena);

    const lastRound: ContestRound = roundHistory[roundHistory.length - 1];
    const judgeResults: JudgeResultList = Object.keys(lastRound.results).map(
      (key) => {
        const result: PlayerResult = lastRound.results[key];
        return {
          playerId: result.playerId,
          result: result.result,
          reason: result.reason,
        } as JudgeResult;
    })
    const narrative = await generateNarrativeForJudgement({
      arenaAgent,
      arenaDescription: lastRound.arenaDescription,
      extraInstructions: "",
      judgeResults,
      round: lastRound,
    })
    
    const round: ContestRound = {
      actions: {},
      arenaDescription: lastRound.arenaDescription,
      narrative,
      positions: lastRound.positions,
      results: {},
      status: lastRound.status,
    };

    return {
      roundHistory: [...roundHistory, round],
      roundNumber: roundNumber + 1,
    };
  },
});

const collectPlayerActionsStep = new Step({
  id: "collectPlayerActions",
  outputSchema: contestWorkflowRoundSchema,
  execute: async ({ context, mastra }) => {

    if (!mastra) {
      throw new Error("Could not get Mastra Instance");
    }
    contestLogger.info(`Keys of context.steps: ${JSON.stringify(Object.keys(context.steps))}`)

    const { arena, players, arenaDescription, rules } = context.triggerData;
    if (context.steps.startRound.status !== "success") {
      throw new Error("Failed to start round");
    }

    const arenaAgent = mastra.getAgent(arena);

    const { roundHistory, roundNumber } = context.steps.startRound
      ?.output as ContestWorkflowRound;

    const round: ContestRound = roundHistory[roundHistory.length - 1];

    // collect actions from each player
    for (const player of players) {
      const playerAgent = mastra.getAgent(player);
      const playerStatus = round.status[player];

      const playerAction = await generatePlayerAction({
        arenaAgent,
        arenaDescription,
        extraInstructions: round.narrative,
        player,
        playerAgent,
        playerStatus,
        round,
        roundNumber,
      });
      round.actions[player] = playerAction;
    }
    contestLogger.info(
      "New round after players: " + JSON.stringify(round, null, 2)
    );

    return {
      roundHistory,
      roundNumber,
    };
  },
});

const generateJudgeResponseStep = new Step({
  id: "generateJudgeResponse",
  outputSchema: contestWorkflowRoundSchema,
  execute: async ({ context, mastra }) => {
    if (!mastra) {
      throw new Error("Could not get Mastra Instance");
    }
    const { judge, arenaDescription, rules } =
      context.triggerData;
    if (context.steps.collectPlayerActions.status !== "success") {
      throw new Error("Failed to collect player actions");
    }
    const { agentCache, roundHistory, roundNumber } = context.steps.collectPlayerActions
      ?.output as ContestWorkflowRound;
    const round: ContestRound = roundHistory[roundHistory.length - 1];
    const extraInstructions =
      roundNumber === 1 ? `The rules are: ${rules}` : "";
    const judgeAgent = mastra.getAgent(judge);
    
    const judgeResults:JudgeResultList = await generateJudgement({
      judgeAgent,
      arenaDescription,
      extraInstructions,
      round,
    });
    contestLogger.info(
      "Judge response: " + JSON.stringify(judgeResults, null, 2)
    );

    const roundProps = {
      judgeAgent,
      arenaDescription,
      judgeResults,
      round
    };

    const statusCall = generatePlayerStatusUpdates(roundProps);
    const positionCall = generatePositionUpdates(roundProps);

    const [playerStatuses, positions] = await Promise.all([statusCall, positionCall]);
    round.positions = positions;
    round.status = playerStatuses;

    const rv = {
      agentCache,
      roundHistory,
      roundNumber,
    };

    contestLogger.info("Final Judge results: " + JSON.stringify(rv, null, 2));

    return rv;
  },
});

// will call generateNarrative in start of next round.

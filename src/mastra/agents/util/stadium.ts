import type {
  PlayerAction,
  GridFeature,
  Participant,
  Point,
  PlayerStatus,
  ContestRound,
  JudgeResponse,
  JudgeResult,
  JudgeResultList,
  PlayerResult,
} from "../../../types/types.d";
import {
  GridFeatureListSchema,
  JudgeResultListSchema,
  PlayerActionSchema,
  PlayerStatusSchema,
  PointSchema,
} from "../../../types/schemas.d";
import { Agent } from "@mastra/core/agent";
import { arenaLogger } from "../../../logging";
import { AgentCache } from "./agentcache";
import { z } from "zod";
import { A } from "@mobily/ts-belt";
import { parseResponse } from "./parser";

function serializePoint(point: Point): string {
  return `${point.x},${point.y}`;
}

function deserializePoint(str: string): Point {
  const [x, y] = str.split(",").map(Number);
  return { x, y };
}

export function addFeatures(
  featureMap: { [key: string]: Point },
  features: Array<GridFeature>
) {
  for (const feature of features) {
    addFeature(featureMap, feature);
  }
  arenaLogger.debug("featureMap: " + JSON.stringify(featureMap, null, 2));
}

export function addFeature(
  featureMap: { [key: string]: Point },
  feature: GridFeature
) {
  const { name, position, endPosition } = feature;
  if (!endPosition) {
    featureMap[`feature:${name}`] = position;
    arenaLogger.debug("Set " + name + " at " + serializePoint(position));
  } else {
    const start = position;
    const end = endPosition;
    const direction = { x: end.x - start.x, y: end.y - start.y };
    for (
      let i = 0;
      i <= Math.max(Math.abs(direction.x), Math.abs(direction.y));
      i++
    ) {
      const current = {
        x: Math.floor(
          start.x +
            (direction.x * i) /
              Math.max(Math.abs(direction.x), Math.abs(direction.y))
        ),
        y: Math.floor(
          start.y +
            (direction.y * i) /
              Math.max(Math.abs(direction.x), Math.abs(direction.y))
        ),
      };
      featureMap[`feature:${name}.${i}`] = current;
      arenaLogger.debug(`Set ${name}.${i} at ${serializePoint(current)}`);
    }
  }
}

export interface RoundDescriptionParams {
  agent: Agent;
  arenaDescription: string;
  extraInstructions: string;
  roundNumber: number;
  playerStatus: PlayerStatus;
}

/**
 * To be an agent call eventually, this function will describe the round to the player
 * @param agent
 * @param player
 * @param playerStatus
 * @param grid
 * @param arenaDescription
 * @param extraInstructions
 * @param roundNumber
 * @returns
 */
export async function describeRoundForPlayer(params: RoundDescriptionParams) {
  const {
    playerStatus,
    arenaDescription,
    extraInstructions,
    roundNumber,
  } = params;
  return Promise.resolve(
    [
      `This arena is: "${arenaDescription}"`,
      `The arena notes are: ${extraInstructions}`,
      `The current round is ${roundNumber}`,
      `Your status is: ${JSON.stringify(playerStatus)}`,
    ].join("\n")
  );
}

export interface Grid {
  description: string,
  features: { [key: string]: Point }
}

export async function generateGrid(
  width: number,
  height: number,
  maxFeatures: number,
  requiredFeatures: Array<GridFeature>,
  description: string,
  players: Participant[],
  agent: Agent
): Promise<Grid> {
  const features: { [key: string]: Point } = {};

    arenaLogger.debug("features: " + JSON.stringify(features, null, 2));
  if (requiredFeatures.length > 0) {
    arenaLogger.info(
      "Adding " + requiredFeatures.length + " required features"
    );
    addFeatures(features, requiredFeatures);
  }

  maxFeatures -= requiredFeatures.length;

  if (maxFeatures > 0) {
    // get features from the agent
    const responseFeatures = await generateFeatures(
      agent,
      description,
      width,
      height,
      maxFeatures
    );
    addFeatures(features, responseFeatures);
  }

  arenaLogger.debug("features now: " + JSON.stringify(features, null, 2));

  arenaLogger.debug("generating player positions");
  for (const player of players) {
    const playerPosition = randomPosition(height, width, features);
    features[`player:${player.name}`] = playerPosition;
    arenaLogger.debug(
      "Set player " + player.name + " at " + serializePoint(playerPosition)
    );
  }
  const grid: Grid = {
    description: `${description} a (${height}x${width}) grid`,
    features
  };
  arenaLogger.debug("grid: " + JSON.stringify(grid, null, 2));
  return grid;
}

export async function generateFeatures(
  agent: Agent,
  description: string,
  width: number,
  height: number,
  maxFeatures: number
) {
  // Generate the features
  const prompt = [
    `This arena is "${description}"`,
    `Please generate ${maxFeatures} random features for the arena`,
    `these will be used to generate the arena grid(${width}x${height})`,
    "The features should be random objects that can be used by the players to complete the game, ",
    "or else they should be obstacles that the players must avoid",
    "respond in JSON, with the following format:",
    '[ { "name": "feature_name", "position": {"x": <number>, "y": <number>}, "endPosition (optional)": {"x": <number>, "y": <number>} } ]',
    "examples of features:",
    " - a pile of boxes",
    " - a tree",
    " - a rock",
    " - a bush",
    " - a door",
    " - a car (uses endPosition)",
    " - a wall (may use endPosition)",
  ].join("\n");

  arenaLogger.debug("prompt: " + prompt);

  const response = await agent.generate(prompt, {
    output: GridFeatureListSchema,
  });
  const responseFeatures = parseResponse(response, GridFeatureListSchema);
  arenaLogger.debug("--- features", responseFeatures);
  return responseFeatures;
}

export interface GenerateJudgementProps {
  judgeAgent: Agent;
  arenaDescription: string;
  extraInstructions: string;
  round: ContestRound;
}

export async function generateJudgement(
  props: GenerateJudgementProps
): Promise<JudgeResultList> {
  const { arenaDescription, extraInstructions, judgeAgent, round } = props;
  const prompt = [
    `This arena is "${arenaDescription}"`,
    `The arena notes are: ${extraInstructions}`,
    `The current objects and players on the grid are: ${JSON.stringify(round.positions)}`,
    `Players have submitted the following actions: ${JSON.stringify(round.actions)}`,
    `Players have the following statuses: ${JSON.stringify(round.status)}`,
    "Please judge the actions for each player and make any changes to their status",
    "These results will be used to update player statuses, and to generate a narrative for the next round",
    "Example results:",
    `[{playerId: "player1", result: "success, add a key to inventory", reason: "Moved right and found a key"},`,
    `{ playerId: "player2", result: "success with consequences", reason: "Moved right but triggered a trap" }]`,
    `return the results in json format: [{playerId: <playerId>, result: <result text>, reason: <reason text>}]`,
  ].join("\n");
  arenaLogger.debug("prompt: " + prompt);
  const response = await judgeAgent.generate(prompt, {
    output: JudgeResultListSchema,
  });
  arenaLogger.info("Judge response: " + JSON.stringify(response, null, 2));
  const judgeResults = response.object as JudgeResultList;
  return judgeResults;
}

export interface GenerateRoundUpdatesProps {
  judgeAgent: Agent;
  arenaDescription: string;
  judgeResults: JudgeResult[];
  round: ContestRound;
}

export async function generatePositionUpdates(
  props: GenerateRoundUpdatesProps
): Promise<{ [key: string]: Point }> {
  const { judgeAgent, arenaDescription, judgeResults, round } = props;

  const prompt = [
    `This arena is "${arenaDescription}"`,
    `Previously, the arena has objects and players at ${JSON.stringify(round.positions)}`,
    `The judge has returned the following results: ${JSON.stringify(judgeResults)}`,
    "Please generate the new positions for the players in the same JSON format as the original positions",
  ].join("\n");

  const response = await judgeAgent.generate(prompt, {
    output: z.record(z.string(), PointSchema),
  });
  const positionUpdates: Record<string, Point> = parseResponse(
    response,
    z.record(z.string(), PointSchema)
  );

  return updateGridFromPlayerPositions(positionUpdates, round.positions);
}

export async function generatePlayerStatusUpdates(
  props: GenerateRoundUpdatesProps
): Promise<Record<string, PlayerStatus>> {
  const { judgeAgent, arenaDescription, judgeResults, round } = props;
  const generationPromises = judgeResults.map((result) =>
    generatePlayerStatus({
      agent: judgeAgent,
      result,
      playerStatus: round.status[result.playerId],
    })
  );
  const playerResults: PlayerResult[] = await Promise.all(generationPromises);
  await Promise.all(generationPromises);

  return updateStatusesFromJudgeResults(playerResults, round.status);
}
export interface GenerateNarrativeForJudgementProps {
  arenaAgent: Agent;
  arenaDescription: string;
  extraInstructions: string;
  judgeResults: JudgeResult[];
  round: ContestRound;
}

export async function generateNarrativeForJudgement(
  props: GenerateNarrativeForJudgementProps
): Promise<string> {
  const {
    arenaAgent,
    arenaDescription,
    extraInstructions,
    judgeResults,
    round,
  } = props;
  const prompt = [
    `This previous round arena description is"${arenaDescription}"`,
    `The arena notes are: ${extraInstructions}`,
    `The objects and players are positioned: ${JSON.stringify(round.positions)}`,
    `Players have submitted the following actions: ${JSON.stringify(round.actions)}`,
    `The judge has returned the following results: ${JSON.stringify(judgeResults)}`,
    "Please generate a narrative to give to the players in the next round, summarizing the results of the previous round in a contest announcer style",
  ].join("\n");
  arenaLogger.debug("prompt: " + prompt);
  const response = await arenaAgent.generate(prompt, {
    output: z.string(),
  });
  const narrative: string = parseResponse(response);
  arenaLogger.info("Narrative: " + narrative);
  return narrative;
}

export interface GeneratePlayerActionProps {
  arenaAgent: Agent;
  playerAgent: Agent;
  arenaDescription: string;
  extraInstructions: string;
  player: Participant;
  playerStatus: PlayerStatus;
  round: ContestRound;
  roundNumber: number;
}

export async function generatePlayerAction(
  props: GeneratePlayerActionProps
): Promise<PlayerAction> {
  const {
    arenaAgent,
    playerAgent,
    arenaDescription,
    extraInstructions,
    player,
    playerStatus,
    round,
    roundNumber,
  } = props;
  const roundDescription = await describeRoundForPlayer({
    agent: arenaAgent,
    arenaDescription: arenaDescription + "\n" + round.arenaDescription,
    extraInstructions,
    playerStatus,
    roundNumber: roundNumber + 1,
  });

  // generate the player action
  const prompt = [
    roundDescription,
    'Please respond with your action in the following json format: {"action": <action>, "target (optional)": {"x": <number>, "y": <number>}, "narration": <narration>}',
  ].join("\n");

  const response = await playerAgent.generate(prompt, {
    output: PlayerActionSchema,
  });
  arenaLogger.info("Player action: " + JSON.stringify(response, null, 2));
  return parseResponse(response, PlayerActionSchema);
}

export interface GeneratePlayerStatusProps {
  agent: Agent;
  result: JudgeResult;
  playerStatus: PlayerStatus;
}

export async function generatePlayerStatus(
  props: GeneratePlayerStatusProps
): Promise<PlayerResult> {
  const { agent, result, playerStatus } = props;
    const prompt = [
    `The judge has returned the following result: ${JSON.stringify(result)}`,
    `The player has the following status: ${JSON.stringify(playerStatus)}`,
    "Please generate an updated status for the player in the same format as the original status",
  ].join("\n");
  const response = await agent.generate(prompt, {
    output: PlayerStatusSchema,
  });
  arenaLogger.info("generate status results: " + JSON.stringify(response, null, 2));
  const status = response.object;
  return {
    status,
    ...result,
  };
}

export function randomPosition(
  height: number,
  width: number,
  features: { [key: string]: Point }
): Point {
  let position: Point;
  do {
    position = {
      x: Math.floor(Math.random() * width),
      y: Math.floor(Math.random() * height),
    };
  } while (A.includes(Object.values(features), position));
  return position;
}

export function updateGridFromPlayerPositions(
  playerPositions: { [key: string]: Point },
  features: { [key: string]: Point }
): { [key: string]: Point } {
  for (const [id, position] of Object.entries(playerPositions)) {
    features[`player:${id}`] = position;
  }
  return features;
}

export function updateStatusesFromJudgeResults(
  judgeResults: JudgeResult[],
  statuses: Record<string, PlayerStatus>
) {
  for (const judgeResult of judgeResults) {
    const { playerId } = judgeResult;
    const status = statuses[playerId];
    statuses[playerId] = status;
  }
  return statuses;
}

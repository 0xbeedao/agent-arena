import type {
  PlayerAction,
  GridFeature,
  Participant,
  Point,
  PlayerStatus,
  ContestRound,
  JudgeResponse,
  JudgeResult,
  PlayerResult,
  Grid,
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
import { parseResponse } from "./parser";

function serializePoint(point: Point): string {
  return `${point.x},${point.y}`;
}

function deserializePoint(str: string): Point {
  const [x, y] = str.split(",").map(Number);
  return { x, y };
}

export interface RoundDescriptionParams {
  agent: Agent;
  arenaDescription: string;
  extraInstructions: string;
  grid: Grid;
  player: Participant;
  playerStatus: PlayerStatus;
  roundNumber: number;
}

export function addFeatures(
  featureMap: { [key: string]: string },
  features: Array<GridFeature>
) {
  for (const feature of features) {
    addFeature(featureMap, feature);
  }
  arenaLogger.debug("featureMap: " + JSON.stringify(featureMap, null, 2));
}

export function addFeature(
  featureMap: { [key: string]: string },
  feature: GridFeature
) {
  const { name, position, endPosition } = feature;
  if (!endPosition) {
    featureMap[serializePoint(position)] = name;
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
      featureMap[serializePoint(current)] = name;
      arenaLogger.debug("Set " + name + " at " + serializePoint(current));
    }
  }
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
    agent,
    player,
    playerStatus,
    grid,
    arenaDescription,
    extraInstructions,
    roundNumber,
  } = params;
  return Promise.resolve(
    [
      `This arena is: "${arenaDescription}"`,
      `The arena notes are: ${extraInstructions}`,
      `The current grid is ${JSON.stringify(grid)}`,
      `The current round is ${roundNumber}`,
      `Your status is: ${JSON.stringify(playerStatus)}`,
    ].join("\n")
  );
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
  const features: { [key: string]: string } = {};
  const playerPositions: { [key: string]: Point } = {};

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
  arenaLogger.debug("features: " + JSON.stringify(features, null, 2));
  if (requiredFeatures.length > 0) {
    arenaLogger.info(
      "Adding " + requiredFeatures.length + " required features"
    );
    addFeatures(features, requiredFeatures);
  }

  arenaLogger.debug("features now: " + JSON.stringify(features, null, 2));

  arenaLogger.debug("generating player positions");
  for (const player of players) {
    const playerPosition = randomPosition(height, width, features);
    playerPositions[player.name] = playerPosition;
    features[serializePoint(playerPosition)] = player.name;
    arenaLogger.debug(
      "Set player " + player.name + " at " + serializePoint(playerPosition)
    );
  }
  const grid: Grid = {
    height,
    width,
    playerPositions,
    features,
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
): Promise<JudgeResponse> {
  const { arenaDescription, extraInstructions, judgeAgent, round } = props;
  const prompt = [
    `This arena is "${arenaDescription}"`,
    `The arena notes are: ${extraInstructions}`,
    `The current grid is: ${JSON.stringify(round.grid)}`,
    `Players have submitted the following actions: ${JSON.stringify(round.actions)}`,
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
  const judgeResults = response.object as JudgeResult[];
  return {
    arenaDescription,
    grid: round.grid,
    results: judgeResults,
  };
}

export interface GenerateRoundUpdatesProps {
  judgeAgent: Agent;
  arenaDescription: string;
  judgeResults: JudgeResult[];
  round: ContestRound;
}

export async function generatePositionUpdates(
  props: GenerateRoundUpdatesProps
): Promise<JudgeResponse> {
  const { judgeAgent, arenaDescription, judgeResults, round } = props;

  const prompt = [
    `This arena is "${arenaDescription}"`,
    `Previously, the players were at the following positions: ${JSON.stringify(round.grid.playerPositions)}`,
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

  round.grid = updateGridFromPlayerPositions(positionUpdates, round.grid);
  return {
    arenaDescription,
    grid: round.grid,
    results: judgeResults,
  };
}

export async function generatePlayerStatusUpdates(
  props: GenerateRoundUpdatesProps
): Promise<JudgeResponse> {
  const { judgeAgent, arenaDescription, judgeResults, round } = props;
  const generationPromises = judgeResults.map((result) =>
    generatePlayerStatus({
      agent: judgeAgent,
      result,
      grid: round.grid,
    })
  );
  const playerResults: PlayerResult[] = await Promise.all(generationPromises);
  await Promise.all(generationPromises);

  updateStatusesFromJudgeResults(playerResults, round.status);
  return {
    arenaDescription,
    grid: round.grid,
    results: playerResults,
  };
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
): Promise<JudgeResponse> {
  const {
    arenaAgent,
    arenaDescription,
    extraInstructions,
    judgeResults,
    round,
  } = props;
  const arenaNarrative = await generateNarrativeFromResults({
    agent: arenaAgent,
    arenaDescription,
    extraInstructions,
    judgeResults,
    round,
  });
  return {
    arenaDescription: arenaNarrative,
    grid: round.grid,
    results: judgeResults,
  };
}

export interface GenerateNarrativeProps {
  agent: Agent;
  arenaDescription: string;
  extraInstructions: string;
  judgeResults: JudgeResult[];
  round: ContestRound;
}

export async function generateNarrativeFromResults(
  props: GenerateNarrativeProps
) {
  const { agent, arenaDescription, extraInstructions, judgeResults, round } =
    props;
  const prompt = [
    `This previous round arena description is"${arenaDescription}"`,
    `The arena notes are: ${extraInstructions}`,
    `The current grid is: ${JSON.stringify(round.grid)}`,
    `Players have submitted the following actions: ${JSON.stringify(round.actions)}`,
    `The judge has returned the following results: ${JSON.stringify(judgeResults)}`,
    "Please generate a narrative to give to the players in the next round, summarizing the results of the previous round in a contest announcer style",
  ].join("\n");
  arenaLogger.debug("prompt: " + prompt);
  const response = await agent.generate(prompt, {
    output: z.string(),
  });
  const narrative = parseResponse(response);
  arenaLogger.info("Narrative: " + narrative);
  return narrative;
}

export interface GeneratePlayerActionProps {
  agentCache: AgentCache;
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
    agentCache,
    arenaDescription,
    extraInstructions,
    player,
    playerStatus,
    round,
    roundNumber,
  } = props;
  const arenaAgent = agentCache.getAgent("arena");
  const roundDescription = await describeRoundForPlayer({
    agent: arenaAgent,
    arenaDescription: arenaDescription + "\n" + round.arenaDescription,
    extraInstructions,
    grid: round.grid,
    player,
    playerStatus,
    roundNumber: roundNumber + 1,
  });

  // generate the player action
  const prompt = [
    roundDescription,
    'Please respond with your action in the following json format: {"action": <action>, "target (optional)": {"x": <number>, "y": <number>}, "narration": <narration>}',
  ].join("\n");
  const playerAgent = agentCache.getAgent(`player-${player.id}`);
  const response = await playerAgent.generate(prompt, {
    output: PlayerActionSchema,
  });
  arenaLogger.info("Player action: " + JSON.stringify(response, null, 2));
  return response.object as PlayerAction;
}

export interface GeneratePlayerStatusProps {
  agent: Agent;
  result: JudgeResult;
  grid: Grid;
}

export async function generatePlayerStatus(
  props: GeneratePlayerStatusProps
): Promise<PlayerResult> {
  const { agent, result, grid } = props;
  const playerStatus = grid.players[result.playerId];
  const prompt = [
    `The current grid is: ${JSON.stringify(grid)}`,
    `The judge has returned the following result: ${JSON.stringify(result)}`,
    `The player has the following status: ${JSON.stringify(playerStatus)}`,
    "Please generate an updated status for the player in the same format as the original status",
  ].join("\n");
  const response = await agent.generate(prompt, {
    output: PlayerStatusSchema,
  });
  const status = parseResponse(response, PlayerStatusSchema);
  return {
    status,
    ...result,
  };
}

export function randomPosition(
  height: number,
  width: number,
  features: { [key: string]: string }
): Point {
  let position: Point;
  do {
    position = {
      x: Math.floor(Math.random() * width),
      y: Math.floor(Math.random() * height),
    };
  } while (features[serializePoint(position)]);
  return position;
}

export function updateGridFromPlayerPositions(
  playerPositions: Record<string, Point>,
  grid: Grid
) {
  for (const [playerId, position] of Object.entries(playerPositions)) {
    const { x: targetX, y: targetY } = position;
    const { x: currentX, y: currentY } = grid.playerPositions[playerId];
    grid.playerPositions[playerId] = { x: targetX, y: targetY };
    grid.features[serializePoint({ x: currentX, y: currentY })] = "";
    grid.features[serializePoint({ x: targetX, y: targetY })] = playerId;
  }
  return grid;
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

import type {
  ArenaFeature,
  Participant,
  Point,
  PlayerStatus,
} from "../../../types/types.d";
import { GridFeatureListSchema } from "../../../types/schemas.d";
import { Agent } from "@mastra/core/agent";
import { arenaLogger } from "../../../logging";

interface Grid {
  height: number;
  width: number;
  players: { [key: string]: Point };
  features: { [key: string]: string };
}

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
  requiredFeatures: Array<ArenaFeature>,
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
    players: playerPositions,
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
  const responseFeatures =
    "object" in response
      ? (response.object as ArenaFeature[])
      : (JSON.parse(response.text) as ArenaFeature[]);
  arenaLogger.debug("--- features", responseFeatures);
  return responseFeatures;
}

export function addFeatures(
  featureMap: { [key: string]: string },
  features: Array<ArenaFeature>
) {
  for (const feature of features) {
    addFeature(featureMap, feature);
  }
  arenaLogger.debug("featureMap: " + JSON.stringify(featureMap, null, 2));
}

export function addFeature(
  featureMap: { [key: string]: string },
  feature: ArenaFeature
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

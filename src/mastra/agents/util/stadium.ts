/**
 * This needs to be refactored to be a workflow - "SetupStadium"
 *
 * The stadium is the main object in the game. It is the arena where the players compete.
 * It has a description, a list of players, and a list of judges.
 * It also has a list of rules that the players and judges must follow.
 *
 * The stadium is responsible for starting the game, and for updating the state of the game.
 *
 * The stadium is responsible for validating the actions of the players and judges.
 *
 */

import type { ArenaFeature, Participant, Point } from "../../../types/types.d";
import { GridFeaturesResponseSchema } from "../../../types/schemas.d";
import { Agent } from "@mastra/core/agent";
import { arenaLogger } from "../../../logging";

// Define the Grid type to use regular objects
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
  arenaLogger.info("features: " + JSON.stringify(features, null, 2));
  if (requiredFeatures.length > 0) {
    arenaLogger.info(
      "Adding " + requiredFeatures.length + " required features"
    );
    addFeatures(features, requiredFeatures);
  }

  arenaLogger.info("features now: " + JSON.stringify(features, null, 2));

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
  arenaLogger.info("grid: " + JSON.stringify(grid, null, 2));
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
    '[ { "name": "feature_name", "position": [x, y] }, "end_position (optional)": [x, y] ]',
    "examples of features:",
    " - a pile of boxes",
    " - a tree",
    " - a rock",
    " - a bush",
    " - a door",
    " - a car (uses end_position)",
    " - a wall (may use end_position)",
  ].join("\n");

  arenaLogger.debug("prompt: " + prompt);

  const response = await agent.generate(
    [
      {
        role: "user",
        content: prompt,
      },
    ],
    {
      output: GridFeaturesResponseSchema,
    }
  );

  arenaLogger.info("response", response);

  const responseFeatures = JSON.parse(response.text) as ArenaFeature[];
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
  const { name, position, end_position } = feature;
  if (!end_position) {
    featureMap[serializePoint(position)] = name;
    arenaLogger.debug("Set " + name + " at " + serializePoint(position));
  } else {
    const start = position;
    const end = end_position;
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

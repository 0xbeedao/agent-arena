import type { GridFeature, Participant, Point } from "../../types/types.d";
import { GridFeatureListSchema } from "../../types/schemas.d";
import { Agent } from "@mastra/core/agent";
import { arenaLogger } from "../../logging";
import { parseResponse } from "../agents/util/parser";
import { A, D } from "@mobily/ts-belt";

export function serializePoint(point: Point): string {
  return `${point.x},${point.y}`;
}

export function deserializePoint(str: string): Point {
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

export interface Grid {
  description: string;
  features: { [key: string]: Point };
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
  } while (A.includes(D.values(features), position));
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
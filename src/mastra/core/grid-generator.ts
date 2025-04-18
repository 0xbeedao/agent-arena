/**
 * @fileoverview Grid generator for Mastra Arena
 * @description Generates game grids with features and player positions
 * 
 * ```mermaid
 * graph TD
 *   A[Grid Initialization] --> B[Add Required Features]
 *   B --> C[Generate Optional Features]
 *   C --> D[Place Players]
 *   D --> E[Finalize Grid]
 * ```
 */
import type { GridFeature, Participant, Point } from "../../types/types.d";
import { GridFeatureListSchema } from "../../types/schemas.d";
import { Agent } from "@mastra/core/agent";
import { arenaLogger } from "../../logging";
import { parseResponse } from "../agents/util/parser";
import { A, D } from "@mobily/ts-belt";

/**
 * Represents a game grid with features and player positions
 * @property description - Human-readable description of the grid
 * @property features - Map of feature names to their positions
 */
export interface Grid {
  description: string;
  features: { [key: string]: Point };
}

/**
 * Converts a Point object to a string representation
 * @param point The point to serialize
 * @returns Comma-separated string of x,y coordinates
 */
export function serializePoint(point: Point): string {
  return `${point.x},${point.y}`;
}

/**
 * Converts a comma-separated string to a Point object
 * @param str The string to deserialize
 * @returns Point object with x,y coordinates
 */
export function deserializePoint(str: string): Point {
  const [x, y] = str.split(",").map(Number);
  return { x, y };
}

/**
 * Adds multiple features to the feature map
 * @param featureMap The current map of features
 * @param features Array of features to add
 */
export function addFeatures(
  featureMap: { [key: string]: Point },
  features: Array<GridFeature>
) {
  for (const feature of features) {
    addFeature(featureMap, feature);
  }
  arenaLogger.debug("featureMap: " + JSON.stringify(featureMap, null, 2));
}

/**
 * Adds a single feature to the feature map
 * @param featureMap The current map of features
 * @param feature The feature to add
 */
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

/**
 * Generates a game grid with specified dimensions and features
 * @param width Grid width in units
 * @param height Grid height in units
 * @param maxFeatures Maximum number of features to generate (including required ones)
 * @param requiredFeatures Array of mandatory features to include
 * @param description Human-readable description of the grid
 * @param players Array of participants needing positions
 * @param agent AI agent used for generating optional features
 * @returns Promise resolving to the generated Grid object
 * @throws Error if maxFeatures is less than requiredFeatures.length
 */
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

/**
 * Generates optional features using an AI agent
 * @param agent The AI agent to use for generation
 * @param description Grid description for context
 * @param width Grid width
 * @param height Grid height
 * @param maxFeatures Maximum number of features to generate
 * @returns Array of generated GridFeature objects
 */
export async function generateFeatures(
  agent: Agent,
  description: string,
  width: number,
  height: number,
  maxFeatures: number
): Promise<Array<GridFeature>> {
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

/**
 * Generates a random position not occupied by existing features
 * @param height Grid height
 * @param width Grid width
 * @param features Current map of features
 * @returns Random valid Point object
 */
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
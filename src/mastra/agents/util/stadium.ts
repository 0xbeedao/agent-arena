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

import type { Grid, Participant, Point } from "../../../types/types.d";
import { GridFeaturesResponseSchema } from "../../../types/schemas.d";
import { Agent } from "@mastra/core/agent";
import { arenaLogger } from "../../../logging";

export async function generateGrid(
  width: number,
  height: number,
  maxFeatures: number,
  description: string,
  players: Participant[],
  agent: Agent
): Promise<Grid> {
  const features = new Map<Point, string>();
  const playerPositions = new Map<string, Point>();

  if (maxFeatures > 0) {
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

    const features = response.object ?? response.text;
    arenaLogger.debug("--- features", features);
    for (const feature of features) {
      const { name, position, end_position } = feature;
      arenaLogger.debug("Processing " + name);
      if (!end_position) {
        features.set(position, name);
        arenaLogger.debug("Set " + name + " at " + position);
      } else {
        const start = position;
        const end = end_position;
        const direction = { x: end.x - start.x, y: end.y - start.y };
        for (
          let i = 0;
          i < Math.max(Math.abs(direction.x), Math.abs(direction.y));
          i++
        ) {
          const current = {
            x: start.x + direction.x * i,
            y: start.y + direction.y * i,
          };
          features.set(current, name);
          arenaLogger.debug("Set " + name + " at " + current);
        }
      }
    }
  }

  arenaLogger.info("features now: " + JSON.stringify(features, null, 2));
  arenaLogger.debug("generating player positions");
  for (const player of players) {
    const playerPosition = randomPosition(height, width, features);
    playerPositions.set(player.name, playerPosition);
    features.set(playerPosition, player.name);
    arenaLogger.debug("Set player " + player.name + " at " + playerPosition);
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

export function randomPosition(
  height: number,
  width: number,
  features: Map<Point, string>
): Point {
  let position: Point;
  do {
    position = {
      x: Math.floor(Math.random() * width),
      y: Math.floor(Math.random() * height),
    };
  } while (features.has(position));
  return position;
}

/**
 * @file player-actions.ts
 * @module mastra/core/player-actions
 * @description Defines functions for generating and describing player actions in the arena.
 *
 * @mermaid
 * flowchart LR
 *  subgraph Player Action Generation
 *    generatePlayerAction --> describeRoundForPlayer
 *    describeRoundForPlayer --> playerAgent.generate
 *    playerAgent.generate --> parseResponse
 *  end
 */

import type { PlayerAction, PlayerStatus, ContestRound } from "../../types/types.d";
import { PlayerActionSchema } from "../../types/schemas.d";
import { Agent } from "@mastra/core/agent";
import { arenaLogger } from "../../logging";
import { parseResponse } from "../agents/util/parser";

/**
 * Properties for generating a player action.
 *
 * @interface GeneratePlayerActionProps
 * @property {Agent} arenaAgent - The agent representing the arena.
 * @property {Agent} playerAgent - The agent representing the player.
 * @property {string} arenaDescription - Description of the arena.
 * @property {string} extraInstructions - Extra instructions for the player.
 * @property {string} player - The player participant.
 * @property {PlayerStatus} playerStatus - The current status of the player.
 * @property {ContestRound} round - The current contest round.
 * @property {number} roundNumber - The current round number.
 */
export interface GeneratePlayerActionProps {
  arenaAgent: Agent;
  playerAgent: Agent;
  arenaDescription: string;
  extraInstructions: string;
  player: string;
  playerStatus: PlayerStatus;
  round: ContestRound;
  roundNumber: number;
}

/**
 * Generates a player action based on the given properties.
 *
 * @async
 * @function generatePlayerAction
 * @param {GeneratePlayerActionProps} props - The properties needed to generate the player action.
 * @returns {Promise<PlayerAction>} A promise that resolves to a PlayerAction object.
 */
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
    arenaDescription: arenaDescription + "\\n" + round.arenaDescription,
    extraInstructions,
    playerStatus,
    roundNumber: roundNumber + 1,
  });

  // generate the player action
  const prompt = [
    roundDescription,
    'Please respond with your action in the following json format: {"action": <action>, "target (optional)": {"x": <number>, "y": <number>}, "narration": <narration>}',
  ].join("\\n");

  const response = await playerAgent.generate(prompt, {
    output: PlayerActionSchema,
  });
  arenaLogger.info("Player " + player + " action: " + JSON.stringify(response, null, 2));
  return parseResponse(response, PlayerActionSchema);
}

/**
 * Parameters for describing a round to a player.
 *
 * @interface RoundDescriptionParams
 * @property {Agent} agent - The agent responsible for describing the round.
 * @property {string} arenaDescription - Description of the arena.
 * @property {string} extraInstructions - Extra instructions for the round.
 * @property {number} roundNumber - The current round number.
 * @property {PlayerStatus} playerStatus - The current status of the player.
 */
export interface RoundDescriptionParams {
  agent: Agent;
  arenaDescription: string;
  extraInstructions: string;
  roundNumber: number;
  playerStatus: PlayerStatus;
}

/**
 * Describes the round to the player.
 *
 * @async
 * @function describeRoundForPlayer
 * @param {RoundDescriptionParams} params - Parameters for describing the round.
 * @returns {Promise<string>} A promise that resolves to the round description as a string.
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
    ].join("\\n")
  );
}
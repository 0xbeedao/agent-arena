import type { PlayerAction, Participant, PlayerStatus, ContestRound } from "../../types/types.d";
import { PlayerActionSchema } from "../../types/schemas.d";
import { Agent } from "@mastra/core/agent";
import { arenaLogger } from "../../logging";
import { parseResponse } from "../agents/util/parser";

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
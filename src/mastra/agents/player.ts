import { Agent } from "@mastra/core/agent";
import type { Participant } from "../../types/types.js";
import { parseLanguageModel } from "./util/languagemodel-parser.js";
import { getDefaultModel, getLanguageModel } from "../../config.js";

export function makePlayerAgent(player: Participant) {
  let instructions = `You are a player named "${player.name}" in a game, you will be given a personality and a set of game rules.
Each round, you will be given your current state, based on your previous actions.
You will then choose an action to take and respond with the action you chose, narrating your choice for entertainment.
You will respond in JSON format.

Personality: ${player.personality}`;

  if (player.instructions) {
    instructions += `\n${player.instructions}`;
  }

  return new Agent({
    name: player.name,
    instructions,
    model: parseLanguageModel(player.model),
  });
}

const p1: Participant = {
  id: "test-player-1",
  name: "Test Player 1",
  personality: "You are an enthusiastic player, eager to win the game.",
  model: getDefaultModel("player"),
  instructions: "",
};

export const playerAgent1 = makePlayerAgent(p1);

const p2: Participant = {
  id: "test-player-2",
  name: "Test Player 2",
  personality:
    "You are a cautious player, always looking for the best way to win the game.",
  model: getDefaultModel("player"),
  instructions: "",
};

export const playerAgent2 = makePlayerAgent(p2);

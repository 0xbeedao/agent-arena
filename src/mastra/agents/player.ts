import { Agent } from "@mastra/core/agent";
import type { Participant } from "../../types/types.js";
import { parseLanguageModel } from "./util/languagemodel-parser.js";
 
export function makePlayerAgent(player: Participant, players: Participant[], rules: String[]) {
  const otherPlayers = players.filter(p => p.name !== player.name);
  const instructions = `You are a player named "${player.name}" in a game, you will be given a personality and a set of game rules.
Each round, you will be given your current state, based on your previous actions.
You will then choose an action to take and respond with the action you chose, narrating your choice for entertainment.
You will respond in JSON format.

Personality: ${player.personality}

There are ${otherPlayers.length} other players in the game:
${otherPlayers.map(p => `- ${p.name}`).join("\n")}

Rules: ${rules.join("\n")}`;

  return new Agent({
    name: player.name,
    instructions,
    model:  parseLanguageModel(player.model)
  });
}

import { Agent } from "@mastra/core/agent";
import type { Participant } from "../../types/types.js";
import { parseLanguageModel } from "./util/languagemodel-parser.js";
import { arenaLogger } from "../../logging.js";

export function makeArenaAgent(
  arena: Participant,
  players: Participant[],
  arenaDescription: String
) {
  const instructions = `You are a vivid describer of the arena named "${arena.name || "Agent Arena"}" for a game. 
Your job is to describe the arena in a way that is easy to understand and visualize.
You will be given a description of the arena, and events that have happened so far and you will need to describe it in a way that is easy to understand and visualize.
You will respond in JSON format.

Personality: ${arena.personality || "You are a neutral observer."}

There are ${players.length} players in the game:
${players.map((player) => `- ${player.name}`).join("\n")}

Arena: ${arenaDescription}`;

  const model = parseLanguageModel(arena.model);
  arenaLogger.info("model", model);

  return new Agent({
    name: arena.name,
    instructions,
    model,
  });
}

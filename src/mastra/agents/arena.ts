import { Agent } from "@mastra/core/agent";
import { getLanguageModel } from "../../config.js";

const name = process.env.ARENA_ARENA_NAME ?? "The Trial Zone";
const personality =
  process.env.ARENA_ARENA_PERSONALITY ?? "You are a neutral observer.";

export const arenaAgent = new Agent({
  name,
  instructions: `You are a vivid describer of "${name}", an arena for a game. 
Your job is to describe the arena in a way that is easy to understand and visualize.
You will be given a description of the arena, and events that have happened so far and you will need to describe it in a way that is easy to understand and visualize.
You will respond in JSON format.

Personality: ${personality}`,
  model: getLanguageModel("arena"),
});

import { Agent } from "@mastra/core/agent";
import { getLanguageModel } from "../../config.js";

const name = process.env.ARENA_JUDGE_NAME ?? "judge";
const personality =
  process.env.ARENA_JUDGE_PERSONALITY ?? "You are a fair and impartial judge.";

export const judgeAgent = new Agent({
  name,
  instructions: `You are a judge named "${name}" that will be given:
- a set of game rules
- a list of player actions. 
You will then decide the result of the player actions based on the rules.
You will respond in JSON format.

Personality: ${personality}`,
  model: getLanguageModel("judge"),
});

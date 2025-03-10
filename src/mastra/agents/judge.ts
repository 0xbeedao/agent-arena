import { Agent } from "@mastra/core/agent";
import { openai } from "@ai-sdk/openai";
import type { Participant } from "../../types/types.d.ts";
import { parseLanguageModel } from "./util/languagemodel-parser.js";
 
export function makeJudgeAgent(judge: Participant, rules: string[]) {
  const instructions = `You are a judge named "${judge.name} || "The Judge"}" that will be given:
- a personality 
- a set of game rules
- the game state
- a list of player actions. 
You will then decide the result of the player actions based on the rules.
You will respond in JSON format.

Personality: ${judge.personality || "You are a fair and impartial judge."}

Rules: ${rules.join("\n")}`
  return new Agent({
    name: judge.name || "The Judge",
    instructions,
    model: parseLanguageModel(judge.model)
  });
}

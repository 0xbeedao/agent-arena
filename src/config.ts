import { parseLanguageModel } from "./mastra/agents/util/languagemodel-parser";

const GEMINI_MODEL = "openrouter:google/gemini-2.5-pro-exp-03-25:free";
const LLAMA_MODEL = "openrouter:meta-llama/llama-4-maverick:free";
const QUASAR_MODEL = "openrouter:openrouter/quasar-alpha";
const MOONSHOT_MODEL = "openrouter:moonshotai/kimi-vl-a3b-thinking:free";
const GPT4O_NANO_MODEL = "openrouter:openai/gpt-4.1-nano";
// const FREE_MODELS = [GEMINI_MODEL, LLAMA_MODEL, QUASAR_MODEL];

const defaultModels: Record<string, string> = {
  arena: QUASAR_MODEL,
  judge: QUASAR_MODEL,
  player: QUASAR_MODEL,
  narrator: GEMINI_MODEL,
  quasar: QUASAR_MODEL,
  llama: LLAMA_MODEL,
  gemini: GEMINI_MODEL,
  moonshot: MOONSHOT_MODEL,
  gpt4o: GPT4O_NANO_MODEL,
};

export function getLanguageModel(target: string, model = "") {
  if (model) {
    return parseLanguageModel(model);
  }
  if (target in defaultModels) {
    return parseLanguageModel(defaultModels[target]);
  }
  throw new Error(`Unknown target: ${target}`);
}

export function getDefaultModel(target: string) {
  if (target in defaultModels) {
    return defaultModels[target];
  }
  throw new Error(`Unknown target: ${target}`);
}

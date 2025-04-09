import { LanguageModelV1 } from "ai";
import { openai } from "@ai-sdk/openai";
import { anthropic } from "@ai-sdk/anthropic";
import { systemLogger } from "../../../logging";
import { google } from "@ai-sdk/google";
import { createOpenRouter } from "@openrouter/ai-sdk-provider";

if (!process.env.OPENROUTER_API_KEY) {
  throw new Error("OPENROUTER_API_KEY is not set");
}

const openrouter = createOpenRouter({
  apiKey: process.env.OPENROUTER_API_KEY,
  compatibility: "strict",
});

/**
 * Parses a language model from a string
 * @param model - The language model to parse
 * @returns The parsed language model
 */
export function parseLanguageModel(model: string): LanguageModelV1 {
  const parts = model.split(":");
  const provider = parts[0];
  const modelName = parts.length > 2 ? parts.slice(1).join(":") : parts[1];

  if (provider === "openai") {
    systemLogger.debug("Using openai");
    return openai(modelName);
  } else if (provider === "anthropic") {
    systemLogger.debug("Using anthropic");
    return anthropic(modelName);
  } else if (provider === "openrouter") {
    systemLogger.debug(`Using openrouter ${modelName}`);
    return openrouter(modelName);
  } else if (provider === "google") {
    systemLogger.debug(`Using google ${modelName}`);
    return google(modelName);
  } else {
    systemLogger.error(`Unsupported language model provider: ${provider}`);
    throw new Error(`Unsupported language model provider: ${provider}`);
  }
}

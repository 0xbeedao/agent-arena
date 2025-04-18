import { Agent } from "@mastra/core/agent";
import { describe, it, expect } from "vitest";
import { parseLanguageModel } from "../mastra/agents/util/languagemodel-parser";
import { z } from "zod";
import { testLogger } from "../logging";

const MODELS = {
  gpt41nano: "openrouter:openai/gpt-4.1-nano",
  llama4Maverick: "openrouter:meta-llama/llama-4-maverick",
  mistralsmall: "openrouter:mistralai/mistral-small-3.1-24b-instruct:free",
};

const MODEL = MODELS.llama4Maverick;
describe("Model Experiments for " + MODEL, () => {
  it(
    "Should call using " + MODEL + " to received structured output",
    async () => {
      const agent = new Agent({
        name: "test",
        instructions: "You are a test agent",
        model: parseLanguageModel(MODEL),
      });
      const response = await agent.generate(
        'respond with a json object with hello = "world"',
        {
          output: z.object({
            hello: z.string(),
          }),
        }
      );
      expect(response).toBeDefined();
      testLogger.debug(JSON.stringify(response, null, 2));
      expect(response.object).toEqual({ hello: "world" });
    }
  );

  it(
    "Should call using " + MODEL + " to received structured output of a record",
    async () => {
      const agent = new Agent({
        name: "test",
        instructions: "You are a test agent",
        model: parseLanguageModel(MODEL),
      });
      const response = await agent.generate(
        'respond with a json object with hello = "world"',
        {
          output: z.record(z.string(), z.string()),
        }
      );
      expect(response).toBeDefined();
      testLogger.debug(JSON.stringify(response, null, 2));
      expect(response.object).toEqual({ hello: "world" });
    }
  );
});

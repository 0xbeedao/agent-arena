import { describe, it, expect } from "vitest";
import { parseLanguageModel } from "./languagemodel-parser";
import { generateText } from "ai";
import { Agent } from "@mastra/core/agent";
import { z } from "zod";
import { testLogger } from "../../../logging";

describe("parseLanguageModel", () => {
  it("should parse a language model", () => {
    const languageModel = parseLanguageModel("openai:gpt-3.5-turbo");
    expect(languageModel).toBeDefined();
  });

  it("should call a free google model", async () => {
    const languageModel = parseLanguageModel("google:gemini-1.5-flash");
    expect(languageModel).toBeDefined();
    const response = await generateText({
      model: languageModel,
      prompt: "Hello, world!",
    });
    expect(response).toBeDefined();
    expect(response.text).toContain("Hello, world!");
  });

  it("should call a free openrouter model", async () => {
    const languageModel = parseLanguageModel(
      "openrouter:google/gemini-2.5-pro-exp-03-25:free"
    );
    expect(languageModel).toBeDefined();
    const response = await generateText({
      model: languageModel,
      prompt: "As a test, respond with 'Hello'",
    });
    expect(response).toBeDefined();
    testLogger.debug(JSON.stringify(response, null, 2));
    expect(response.text).toContain("Hello");
  });

  it("Should call using a Mastra Agent", async () => {
    const agent = new Agent({
      name: "test",
      instructions: "You are a test agent",
      model: parseLanguageModel("google:gemini-1.5-flash"),
    });
    const response = await agent.generate("Hello, world!");
    expect(response).toBeDefined();
    testLogger.debug(JSON.stringify(response, null, 2));
    expect(response.text).toContain("Hello, world!");
  });

  it("Should call moonshot", async () => {
    const languageModel = parseLanguageModel(
      "openrouter:moonshotai/kimi-vl-a3b-thinking:free"
    );
    expect(languageModel).toBeDefined();
    const response = await generateText({
      model: languageModel,
      prompt: "Hello, world!",
    });
    expect(response).toBeDefined();
    testLogger.debug(JSON.stringify(response, null, 2));
    expect(response.text).toContain("Hello, world!");
  });

  it("Should call using a Mastra Agent to received structured output", async () => {
    const agent = new Agent({
      name: "test",
      instructions: "You are a test agent",
      model: parseLanguageModel("openai:gpt-4o-mini"),
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
    // expect(response.text).toEqual('{"hello":"world"}');
  });

  it("Should call using a GPT4.1 Nano Agent to received structured output", async () => {
    const agent = new Agent({
      name: "test",
      instructions: "You are a test agent",
      model: parseLanguageModel("openrouter:openai/gpt-4.1-nano"),
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
    // expect(response.text).toEqual('{"hello":"world"}');
  });
});

/**
 * Wrapper around an agent that provides a more convenient interface for
 * testing and development.
 */

import { Agent } from "@mastra/core/agent";

export class AgentWrapper {
  private agent: Agent;
  private mocked: boolean;
  private responses: string[];
  private index: number;
  private prompts: string[] = [];

  constructor(agent: Agent, mocked: boolean, responses: string[]) {
    this.agent = agent;
    this.mocked = mocked;
    this.responses = responses;
    this.index = 0;
  }

  getMockedPrompts() {
    return this.prompts;
  }

  getMockedResponses() {
    return this.responses;
  }

  getMockedIndex() {
    return this.index;
  }

  async generate(prompt: string, schema: z.ZodSchema) {
    if (this.mocked) {
      this.index++;
      this.prompts.push(prompt);
      return this.responses[this.index - 1];
    }

    const response = await this.agent.generate(
      [{ role: "user", content: prompt }],
      {
        output: schema,
      }
    );
    return response.text;
  }
}

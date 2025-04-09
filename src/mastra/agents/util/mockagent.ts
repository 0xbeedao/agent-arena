/**
 * Wrapper around an agent that provides a more convenient interface for
 * testing and development.
 */

import { Agent } from "@mastra/core/agent";
import { CoreMessage } from "@mastra/core/llm";

export default class MockAgent extends Agent {
  private mockedResponses: string[] = [];
  private mockedIndex: number = 0;
  private mockedPrompts: string[] = [];

  addMockedResponseString(response: string) {
    this.mockedResponses.push(response);
  }

  addMockedResponseObject(response: any) {
    this.mockedResponses.push(JSON.stringify(response));
  }

  getMockedPrompts() {
    return this.mockedPrompts;
  }

  getMockedResponses() {
    return this.mockedResponses;
  }

  getMockedIndex() {
    return this.mockedIndex;
  }

  async generate(messages: string | string[] | CoreMessage[], _: any) {
    this.mockedIndex++;
    const message = messages[messages.length - 1];
    this.mockedPrompts.push(message as string);
    return {
      text: this.mockedResponses[this.mockedIndex - 1],
      raw: this.mockedResponses[this.mockedIndex - 1],
      usage: {
        prompt_tokens: 0,
        completion_tokens: 0,
      },
    };
  }
}

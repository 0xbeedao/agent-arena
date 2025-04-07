import { Agent } from "@mastra/core/agent";

export class AgentCache {
  private cache: Map<string, Agent> = new Map();

  constructor() {
    this.cache = new Map();
  }

  getAgent(id: string): Agent {
    const agent = this.cache.get(id);
    if (!agent) {
      throw new Error(`Agent not found: ${id}`);
    }
    return agent;
  }

  addAgent(id: string, agent: Agent) {
    this.cache.set(id, agent);
  }
}

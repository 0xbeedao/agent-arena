import { describe } from 'vitest';
/**
 * Agent API module for interacting with the agent controller endpoints.
 */

// Base URL for the API
const API_BASE_URL = 'http://localhost:8000';

/**
 * Interface representing an Agent configuration
 * Based on the AgentConfig model in the backend
 */
export interface AgentConfig {
  id: string;
  name: string;
  description?: string;
  endpoint: string;
  api_key: string;
  metadata: string;
  strategy_id: string;
}

/**
 * Interface for creating a new agent (without ID)
 */
export interface CreateAgentRequest {
  name: string;
  description: string;
  endpoint: string;
  api_key: string;
  metadata: string;
  strategy_id: string;
}

/**
 * Response from creating a new agent
 */
export interface CreateAgentResponse {
  id: string;
}

/**
 * Response from updating an agent
 */
export interface UpdateAgentResponse {
  success: boolean;
}

/**
 * Creates a new agent
 * @param agent The agent configuration to create
 * @returns A promise that resolves to the created agent's ID
 */
export async function createAgent(agent: CreateAgentRequest): Promise<CreateAgentResponse> {
  const response = await fetch(`${API_BASE_URL}/agent`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(agent),
  });

  if (!response.ok) {
    throw new Error(`Failed to create agent: ${response.statusText}`);
  }

  return response.json() as Promise<CreateAgentResponse>;
}

/**
 * Gets an agent by ID
 * @param agentId The ID of the agent to get
 * @returns A promise that resolves to the agent configuration
 */
export async function getAgent(agentId: string): Promise<AgentConfig> {
  const response = await fetch(`${API_BASE_URL}/agent/${agentId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to get agent: ${response.statusText}`);
  }

  return response.json() as Promise<AgentConfig>;
}

/**
 * Gets a list of all agents
 * @returns A promise that resolves to an array of agent configurations
 */
export async function getAgentList(): Promise<Array<AgentConfig>> {
  const response = await fetch(`${API_BASE_URL}/agent`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to get agent list: ${response.statusText}`);
  }

  return response.json() as Promise<Array<AgentConfig>>;
}

/**
 * Updates an agent
 * @param agentId The ID of the agent to update
 * @param agent The updated agent configuration
 * @returns A promise that resolves to a success indicator
 */
export async function updateAgent(agentId: string, agent: AgentConfig): Promise<UpdateAgentResponse> {
  const response = await fetch(`${API_BASE_URL}/agent/${agentId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(agent),
  });

  if (!response.ok) {
    throw new Error(`Failed to update agent: ${response.statusText}`);
  }

  return response.json() as Promise<UpdateAgentResponse>;
}
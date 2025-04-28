/**
 * React Query hooks for the agent API
 */
import { 
  useMutation, 
  useQuery, 
  useQueryClient,
  type UseQueryResult, 
  type UseMutationResult 
} from '@tanstack/react-query';

import { 
  type AgentConfig, 
  type CreateAgentRequest, 
  type CreateAgentResponse, 
  type UpdateAgentResponse,
  createAgent, 
  getAgent, 
  getAgentList, 
  updateAgent 
} from '../agent';

// Query keys for React Query
export const agentKeys = {
  all: ['agents'] as const,
  lists: () => [...agentKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...agentKeys.lists(), { filters }] as const,
  details: () => [...agentKeys.all, 'detail'] as const,
  detail: (id: string) => [...agentKeys.details(), id] as const,
};

/**
 * Hook to fetch a list of all agents
 */
export function useAgentList(): UseQueryResult<Array<AgentConfig>, Error> {
  return useQuery({
    queryKey: agentKeys.lists(),
    queryFn: () => getAgentList(),
  });
}

/**
 * Hook to fetch a single agent by ID
 */
export function useAgent(agentId: string): UseQueryResult<AgentConfig, Error> {
  return useQuery({
    queryKey: agentKeys.detail(agentId),
    queryFn: () => getAgent(agentId),
    enabled: !!agentId, // Only run the query if agentId is provided
  });
}

/**
 * Hook to create a new agent
 */
export function useCreateAgent(): UseMutationResult<CreateAgentResponse, Error, CreateAgentRequest, unknown> {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (newAgent: CreateAgentRequest) => createAgent(newAgent),
    onSuccess: () => {
      // Invalidate the agent list query to refetch the updated list
      void queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
    },
  });
}

/**
 * Hook to update an existing agent
 */
export function useUpdateAgent(): UseMutationResult<UpdateAgentResponse, Error, { agentId: string; agent: AgentConfig }, unknown> {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ agentId, agent }: { agentId: string; agent: AgentConfig }) => 
      updateAgent(agentId, agent),
    onSuccess: (_, variables) => {
      // Invalidate the specific agent query and the agent list
      void queryClient.invalidateQueries({ queryKey: agentKeys.detail(variables.agentId) });
      void queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
    },
  });
}
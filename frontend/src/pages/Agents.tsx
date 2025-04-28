/* eslint-disable camelcase */
import { useState } from "react";
import type { FunctionComponent } from "../common/types";
import { Navbar } from "../components/layout/Navbar";
import { Box } from "../components/ui/Box";
import { StyledBox } from "../components/ui/StyledBox";
import { StyledButton } from "../components/ui/StyledButton";
import {
  useAgentList,
  useAgent,
  useCreateAgent,
  useUpdateAgent
} from "../api/hooks/useAgents";
import type { AgentConfig, CreateAgentRequest } from "../api/agent";

export const Agents = (): FunctionComponent => {
  // State for managing the UI
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  
  // Form state with snake_case property names to match backend API
  const [formData, setFormData] = useState<CreateAgentRequest>({
    name: "",
    endpoint: "",
    api_key: "", // Backend expects snake_case
    metadata: "",
    strategy_id: "" // Backend expects snake_case
  });

  // Fetch agents data
  const { data: agents, isLoading, isError } = useAgentList();
  // We're fetching the selected agent but not using it directly in the UI
  useAgent(selectedAgentId || "");
  
  // Mutations
  const createAgentMutation = useCreateAgent();
  const updateAgentMutation = useUpdateAgent();

  // Handle form input changes
  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>): void => {
    const { name, value } = event.target;
    setFormData((previous) => ({ ...previous, [name]: value }));
  };

  // Reset form and UI state
  const resetForm = (): void => {
    setFormData({
      name: "",
      endpoint: "",
      api_key: "", // Backend expects snake_case
      metadata: "",
      strategy_id: "" // Backend expects snake_case
    });
    setIsCreating(false);
    setIsEditing(false);
    setSelectedAgentId(null);
  };

  // Handle create agent
  const handleCreateAgent = async (event: React.FormEvent): Promise<void> => {
    event.preventDefault();
    try {
      await createAgentMutation.mutateAsync(formData);
      resetForm();
    } catch (error) {
      console.error("Failed to create agent:", error);
    }
  };

  // Handle update agent
  const handleUpdateAgent = async (event: React.FormEvent): Promise<void> => {
    event.preventDefault();
    if (!selectedAgentId) return;
    
    try {
      await updateAgentMutation.mutateAsync({
        agentId: selectedAgentId,
        agent: { ...formData, id: selectedAgentId } as AgentConfig
      });
      resetForm();
    } catch (error) {
      console.error("Failed to update agent:", error);
    }
  };

  // Handle edit button click
  const handleEditClick = (agent: AgentConfig): void => {
    setSelectedAgentId(agent.id);
    setFormData({
      name: agent.name,
      endpoint: agent.endpoint,
      api_key: agent.api_key, // Backend uses snake_case
      metadata: agent.metadata,
      strategy_id: agent.strategy_id // Backend uses snake_case
    });
    setIsEditing(true);
    setIsCreating(false);
  };

  // Render agent list
  const renderAgentList = (): React.ReactNode => {
    if (isLoading) return <p>Loading agents...</p>;
    if (isError) return <p>Error loading agents</p>;
    if (!agents || agents.length === 0) return <p>No agents found</p>;

    return (
      <div className="space-y-4">
        {agents.map((agent) => (
          <StyledBox
            key={agent.id}
            className="p-4"
            position="inner-alt"
            variant="column"
          >
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-xl font-semibold">{agent.name}</h3>
                <p className="text-sm text-gray-600">Endpoint: {agent.endpoint}</p>
                <p className="text-sm text-gray-600">Strategy ID: {agent.strategy_id}</p>
              </div>
              <div className="flex space-x-2">
                <StyledButton
                  variant="secondary"
                  onClick={(): void => {
                    handleEditClick(agent);
                  }}
                >
                  Edit
                </StyledButton>
              </div>
            </div>
          </StyledBox>
        ))}
      </div>
    );
  };

  // Render form
  const renderForm = (): React.ReactNode => {
    const isSubmitting = createAgentMutation.isPending || updateAgentMutation.isPending;
    const formTitle = isCreating ? "Create New Agent" : "Edit Agent";
    const handleSubmit = isCreating ? handleCreateAgent : handleUpdateAgent;

    return (
      <StyledBox
        className="p-6"
        position="inner-alt"
        variant="column"
      >
        <h2 className="text-2xl font-semibold mb-4">{formTitle}</h2>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              required
              className="w-full p-2 border border-gray-300 rounded"
              name="name"
              type="text"
              value={formData.name}
              onChange={handleInputChange}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Endpoint</label>
            <input
              required
              className="w-full p-2 border border-gray-300 rounded"
              name="endpoint"
              type="text"
              value={formData.endpoint}
              onChange={handleInputChange}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
            <input
              required
              className="w-full p-2 border border-gray-300 rounded"
              name="api_key"
              type="text"
              value={formData.api_key}
              onChange={handleInputChange}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Metadata</label>
            <textarea
              className="w-full p-2 border border-gray-300 rounded"
              name="metadata"
              rows={3}
              value={formData.metadata}
              onChange={handleInputChange}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Strategy ID</label>
            <input
              required
              className="w-full p-2 border border-gray-300 rounded"
              name="strategy_id"
              type="text"
              value={formData.strategy_id}
              onChange={handleInputChange}
            />
          </div>
          
          <div className="flex space-x-4 pt-4">
            <button disabled={isSubmitting} type="submit">
              <StyledButton>
                {isSubmitting ? "Saving..." : "Save"}
              </StyledButton>
            </button>
            <StyledButton
              variant="secondary"
              onClick={resetForm}
            >
              Cancel
            </StyledButton>
          </div>
        </form>
      </StyledBox>
    );
  };

  return (
    <div className="flex h-screen w-full flex-col">
      <Navbar />
      <Box className="w-9/12 mx-auto py-8" variant="column">
        <StyledBox position="outer" variant="column">
          <h1 className="text-4xl font-semibold mb-4 font-heading">Agents Management</h1>
          
          {/* Action buttons */}
          <div className="flex justify-between items-center mb-6">
            <div>
              <StyledButton
                onClick={(): void => {
                  setIsCreating(true);
                  setIsEditing(false);
                  setSelectedAgentId(null);
                  setFormData({
                    name: "",
                    endpoint: "",
                    api_key: "", // Backend expects snake_case
                    metadata: "",
                    strategy_id: "" // Backend expects snake_case
                  });
                }}
              >
                Create New Agent
              </StyledButton>
            </div>
          </div>
          
          {/* Form or List */}
          <div className="space-y-6">
            {(isCreating || isEditing) ? renderForm() : renderAgentList()}
          </div>
        </StyledBox>
      </Box>
    </div>
  );
};

import { mastra } from "../mastra/index";

// Get the workflow
const contest = mastra.getWorkflow("contest");
const { runId, start } = contest.createRun();

// Start the workflow execution
await start({
  triggerData: {
    arena: {
      id: "arena",
      name: "Arena",
      instructions: "",
      model: "openai:gpt-3.5-turbo",
      personality: "",
    },
    judge: {
      id: "judge",
      name: "Judge",
      instructions: "",
      model: "openai:gpt-3.5-turbo",
      personality: "",
    },
    players: [
      {
        id: "tester1",
        name: "Testy McGee",
        instructions: "",
        model: "openai:gpt-3.5-turbo",
        personality: "ready to be creative and help test",
      },
    ],
    arenaDescription: "A square arena with a red ball and a hoop",
    maxFeatures: 5,
    rules: [
      "The ball must be thrown into the hoop",
      "maximum distance to throw is 2 squares away",
    ],
  },
});

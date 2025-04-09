import { mastra } from "../mastra/index";

// Get the workflow
const contest = mastra.getWorkflow("contest");
const { runId, start } = contest.createRun();

const GEMINI_MODEL = "openrouter:google/gemini-2.5-pro-exp-03-25:free";
const LLAMA_MODEL = "openrouter:meta-llama/llama-4-maverick:free";
const QUASAR_MODEL = "openrouter:openrouter/quasar-alpha";

// Start the workflow execution
const result = await start({
  triggerData: {
    arena: {
      id: "arena",
      name: "Arena",
      instructions: "",
      model: QUASAR_MODEL,
      personality: "",
    },
    arenaHeight: 10,
    arenaWidth: 10,
    judge: {
      id: "judge",
      name: "Judge",
      instructions: "",
      model: "openrouter:meta-llama/llama-4-maverick:free",
      personality: "",
    },
    players: [
      {
        id: "tester1",
        name: "Testy McGee",
        instructions: "",
        model: "openrouter:openrouter/quasar-alpha",
        personality: "ready to be creative and help test",
      },
    ],
    arenaDescription: "A square arena with a red ball and a hoop",
    maxFeatures: 5,
    requiredFeatures: [
      {
        name: "red ball",
        position: { x: 1, y: 1 },
      },
      {
        name: "hoop",
        position: { x: 10, y: 8 },
      },
    ],
    rules: [
      "The ball must be thrown into the hoop",
      "maximum distance to throw is 2 squares away",
    ],
    roundHistory: [],
  },
});
console.log("result");
console.log(JSON.stringify(result, null, 2));

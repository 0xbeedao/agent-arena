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
    arena: "arena",
    arenaHeight: 10,
    arenaWidth: 10,
    judge: "judge",
    players: ["player1", "player2"],
    rules: "The ball must be thrown into the hoop, maximum distance to throw is 2 squares away",
  },
});
console.log("result");
console.log(JSON.stringify(result, null, 2));

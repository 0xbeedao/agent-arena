import { mastra } from "../mastra/index";

// Get the workflow
const contest = mastra.getWorkflow("contest");
const { runId, start } = contest.createRun();

// Start the workflow execution
try {
  const result = await start({
    triggerData: {
      arena: "arena",
      arenaDescription: "A square arena",
      arenaHeight: 10,
      arenaWidth: 10,
      judge: "judge",
      maxFeatures: 5,
      players: ["player1", "player2"],
      rules: "The ball must be thrown into the hoop, maximum distance to throw is 2 squares away",
    },
  });
  console.log("result");
  console.log(JSON.stringify(result, null, 2));
} catch (e) {
  console.log('Error', e);
}

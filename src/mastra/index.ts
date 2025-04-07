import { Mastra } from "@mastra/core";
import { makeContestWorkflow } from "./workflows/contest";
import { mastraLogger } from "../logging";

export const mastra = new Mastra({
  workflows: {
    contest: makeContestWorkflow(),
  },
  logger: mastraLogger,
});

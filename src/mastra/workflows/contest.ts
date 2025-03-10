import { Workflow, Step } from "@mastra/core/workflows";
import { z } from "zod";
import { contestWorkflowSchema, contestWorkflowSetupSchema } from "../../types/schemas";
import type { Participant } from "../../types/types";

export function makeContestWorkflow(players: Participant[]) {
    return new Workflow({
        name: "Contest",
        triggerSchema: contestWorkflowSetupSchema,
    });
}

const describeArenaStep = new Step({
    id: 'describeArena',
    outputSchema: contestWorkflowSchema,
    execute: async ({ context }) => {
        // TODO: Implement
    },
  });

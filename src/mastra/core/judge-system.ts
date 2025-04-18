import type { ContestRound, JudgeResult, JudgeResultList, PlayerResult, Point, PlayerStatus } from "../../types/types.d";
import { JudgeResultListSchema, PlayerStatusSchema } from "../../types/schemas.d";
import { Agent } from "@mastra/core/agent";
import { arenaLogger, judgeLogger } from "../../logging";
import { parseResponse } from "../agents/util/parser";
import { z } from "zod";

export interface GenerateJudgementProps {
    judgeAgent: Agent;
    arenaDescription: string;
    extraInstructions: string;
    round: ContestRound;
}

export async function generateJudgement(
    props: GenerateJudgementProps
): Promise<JudgeResultList> {
    const { arenaDescription, extraInstructions, judgeAgent, round } = props;
    const prompt = [
        `This arena is "${arenaDescription}"`,
        `The arena notes are: ${extraInstructions}`,
        `The current objects and players on the grid are: ${JSON.stringify(round.positions)}`,
        `Players have submitted the following actions: ${JSON.stringify(round.actions)}`,
        `Players have the following statuses: ${JSON.stringify(round.status)}`,
        "Please judge the actions for each player and make any changes to their status",
        "These results will be used to update player statuses, and to generate a narrative for the next round",
        "Example results:",
        `[{playerId: "player1", result: "success, add a key to inventory", reason: "Moved right and found a key"},`,
        `{ playerId: "player2", result: "success with consequences", reason: "Moved right but triggered a trap" }]`,
        `return the results in json format: [{playerId: <playerId>, result: <result text>, reason: <reason text>}]`,
    ].join("\n");
    arenaLogger.debug("prompt: " + prompt);
    const response = await judgeAgent.generate(prompt, {
        output: JudgeResultListSchema,
    });
    arenaLogger.info("Judge response: " + JSON.stringify(response, null, 2));
    const judgeResults = response.object as JudgeResultList;
    return judgeResults;
}

export interface GenerateRoundUpdatesProps {
    judgeAgent: Agent;
    arenaDescription: string;
    judgeResults: JudgeResult[];
    round: ContestRound;
}

export async function generatePositionUpdates(
    props: GenerateRoundUpdatesProps
): Promise<{ [key: string]: Point }> {
    const { judgeAgent, arenaDescription, judgeResults, round } = props;

    const prompt = [
        `This arena is "${arenaDescription}"`,
        `Previously, the arena has objects and players at ${JSON.stringify(round.positions)}`,
        `The judge has returned the following results: ${JSON.stringify(judgeResults)}`,
        "Please generate the new positions for the players in the same JSON format as the original positions",
    ].join("\n");

    const response = await judgeAgent.generate(prompt, {
        output: z.record(z.string(), z.object({ x: z.number(), y: z.number() })),
    });
    const positionUpdates: Record<string, Point> = parseResponse(
        response,
        z.record(z.string(), z.object({ x: z.number(), y: z.number() }))
    );

    return positionUpdates;
}

export async function generatePlayerStatus(
    props: { agent: Agent; result: JudgeResult; playerStatus: PlayerStatus }
): Promise<PlayerResult> {
    const { agent, result, playerStatus } = props;
    const prompt = [
        `The judge has returned the following result: ${JSON.stringify(result)}`,
        `The player has the following status: ${JSON.stringify(playerStatus)}`,
        "Please generate an updated status for the player in the same format as the original status",
    ].join("\n");
    const response = await agent.generate(prompt, {
        output: PlayerStatusSchema,
    });
    const status = response.object as PlayerStatus;
    arenaLogger.info("generate status results: " + JSON.stringify(status, null, 2));
    return {
        status,
        ...result,
    };
}

export async function generatePlayerStatusUpdates(
    props: GenerateRoundUpdatesProps
): Promise<Record<string, PlayerStatus>> {
    const { judgeAgent, judgeResults, round } = props;
    const updatedStatuses: { [key: string]: PlayerStatus } = {};

    const generationPromises = judgeResults.map((result) => generatePlayerStatus({
        agent: judgeAgent,
        result,
        playerStatus: round.status[result.playerId],
    }));

    const playerResults = await Promise.all(generationPromises);

    for (const result of playerResults) {
        judgeLogger.info(`Processed ${JSON.stringify(result)}`);
        updatedStatuses[result.playerId] = result.status;
    }

    judgeLogger.info([
        "Received all player results:",
        JSON.stringify(playerResults, null, 2),
        "and returning:" +
        JSON.stringify(updatedStatuses, null, 2)].join("\n"));

    return updatedStatuses;
}

export interface GenerateNarrativeForJudgementProps {
    arenaAgent: Agent;
    arenaDescription: string;
    extraInstructions: string;
    judgeResults: JudgeResult[];
    round: ContestRound;
}

export async function generateNarrativeForJudgement(
    props: GenerateNarrativeForJudgementProps
): Promise<string> {
    const {
        arenaAgent,
        arenaDescription,
        extraInstructions,
        judgeResults,
        round,
    } = props;
    const prompt = [
        `This previous round arena description is"${arenaDescription}"`,
        `The arena notes are: ${extraInstructions}`,
        `The objects and players are positioned: ${JSON.stringify(round.positions)}`,
        `Players have submitted the following actions: ${JSON.stringify(round.actions)}`,
        `The judge has returned the following results: ${JSON.stringify(judgeResults)}`,
        "Please generate a narrative to give to the players in the next round, summarizing the results of the previous round in a contest announcer style",
    ].join("\n");
    arenaLogger.debug("prompt: " + prompt);
    const response = await arenaAgent.generate(prompt, {
        output: z.string(),
    });
    const narrative: string = parseResponse(response);
    arenaLogger.info("Narrative: " + narrative);
    return narrative;
}
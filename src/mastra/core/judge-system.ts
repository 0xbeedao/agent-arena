/**
 * @module JudgeSystem
 * @description This module contains functions for judging player actions and generating round updates in the arena.
 *
 * @mermaid
 * graph LR
 *  subgraph Judge System
 *      GenerateJudgement(generateJudgement) --> JudgeAgent(Judge Agent)
 *      JudgeAgent --> JudgeResultList
 *      JudgeResultList --> GeneratePositionUpdates(generatePositionUpdates)
 *      JudgeResultList --> GeneratePlayerStatusUpdates(generatePlayerStatusUpdates)
 *      GeneratePlayerStatusUpdates --> GeneratePlayerStatus(generatePlayerStatus)
 *      GeneratePlayerStatus --> PlayerAgent(Judge Agent)
 *      PlayerAgent --> PlayerResult
 *      JudgeResultList --> GenerateNarrativeForJudgement(generateNarrativeForJudgement)
 *      GenerateNarrativeForJudgement --> ArenaAgent(Arena Agent)
 *      ArenaAgent --> Narrative
 *  end
 */
import type { ContestRound, JudgeResult, JudgeResultList, PlayerResult, Point, PlayerStatus } from "../../types/types.d";
import { JudgeResultListSchema, PlayerStatusSchema } from "../../types/schemas.d";
import { Agent } from "@mastra/core/agent";
import { arenaLogger, judgeLogger } from "../../logging";
import { parseResponse } from "../agents/util/parser";
import { z } from "zod";

/**
 * @interface GenerateJudgementProps
 * @description Properties for the generateJudgement function.
 */
export interface GenerateJudgementProps {
    /**
     * @property judgeAgent - The agent responsible for judging player actions.
     * @type {Agent}
     */
    judgeAgent: Agent;
    /**
     * @property arenaDescription - A description of the arena.
     * @type {string}
     */
    arenaDescription: string;
    /**
     * @property extraInstructions - Extra instructions for the judge.
     * @type {string}
     */
    extraInstructions: string;
    /**
     * @property round - The current contest round.
     * @type {ContestRound}
     */
    round: ContestRound;
}

/**
 * @async
 * @function generateJudgement
 * @description Generates a judgement on player actions for a given round.
 * @param {GenerateJudgementProps} props - Properties for generating judgement.
 * @returns {Promise<JudgeResultList>} - A promise that resolves to a list of judge results.
 */
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

/**
 * @interface GenerateRoundUpdatesProps
 * @description Properties for functions that generate round updates.
 */
export interface GenerateRoundUpdatesProps {
    /**
     * @property judgeAgent - The agent responsible for judging player actions.
     * @type {Agent}
     */
    judgeAgent: Agent;
    /**
     * @property arenaDescription - A description of the arena.
     * @type {string}
     */
    arenaDescription: string;
    /**
     * @property judgeResults - Results from the judge for the current round.
     * @type {JudgeResult[]}
     */
    judgeResults: JudgeResult[];
    /**
     * @property round - The current contest round.
     * @type {ContestRound}
     */
    round: ContestRound;
}

/**
 * @async
 * @function generatePositionUpdates
 * @description Generates updates for player positions based on judge results.
 * @param {GenerateRoundUpdatesProps} props - Properties for generating position updates.
 * @returns {Promise<{[key: string]: Point}>} - A promise that resolves to a record of player IDs to points.
 */
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

/**
 * @async
 * @function generatePlayerStatus
 * @description Generates an updated player status based on a judge result.
 * @param {object} props - Properties for generating player status.
 * @param {Agent} props.agent - The agent responsible for generating player status.
 * @param {JudgeResult} props.result - The judge result for the player.
 * @param {PlayerStatus} props.playerStatus - The current status of the player.
 * @returns {Promise<PlayerResult>} - A promise that resolves to a player result.
 */
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

/**
 * @async
 * @function generatePlayerStatusUpdates
 * @description Generates status updates for all players based on judge results.
 * @param {GenerateRoundUpdatesProps} props - Properties for generating player status updates.
 * @returns {Promise<Record<string, PlayerStatus>>} - A promise that resolves to a record of player IDs to player statuses.
 */
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

/**
 * @interface GenerateNarrativeForJudgementProps
 * @description Properties for the generateNarrativeForJudgement function.
 */
export interface GenerateNarrativeForJudgementProps {
    /**
     * @property arenaAgent - The agent responsible for generating the narrative.
     * @type {Agent}
     */
    arenaAgent: Agent;
    /**
     * @property arenaDescription - A description of the arena.
     * @type {string}
     */
    arenaDescription: string;
    /**
     * @property extraInstructions - Extra instructions for the narrative generation.
     * @type {string}
     */
    extraInstructions: string;
    /**
     * @property judgeResults - Results from the judge for the current round.
     * @type {JudgeResult[]}
     */
    judgeResults: JudgeResult[];
    /**
     * @property round - The current contest round.
     * @type {ContestRound}
     */
    round: ContestRound;
}

/**
 * @async
 * @function generateNarrativeForJudgement
 * @description Generates a narrative for the judgement of a round.
 * @param {GenerateNarrativeForJudgementProps} props - Properties for generating the narrative.
 * @returns {Promise<string>} - A promise that resolves to a narrative string.
 */
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
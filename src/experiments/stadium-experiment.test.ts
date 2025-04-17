// This file is used to test the stadium usage with live models

import { describe, it, expect, vi } from "vitest";
import { Agent } from "@mastra/core/agent";
import { A, D, pipe, S } from "@mobily/ts-belt";
import {
  generateFeatures,
  generateGrid,
  generateJudgement,
} from "../mastra/agents/util/stadium";
import { getLanguageModel } from "../config";
import type {
  ContestRound,
  PlayerAction,
  PlayerStatus,
} from "../types/types.d";

const MODELS_UNDER_TEST = ["gpt4o"];

describe("Stadium Usage tests with live models", () => {
  MODELS_UNDER_TEST.forEach((model) => {
    describe(`generateFeatures with ${model}`, async () => {
      it("should generate a single feature", async () => {
        const agent = new Agent({
          name: "player",
          instructions: "You are a player in a game",
          model: getLanguageModel(model),
        });

        const features = await generateFeatures(
          agent,
          "A square arena",
          10,
          10,
          1
        );
        expect(features.length).toBe(1);
        expect(features[0].name).toBeDefined();
        expect(features[0].position).toBeDefined();
      });

      it("should generate multiple features", async () => {
        const agent = new Agent({
          name: "player",
          instructions: "You are a player in a game",
          model: getLanguageModel(model),
        });
        const features = await generateFeatures(
          agent,
          "A square arena",
          10,
          10,
          5
        );
        expect(features.length).toBeGreaterThan(0);
        // both names and positions should be unique
        expect(A.uniq(features.map((f) => f.name)).length).toBe(
          features.length
        );
        expect(A.uniq(features.map((f) => f.position)).length).toBe(
          features.length
        );
        // positions should be within the grid
        features.forEach((f) => {
          expect(f.position.x).toBeGreaterThanOrEqual(0);
          expect(f.position.x).toBeLessThanOrEqual(10);
          expect(f.position.y).toBeGreaterThanOrEqual(0);
          expect(f.position.y).toBeLessThanOrEqual(10);
        });
      });
    });
  });

  MODELS_UNDER_TEST.forEach((model) => {
    describe(`generateGrid with ${model}`, async () => {
      it("should generate a grid with a single required feature", async () => {
        // Create mock agent for testing without paying for OpenAI
        const agent = new Agent({
          name: "player",
          instructions: "You are a player in a game",
          model: getLanguageModel(model),
        });

        const grid = await generateGrid(
          10,
          10,
          0,
          [
            {
              name: "rock",
              position: { x: 2, y: 3 },
            },
          ],
          "A square arena with a rock",
          [],
          agent
        );

        expect(Object.keys(grid.features).length).toBe(1);
        expect(grid.features["2,3"]).toBe("rock");
      });

      // it("should generate a grid with a single required feature and at least one rainbow feature with gemini", async () => {
      //   const agent = new Agent({
      //     name: "player",
      //     instructions:
      //       "You are setting up a game, please generate a grid with a rock and a rainbow",
      //     model: getLanguageModel(model),
      //   });

      //   const grid = await generateGrid(
      //     10,
      //     10,
      //     4,
      //     [
      //       {
      //         name: "rock",
      //         position: { x: 6, y: 6 },
      //       },
      //     ],
      //     "A square arena with a rock",
      //     [],
      //     agent
      //   );

      //   expect(Object.keys(grid.features).length).toBeGreaterThan(1);

      //   expect(grid.features["6,6"]).toBe("rock");

      //   const hasRainbow = pipe(
      //     grid.features,
      //     D.values,
      //     A.some((value) => S.includes("rainbow", value))
      //   );

      //   expect(hasRainbow).toBe(true);
      // });
    });
  });

  describe("generateJudgement", () => {
    MODELS_UNDER_TEST.forEach((model) => {
      describe(`generateJudgement with ${model}`, async () => {
        it("should generate valid judge results for player actions", async () => {
          const agent = new Agent({
            name: "judge",
            instructions:
              "You are a judge in a game, evaluating player actions",
            model: getLanguageModel(model),
          });

          // Create test round data
          const round: ContestRound = {
            grid: {
              height: 10,
              width: 10,
              playerPositions: {
                player1: { x: 2, y: 1 },
                player2: { x: 5, y: 6 },
              },
              features: {
                "2,1": "player1",
                "5,6": "player2",
                "3,3": "rock",
              } as Record<string, string>,
            },
            actions: {
              player1: {
                action: "move",
                target: { x: 3, y: 1 },
                narration: "I move to the right to explore",
              },
              player2: {
                action: "move",
                target: { x: 6, y: 6 },
                narration: "I move to the right cautiously",
              },
            } as Record<string, PlayerAction>,
            arenaDescription: "A dangerous arena with traps and treasures",
            status: {
              player1: {
                status: "ok",
                health: 100,
                inventory: [],
              },
              player2: {
                status: "ok",
                health: 100,
                inventory: [],
              },
            } as Record<string, PlayerStatus>,
          };

          const judgeResponse = await generateJudgement({
            judgeAgent: agent,
            arenaDescription: "A dangerous arena with traps and treasures",
            extraInstructions: "Beware of hidden traps",
            round,
          });

          // Verify the structure of the response
          expect(judgeResponse.results).toBeDefined();
          expect(Array.isArray(judgeResponse.results)).toBe(true);
          expect(judgeResponse.results.length).toBe(2);

          // Verify each player result has required fields
          judgeResponse.results.forEach((result) => {
            expect(result.playerId).toBeDefined();
            expect(result.status).toBeDefined();
            expect(result.status.status).toBeDefined();
            expect(result.status.health).toBeDefined();
            expect(result.status.inventory).toBeDefined();
            expect(result.position).toBeDefined(); // position is at top level
            expect(result.position.x).toBeDefined();
            expect(result.position.y).toBeDefined();
            expect(result.result).toBeDefined();
            expect(result.reason).toBeDefined();
          });

          // Verify grid is returned
          expect(judgeResponse.grid).toBeDefined();
          expect(judgeResponse.grid.height).toBe(10);
          expect(judgeResponse.grid.width).toBe(10);
          expect(judgeResponse.grid.playerPositions).toBeDefined();
          expect(judgeResponse.grid.features).toBeDefined();

          // Verify arena description is returned
          expect(judgeResponse.arenaDescription).toBeDefined();
        }, 10000);
      });
    });
  });
});

// This file is used to test the stadium usage with live models

import { describe, it, expect, vi } from "vitest";
import { Agent } from "@mastra/core/agent";
import { google } from "@ai-sdk/google";
import { A, D, pipe, S } from "@mobily/ts-belt";
import { generateFeatures, generateGrid } from "../mastra/agents/util/stadium";

describe("Stadium Usage tests with live models", () => {
  describe("generateFeatures", async () => {
    it("should generate a single feature", async () => {
      const agent = new Agent({
        name: "player",
        instructions: "You are a player in a game",
        model: google("gemini-2.0-flash-lite"),
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
        model: google("gemini-2.0-flash-lite"),
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
      expect(A.uniq(features.map((f) => f.name)).length).toBe(features.length);
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

  describe("generateGrid", async () => {
    it("should generate a grid with a single required feature", async () => {
      // Create mock agent for testing without paying for OpenAI
      const agent = new Agent({
        name: "player",
        instructions: "You are a player in a game",
        model: google("gemini-2.0-flash-lite"),
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

    it("should generate a grid with a single required feature and at least one rainbow feature", async () => {
      const agent = new Agent({
        name: "player",
        instructions:
          "You are setting up a game, please generate a grid with a rock and a rainbow",
        model: google("gemini-2.0-flash-lite"),
      });

      const grid = await generateGrid(
        10,
        10,
        4,
        [
          {
            name: "rock",
            position: { x: 6, y: 6 },
          },
        ],
        "A square arena with a rock",
        [],
        agent
      );

      expect(Object.keys(grid.features).length).toBeGreaterThan(1);

      expect(grid.features["6,6"]).toBe("rock");

      const hasRainbow = pipe(
        grid.features,
        D.values,
        A.some((value) => S.includes("rainbow", value))
      );

      expect(hasRainbow).toBe(true);
    });
  });
});

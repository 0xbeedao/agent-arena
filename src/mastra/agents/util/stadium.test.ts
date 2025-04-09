import { addFeature, generateFeatures, generateGrid } from "./stadium";
import { describe, it, expect } from "vitest";
import { Agent } from "@mastra/core/agent";
import { google } from "@ai-sdk/google";
import { D, A, S, pipe } from "@mobily/ts-belt";

describe("addFeature", () => {
  it("should add a single point feature to the map", () => {
    const featureMap: { [key: string]: string } = {};
    const feature = {
      name: "rock",
      position: { x: 2, y: 3 },
    };

    addFeature(featureMap, feature);

    expect(Object.keys(featureMap).length).toBe(1);
    expect(featureMap["2,3"]).toBe("rock");
  });

  it("should add a line feature between two points", () => {
    const featureMap: { [key: string]: string } = {};
    const feature = {
      name: "wall",
      position: { x: 0, y: 0 },
      endPosition: { x: 2, y: 0 },
    };

    addFeature(featureMap, feature);

    // Should create 3 points (0,0), (1,0), (2,0)
    expect(Object.keys(featureMap).length).toBe(3);
    expect(featureMap["0,0"]).toBe("wall");
    expect(featureMap["1,0"]).toBe("wall");
    expect(featureMap["2,0"]).toBe("wall");
  });

  it("should add a diagonal line feature", () => {
    const featureMap: { [key: string]: string } = {};
    const feature = {
      name: "fence",
      position: { x: 0, y: 0 },
      endPosition: { x: 2, y: 2 },
    };

    addFeature(featureMap, feature);

    // Should create 3 points (0,0), (1,1), (2,2)
    expect(Object.keys(featureMap).length).toBe(3);
    expect(featureMap["0,0"]).toBe("fence");
    expect(featureMap["1,1"]).toBe("fence");
    expect(featureMap["2,2"]).toBe("fence");
  });

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
      // Create the AgentWrapper and set up mocked responses
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

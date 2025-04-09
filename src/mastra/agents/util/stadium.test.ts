import { addFeature, generateGrid } from "./stadium";
import { describe, it, expect } from "vitest";
import { Agent } from "@mastra/core/agent";
import { openai } from "@ai-sdk/openai";
import { AgentWrapper } from "./agentwrapper";

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
      end_position: { x: 2, y: 0 },
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
      end_position: { x: 2, y: 2 },
    };

    addFeature(featureMap, feature);

    // Should create 3 points (0,0), (1,1), (2,2)
    expect(Object.keys(featureMap).length).toBe(3);
    expect(featureMap["0,0"]).toBe("fence");
    expect(featureMap["1,1"]).toBe("fence");
    expect(featureMap["2,2"]).toBe("fence");
  });

  describe("generateGrid", async () => {
    it("should generate a grid with a single required feature", async () => {
      const agent = new Agent({
        name: "player",
        instructions: "You are a player in a game",
        model: openai("gpt-3.5-turbo"),
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

    it("should generate a grid with a single required feature and a single optional feature", async () => {
      const object = [
        {
          name: "a brilliant rainbow",
          position: { x: 2, y: 3 },
        },
      ];
      const agent = new Agent({
        name: "player",
        instructions: "You are a player in a game",
        model: openai("gpt-3.5-turbo"),
      });

      const agentWrapper = new AgentWrapper(agent, true, [
        JSON.stringify(object),
      ]);

      const grid = await generateGrid(
        10,
        10,
        1,
        [
          {
            name: "rock",
            position: { x: 6, y: 6 },
          },
        ],
        "A square arena with a rock",
        [],
        agentWrapper
      );
      expect(Object.keys(grid.features).length).toBe(2);
      expect(grid.features["6,6"]).toBe("rock");
      expect(grid.features["2,3"]).toBe("a brilliant rainbow");
    });
  });
});

import {
  addFeature,
  generateFeatures,
  generateGrid,
  updateGridFromJudgeResults,
  generateNarrativeFromResults,
  generateJudgement,
} from "./stadium";
import { describe, it, expect, vi } from "vitest";
import { Agent } from "@mastra/core/agent";
import { google } from "@ai-sdk/google";
import { D, A, S, pipe } from "@mobily/ts-belt";
import type {
  ContestRound,
  PlayerAction,
  PlayerStatus,
} from "../../../types/types.d";
import { AgentCache } from "./agentcache";

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
});

describe("generateFeatures", async () => {
  it("should generate a single feature", async () => {
    const mockFeatures = [
      {
        name: "rock",
        position: { x: 2, y: 3 },
      },
    ];
    const mockAgent = {
      generate: vi.fn().mockResolvedValue({
        text: JSON.stringify(mockFeatures),
      }),
    } as unknown as Agent;

    const features = await generateFeatures(
      mockAgent,
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
    const mockFeatures = [
      {
        name: "rock",
        position: { x: 2, y: 3 },
      },
      {
        name: "tree",
        position: { x: 4, y: 5 },
      },
    ];
    const mockAgent = {
      generate: vi.fn().mockResolvedValue({
        text: JSON.stringify(mockFeatures),
      }),
    } as unknown as Agent;

    const features = await generateFeatures(
      mockAgent,
      "A square arena",
      10,
      10,
      5
    );
    expect(features.length).toBeGreaterThan(0);
    expect(A.uniq(features.map((f) => f.name)).length).toBe(features.length);
    expect(A.uniq(features.map((f) => f.position)).length).toBe(
      features.length
    );
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
    const mockGrid = {
      features: {
        "2,3": "rock",
      },
    };
    const mockAgent = {
      generate: vi.fn().mockResolvedValue({
        text: JSON.stringify(mockGrid),
      }),
    } as unknown as Agent;

    const grid = await generateGrid(
      10,
      10,
      0,
      [{ name: "rock", position: { x: 2, y: 3 } }],
      "A square arena with a rock",
      [],
      mockAgent
    );
    expect(Object.keys(grid.features).length).toBe(1);
    expect(grid.features["2,3"]).toBe("rock");
  });

  it("should generate a grid with a single required feature and at least one rainbow feature", async () => {
    const mockFeaturesResponse = [
      {
        name: "rainbow",
        position: { x: 7, y: 7 },
      },
    ];
    const mockAgent = {
      generate: vi.fn().mockResolvedValue({
        text: JSON.stringify(mockFeaturesResponse),
      }),
    } as unknown as Agent;

    const grid = await generateGrid(
      10,
      10,
      4,
      [{ name: "rock", position: { x: 6, y: 6 } }],
      "A square arena with a rock",
      [],
      mockAgent
    );
    expect(Object.keys(grid.features).length).toBeGreaterThan(1);
    expect(grid.features["6,6"]).toBe("rock");
    expect(grid.features["7,7"]).toBe("rainbow");
  });
});

describe("generateNarrativeFromResults", () => {
  it("should generate a narrative based on judge results", async () => {
    // Create mock agent that returns a predefined narrative
    const mockNarrative =
      "Round 1 summary: Player1 moved right and collected a key! Player2 was hit by a trap and lost health.";
    const mockAgent = {
      generate: vi.fn().mockResolvedValue({
        text: mockNarrative,
      }),
    } as unknown as Agent;

    // Create mock round data
    const round: ContestRound = {
      grid: {
        height: 10,
        width: 10,
        players: {
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
          inventory: ["key"],
        },
        player2: {
          status: "ok",
          health: 100,
          inventory: [],
        },
      } as Record<string, PlayerStatus>,
    };
    // Create mock judge results
    const judgeResults = [
      {
        playerId: "player1",
        status: {
          status: "ok",
          health: 100,
          inventory: ["key"],
          position: { x: 3, y: 1 },
        },
        result: "success",
        reason: "Moved right and found a key",
      },
      {
        playerId: "player2",
        status: {
          status: "injured",
          health: 80,
          inventory: [],
          position: { x: 6, y: 6 },
        },
        result: "success with consequences",
        reason: "Moved right but triggered a trap",
      },
    ];

    // Call the function with test data
    const narrative = await generateNarrativeFromResults({
      agent: mockAgent,
      arenaDescription: "A dangerous arena with traps and treasures",
      extraInstructions: "Beware of hidden traps",
      judgeResults,
      round: round as ContestRound,
    });

    // Verify the result
    expect(narrative).toBe(mockNarrative);

    // Verify that agent.generate was called with the expected prompt
    expect(mockAgent.generate).toHaveBeenCalledTimes(1);
    expect(mockAgent.generate).toHaveBeenCalledWith(
      expect.stringContaining("A dangerous arena with traps and treasures"),
      { output: expect.any(Object) }
    );

    // Check that the prompt includes all the necessary information
    const generateCall = (mockAgent.generate as ReturnType<typeof vi.fn>).mock
      .calls[0][0] as string;
    expect(generateCall).toContain("Beware of hidden traps");
    expect(generateCall).toContain(JSON.stringify(round.grid));
    expect(generateCall).toContain(JSON.stringify(round.actions));
    expect(generateCall).toContain(JSON.stringify(judgeResults));
  });
});

describe("updateGridFromJudgeResults", () => {
  it("should update player positions and features in the grid", () => {
    // Set up initial grid with players
    const grid = {
      height: 10,
      width: 10,
      players: {
        player1: { x: 1, y: 1 },
        player2: { x: 5, y: 5 },
      },
      features: {
        "1,1": "player1",
        "5,5": "player2",
        "3,3": "rock",
      } as Record<string, string>,
    };

    // Create judge results that move players to new positions
    const judgeResults = [
      {
        playerId: "player1",
        status: {
          status: "ok",
          health: 100,
          inventory: [],
          position: { x: 2, y: 1 },
        },
        result: "success",
        reason: "Moved right",
      },
      {
        playerId: "player2",
        status: {
          status: "ok",
          health: 100,
          inventory: [],
          position: { x: 5, y: 6 },
        },
        result: "success",
        reason: "Moved down",
      },
    ];

    // Update the grid
    updateGridFromJudgeResults(judgeResults, grid);

    // Check that player positions were updated
    expect(grid.players["player1"]).toEqual({ x: 2, y: 1 });
    expect(grid.players["player2"]).toEqual({ x: 5, y: 6 });

    // Check that features were updated
    expect(grid.features["1,1"]).toBe(""); // Old position cleared
    expect(grid.features["5,5"]).toBe(""); // Old position cleared
    expect(grid.features["2,1"]).toBe("player1"); // New position has player1
    expect(grid.features["5,6"]).toBe("player2"); // New position has player2
    expect(grid.features["3,3"]).toBe("rock"); // Other features remain unchanged
  });

  it("should handle multiple moves for the same player", () => {
    // Set up initial grid with one player
    const grid = {
      height: 10,
      width: 10,
      players: {
        player1: { x: 1, y: 1 },
      },
      features: {
        "1,1": "player1",
        "3,3": "rock",
      } as Record<string, string>,
    };

    // Create judge results with multiple entries for the same player
    // (simulating a bug or multiple rounds being processed at once)
    const judgeResults = [
      {
        playerId: "player1",
        status: {
          status: "ok",
          health: 100,
          inventory: [],
          position: { x: 2, y: 1 },
        },
        result: "success",
        reason: "First move",
      },
      {
        playerId: "player1",
        status: {
          status: "ok",
          health: 90,
          inventory: ["key"],
          position: { x: 3, y: 1 },
        },
        result: "success",
        reason: "Second move",
      },
    ];

    // Update the grid
    updateGridFromJudgeResults(judgeResults, grid);

    // Check that the final position is the last one in the results
    expect(grid.players["player1"]).toEqual({ x: 3, y: 1 });

    // Check that features were updated correctly
    expect(grid.features["1,1"]).toBe(""); // Initial position cleared
    expect(grid.features["2,1"]).toBe(""); // Intermediate position cleared
    expect(grid.features["3,1"]).toBe("player1"); // Final position has player
    expect(grid.features["3,3"]).toBe("rock"); // Other features remain unchanged
  });
});

describe("generateJudgement", () => {
  it("should generate a judge response based on player actions", async () => {
    // Create mock agent that returns a predefined judge response
    const mockJudgeResponse = {
      object: [
        {
          playerId: "player1",
          status: {
            status: "ok",
            health: 100,
            inventory: ["key"],
            position: { x: 3, y: 1 },
          },
          result: "success",
          reason: "Moved right and found a key",
        },
        {
          playerId: "player2",
          status: {
            status: "injured",
            health: 80,
            inventory: [],
            position: { x: 6, y: 6 },
          },
          result: "success with consequences",
          reason: "Moved right but triggered a trap",
        },
      ],
    };

    const mockNarrative =
      "Round 1 summary: Player1 moved right and collected a key! Player2 was hit by a trap and lost health.";

    const mockJudge = {
      generate: vi
        .fn()
        .mockResolvedValueOnce(mockJudgeResponse)
        .mockResolvedValueOnce({ text: mockNarrative }),
    } as unknown as Agent;

    // Create mock agent cache
    const mockAgentCache = {
      getAgent: vi.fn().mockReturnValue(mockJudge),
    } as unknown as AgentCache;

    // Create mock round data
    const round: ContestRound = {
      grid: {
        height: 10,
        width: 10,
        players: {
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
          inventory: ["key"],
        },
        player2: {
          status: "ok",
          health: 100,
          inventory: [],
        },
      } as Record<string, PlayerStatus>,
    };

    // Call the function with test data
    const judgeResponse = await generateJudgement({
      agentCache: mockAgentCache,
      arenaDescription: "A dangerous arena with traps and treasures",
      extraInstructions: "Beware of hidden traps",
      round,
    });

    // Verify the result
    expect(judgeResponse.results).toEqual(mockJudgeResponse.object);
    expect(judgeResponse.grid).toEqual(round.grid);
    expect(judgeResponse.arenaDescription).toBeDefined();

    // Verify that agent.generate was called with the expected prompt
    expect(mockJudge.generate).toHaveBeenCalledTimes(2);
    expect(mockJudge.generate).toHaveBeenCalledWith(
      expect.stringContaining("A dangerous arena with traps and treasures"),
      { output: expect.any(Object) }
    );

    // Check that the prompt includes all the necessary information
    const generateCall = (mockJudge.generate as ReturnType<typeof vi.fn>).mock
      .calls[0][0] as string;
    expect(generateCall).toContain("Beware of hidden traps");
    expect(generateCall).toContain(
      JSON.stringify(round.grid.players["player1"])
    );
    const generateCall2 = (mockJudge.generate as ReturnType<typeof vi.fn>).mock
      .calls[1][0] as string;
    expect(generateCall2).toContain("right");
  });
});

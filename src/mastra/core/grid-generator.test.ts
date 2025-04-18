import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  addFeature,
  addFeatures,
  generateFeatures,
  generateGrid,
  randomPosition,
} from "./grid-generator";
import type { Point, GridFeature, ContestRound, Participant } from "../../types/types.d";

const mockPlayer1: Participant = { id: "p1", name: "player1", model: "test", personality: "test-p1" };
const mockPlayer2: Participant = { id: "p2", name: "player2", model: "test", personality: "test-p2" };

describe("Grid Generator Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("addFeature", () => {
    it("should add a single point feature to the map", () => {
      const featureMap: { [key: string]: Point } = {};
      const feature = {
        name: "rock",
        position: { x: 2, y: 3 },
      };

      addFeature(featureMap, feature);

      expect(Object.keys(featureMap).length).toBe(1);
      expect(featureMap["feature:rock"]).toEqual({x: 2, y: 3});
    });

    it("should add a line feature between two points", () => {
      const featureMap: { [key: string]: Point } = {};
      const feature = {
        name: "wall",
        position: { x: 0, y: 0 },
        endPosition: { x: 2, y: 0 },
      };

      addFeature(featureMap, feature);

      expect(Object.keys(featureMap).length).toBe(3);
      expect(featureMap["feature:wall.0"]).toEqual({x:0, y: 0});
      expect(featureMap["feature:wall.1"]).toEqual({x:1, y: 0});
      expect(featureMap["feature:wall.2"]).toEqual({x:2, y: 0});
    });

    it("should add a diagonal line feature", () => {
      const featureMap: { [key: string]: Point } = {};
      const feature = {
        name: "fence",
        position: { x: 0, y: 0 },
        endPosition: { x: 2, y: 2 },
      };

      addFeature(featureMap, feature);

      expect(Object.keys(featureMap).length).toBe(3);
      expect(featureMap["feature:fence.0"]).toEqual({x: 0, y: 0});
      expect(featureMap["feature:fence.1"]).toEqual({x: 1, y: 1});
      expect(featureMap["feature:fence.2"]).toEqual({x: 2, y: 2});      
    });
  });

  describe("addFeatures", () => {
    it("should add multiple features to the map", () => {
      const featureMap: { [key: string]: Point } = {};
      const features: GridFeature[] = [
        { name: "rock", position: { x: 1, y: 1 } },
        { name: "tree", position: { x: 3, y: 4 } },
        {
          name: "wall",
          position: { x: 0, y: 0 },
          endPosition: { x: 2, y: 0 },
        },
      ];

      addFeatures(featureMap, features);

      expect(Object.keys(featureMap).length).toBe(5);
      expect(featureMap["feature:rock"]).toEqual({x: 1, y: 1});
      expect(featureMap["feature:tree"]).toEqual({x: 3, y: 4});
      expect(featureMap["feature:wall.0"]).toEqual({x: 0, y: 0});
      expect(featureMap["feature:wall.1"]).toEqual({x: 1, y: 0});
      expect(featureMap["feature:wall.2"]).toEqual({x: 2, y: 0});
    });

    it("should handle an empty features array", () => {
      const featureMap: { [key: string]: Point } = { existing: {x: 5, y: 5} };
      const features: GridFeature[] = [];

      addFeatures(featureMap, features);

      expect(Object.keys(featureMap).length).toBe(1);
      expect(featureMap["existing"]).toEqual({x: 5, y: 5});
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
      const localMockAgent = {
        generate: vi.fn().mockResolvedValue({
          object: mockFeatures,
        }),
      } as unknown as any;

      const features = await generateFeatures(
        localMockAgent,
        "A square arena",
        10,
        10,
        1
      );
      expect(features.length).toBe(1);
      expect(features[0].name).toBeDefined();
      expect(features[0].position).toBeDefined();
      expect(localMockAgent.generate).toHaveBeenCalledTimes(1);
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
      const localMockAgent = {
        generate: vi.fn().mockResolvedValue({
          object: mockFeatures,
        }),
      } as unknown as any;

      const features = await generateFeatures(
        localMockAgent,
        "A square arena",
        10,
        10,
        5
      );
      expect(features.length).toBeGreaterThan(0);
      features.forEach((f: GridFeature) => {
        expect(f.position.x).toBeGreaterThanOrEqual(0);
        expect(f.position.y).toBeGreaterThanOrEqual(0);
      });
      expect(localMockAgent.generate).toHaveBeenCalledTimes(1);
    });
  });

  describe("generateGrid", async () => {
    it("should generate a grid with only the required feature when maxFeatures is 0", async () => {
      const grid = await generateGrid(
        10,
        10,
        0,
        [{ name: "rock", position: { x: 2, y: 3 } }],
        "A square arena with a rock",
        [],
        null as unknown as any
      );
      expect(Object.keys(grid.features).length).toBe(1);
      expect(grid.features["feature:rock"]).toEqual({x: 2, y: 3});
    });

    it("should generate a grid calling generateFeatures for random features and place players", async () => {
      const mockFeaturesResponse = [
        {
          name: "rainbow",
          position: { x: 7, y: 7 },
        },
      ];
      const localMockAgent = {
        generate: vi.fn().mockResolvedValue({
          object: mockFeaturesResponse,
        }),
      } as unknown as any;

      const randomSpy = vi.spyOn(Math, "random");
      randomSpy.mockReturnValueOnce(0.01).mockReturnValueOnce(0.02);
      randomSpy.mockReturnValueOnce(0.03).mockReturnValueOnce(0.11);

      const grid = await generateGrid(
        10,
        10,
        2,
        [{ name: "rock", position: { x: 6, y: 6 } }],
        "A square arena with a rock",
        [mockPlayer1, mockPlayer2],
        localMockAgent
      );

      expect(Object.keys(grid.features).length).toBe(4);
      expect(grid.features["feature:rock"]).toEqual({x:6, y: 6});
      expect(grid.features["feature:rainbow"]).toEqual({x: 7, y: 7});
      expect(grid.features[`player:${mockPlayer1.name}`]).toEqual({x: 0, y: 0});
      expect(grid.features[`player:${mockPlayer2.name}`]).toEqual({x: 0, y: 1});
      expect(localMockAgent.generate).toHaveBeenCalledTimes(1);

      randomSpy.mockRestore();
    });
  });

  describe("randomPosition", () => {
    it("should return a position within bounds", () => {
      const height = 5;
      const width = 5;
      const features = {};
      const pos = randomPosition(height, width, features);

      expect(pos.x).toBeGreaterThanOrEqual(0);
      expect(pos.x).toBeLessThan(width);
      expect(pos.y).toBeGreaterThanOrEqual(0);
      expect(pos.y).toBeLessThan(height);
    });

    it("should avoid existing feature positions", () => {
      const height = 2;
      const width = 1;
      const features = {
        "TEST": {x: 0, y: 0}
      };
      const randomSpy = vi.spyOn(Math, "random");
      randomSpy.mockReturnValueOnce(0).mockReturnValueOnce(0);
      randomSpy.mockReturnValueOnce(0).mockReturnValueOnce(0.6);

      const pos = randomPosition(height, width, features);

      expect(pos).toEqual({ x: 0, y: 1 });
      expect(randomSpy).toHaveBeenCalledTimes(4);

      randomSpy.mockRestore();
    });
  });

  describe("updateGridFromPlayerPositions", () => {
    it("should update player positions and features in the grid based on new positions", () => {
      // TODO
    });
  });
});
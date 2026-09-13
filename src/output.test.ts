import { describe, expect, test } from "bun:test";
import * as fs from "node:fs";
import * as path from "node:path";
import * as os from "node:os";
import { resolveCandidateOutput } from "./output.ts";

describe("candidate-only renderer output", () => {
  test("refuses historical, arbitrary, symlinked and registered release outputs", () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "colorbench-output-"));
    try {
      fs.mkdirSync(path.join(root, "dataset"));
      const candidate = path.join(root, "dataset/candidate-rendered");
      expect(resolveCandidateOutput(undefined, root)).toBe(candidate);
      for (const name of [
        "dataset/rendered",
        "dataset/colorbench-1",
        "dataset/frozen",
        ".",
        "dataset",
      ]) {
        expect(() => resolveCandidateOutput(name, root)).toThrow();
      }
      const frozen = path.join(root, "dataset/frozen");
      fs.mkdirSync(frozen);
      fs.writeFileSync(path.join(frozen, "sentinel"), "preserve");
      fs.symlinkSync(frozen, candidate);
      expect(() => resolveCandidateOutput(undefined, root)).toThrow("symlink");
      fs.unlinkSync(candidate);
      fs.mkdirSync(path.join(root, "releases"));
      fs.writeFileSync(
        path.join(root, "releases/0.2.0.json"),
        JSON.stringify({
          dataset_path: "dataset/candidate-rendered",
          dataset_manifest: "dataset/candidate-rendered/manifest.json",
        }),
      );
      expect(() => resolveCandidateOutput(undefined, root)).toThrow("release");
      expect(fs.readFileSync(path.join(frozen, "sentinel"), "utf8")).toBe("preserve");
    } finally {
      fs.rmSync(root, { recursive: true, force: true });
    }
  });
});

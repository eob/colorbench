import * as fs from "node:fs";
import * as path from "node:path";

export const REPOSITORY = path.resolve(import.meta.dir, "..");
export function resolveCandidateOutput(requested?: string, repository = REPOSITORY): string {
  const candidate = path.resolve(repository, "dataset/candidate-rendered");
  const chosen = path.resolve(repository, requested ?? "dataset/candidate-rendered");
  if (chosen !== candidate)
    throw new Error(
      "Renderer writes only dataset/candidate-rendered; historical and arbitrary paths are protected",
    );
  for (let current = chosen; ; current = path.dirname(current)) {
    if (fs.lstatSync(current, { throwIfNoEntry: false })?.isSymbolicLink())
      throw new Error(`Refusing output through symlink: ${current}`);
    if (current === path.dirname(current)) break;
  }
  const releases = path.join(repository, "releases");
  if (fs.existsSync(releases))
    for (const file of fs.readdirSync(releases)) {
      if (!file.endsWith(".json")) continue;
      const descriptor = JSON.parse(fs.readFileSync(path.join(releases, file), "utf8"));
      const protectedPaths = [
        descriptor.dataset_path,
        typeof descriptor.dataset_manifest === "string"
          ? path.dirname(descriptor.dataset_manifest)
          : undefined,
      ];
      for (const value of protectedPaths) {
        if (typeof value !== "string") continue;
        const protectedPath = path.resolve(repository, value);
        if (
          chosen === protectedPath ||
          chosen.startsWith(protectedPath + path.sep) ||
          protectedPath.startsWith(chosen + path.sep)
        ) {
          throw new Error(`Refusing registered release output: ${file}`);
        }
        if (fs.existsSync(protectedPath) && fs.realpathSync(protectedPath) === chosen)
          throw new Error(`Refusing aliased release output: ${file}`);
      }
    }
  return chosen;
}

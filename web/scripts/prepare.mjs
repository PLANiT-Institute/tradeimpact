// Copies build inputs into the web app so the deployment is self-contained:
//   ../data/published  -> public/data      (SSG + client fetches)
//   ../ti-framework/ti_framework + ../api/compute.py -> api/_engine  (Python function)
import {
  cpSync,
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { createHash } from "node:crypto";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const web = dirname(dirname(fileURLToPath(import.meta.url)));
const repo = dirname(web);
const dataDst = join(web, "public", "data");
const engineDst = join(web, "api", "_engine");
const manifestPath = join(web, ".prepared-manifest.json");

function treeHash(root) {
  const digest = createHash("sha256");
  function visit(dir) {
    for (const name of readdirSync(dir).sort()) {
      const path = join(dir, name);
      const stat = statSync(path);
      if (stat.isDirectory()) visit(path);
      else {
        digest.update(path.slice(root.length + 1));
        digest.update("\0");
        digest.update(readFileSync(path));
        digest.update("\0");
      }
    }
  }
  visit(root);
  return digest.digest("hex");
}

function validatePackagedCopy() {
  if (!existsSync(dataDst) || !existsSync(engineDst) || !existsSync(manifestPath)) return false;
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const ageMs = Date.now() - Date.parse(manifest.preparedAt);
  if (!Number.isFinite(ageMs) || ageMs < 0 || ageMs > 2 * 60 * 60 * 1000) {
    throw new Error(
      "packaged deploy inputs are older than 2 hours; run `npm run package:deploy` immediately before `vercel`",
    );
  }
  const meta = JSON.parse(readFileSync(join(dataDst, "meta.json"), "utf8"));
  const actual = {
    dataSha256: treeHash(dataDst),
    engineSha256: treeHash(engineDst),
    datasetSha256: meta.dataset_sha256,
  };
  for (const [key, value] of Object.entries(actual)) {
    if (manifest[key] !== value) throw new Error(`packaged deploy ${key} mismatch`);
  }
  return true;
}

const published = join(repo, "data", "published");
if (!existsSync(published)) {
  // CLI deploys upload only web/. Accept a pre-packaged copy only when it is recent
  // and every byte still matches the local packaging manifest.
  if (validatePackagedCopy()) {
    console.log("prepare: verified recent packaged public/data + api/_engine");
    process.exit(0);
  }
  console.error(
    "repo sources and a verified packaged copy are absent — run `npm run package:deploy` before a CLI deploy",
  );
  process.exit(1);
}
rmSync(dataDst, { recursive: true, force: true });
mkdirSync(join(web, "public"), { recursive: true });
cpSync(published, dataDst, { recursive: true });

rmSync(engineDst, { recursive: true, force: true });
cpSync(join(repo, "ti-framework", "ti_framework"), join(engineDst, "ti_framework"), {
  recursive: true,
  filter: (src) => !src.includes("__pycache__"),
});
cpSync(join(repo, "api", "compute.py"), join(engineDst, "compute_service.py"));
const meta = JSON.parse(readFileSync(join(dataDst, "meta.json"), "utf8"));
writeFileSync(
  manifestPath,
  `${JSON.stringify(
    {
      format: 1,
      preparedAt: new Date().toISOString(),
      dataSha256: treeHash(dataDst),
      engineSha256: treeHash(engineDst),
      datasetSha256: meta.dataset_sha256,
    },
    null,
    2,
  )}\n`,
);
console.log("prepared: public/data + api/_engine");

// Copies build inputs into the web app so the deployment is self-contained:
//   ../data/published  -> public/data      (SSG + client fetches)
//   ../ti-framework/ti_framework + ../api/compute.py -> api/_engine  (Python function)
import { cpSync, mkdirSync, rmSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const web = dirname(dirname(fileURLToPath(import.meta.url)));
const repo = dirname(web);

const published = join(repo, "data", "published");
if (!existsSync(published)) {
  // CLI deploys upload only web/ — the copies were made locally before upload.
  if (existsSync(join(web, "public", "data")) && existsSync(join(web, "api", "_engine"))) {
    console.log("prepare: repo sources absent, keeping pre-copied public/data + api/_engine");
    process.exit(0);
  }
  console.error("data/published missing — run data-pipeline/build_dataset.py first");
  process.exit(1);
}
rmSync(join(web, "public", "data"), { recursive: true, force: true });
mkdirSync(join(web, "public"), { recursive: true });
cpSync(published, join(web, "public", "data"), { recursive: true });

const engineDst = join(web, "api", "_engine");
rmSync(engineDst, { recursive: true, force: true });
cpSync(join(repo, "ti-framework", "ti_framework"), join(engineDst, "ti_framework"), {
  recursive: true,
  filter: (src) => !src.includes("__pycache__"),
});
cpSync(join(repo, "api", "compute.py"), join(engineDst, "compute_service.py"));
console.log("prepared: public/data + api/_engine");

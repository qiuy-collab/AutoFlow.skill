#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const INTEGRATION = path.join(ROOT, "integrations", "impeccable");
const SKILL = path.join(INTEGRATION, "SKILL.md");
const DETECTOR = path.join(INTEGRATION, "scripts", "detect.mjs");
const CONTEXT = path.join(INTEGRATION, "scripts", "context.mjs");
const SIGNALS = path.join(INTEGRATION, "scripts", "context-signals.mjs");
const PALETTE = path.join(INTEGRATION, "scripts", "palette.mjs");
const METADATA = path.join(INTEGRATION, "scripts", "command-metadata.json");

function usage() {
  console.log(`AutoFlow Impeccable adapter

Usage:
  node scripts/impeccable_adapter.mjs check
  node scripts/impeccable_adapter.mjs command --name audit
  node scripts/impeccable_adapter.mjs context [--target <local-path>]
  node scripts/impeccable_adapter.mjs signals
  node scripts/impeccable_adapter.mjs palette
  node scripts/impeccable_adapter.mjs detect [--json] <local-file-or-directory>...

The adapter is local-only: it never runs npx, plugin hooks, update checks, or URL scans.`);
}

function fail(message) {
  console.error(`AutoFlow Impeccable adapter error: ${message}`);
  process.exitCode = 2;
}

function run(script, args) {
  const result = spawnSync(process.execPath, [script, ...args], {
    cwd: process.cwd(),
    stdio: "inherit",
    env: {
      ...process.env,
      AUTOFLOW_IMPECCABLE_OFFLINE: "1",
    },
  });
  if (result.error) fail(result.error.message);
  else if (result.status !== 0) process.exitCode = result.status ?? 1;
}

function check() {
  const required = [SKILL, DETECTOR, CONTEXT, SIGNALS, PALETTE, METADATA];
  const missing = required.filter((file) => !fs.existsSync(file));
  if (missing.length) return fail(`missing integrated files: ${missing.join(", ")}`);
  console.log("integrated-impeccable available");
  console.log(`skill=${SKILL}`);
  console.log(`detector=${DETECTOR}`);
  console.log("network_update_check=false");
}

function command(args) {
  const index = args.indexOf("--name");
  const name = index >= 0 ? args[index + 1] : "";
  if (!name) return fail("command requires --name <command>");
  let metadata;
  try {
    metadata = JSON.parse(fs.readFileSync(METADATA, "utf8"));
  } catch (error) {
    return fail(`cannot read command metadata: ${error.message}`);
  }
  if (!Object.prototype.hasOwnProperty.call(metadata, name)) {
    return fail(`unknown Impeccable command: ${name}`);
  }
  const reference = path.join(INTEGRATION, "reference", `${name}.md`);
  if (!fs.existsSync(reference)) return fail(`command reference is missing: ${reference}`);
  console.log(JSON.stringify({ command: name, reference, description: metadata[name].description }, null, 2));
}

function detect(args) {
  const urls = args.filter((target) => /^https?:\/\//i.test(target));
  if (urls.length) return fail(`URL scans are disabled in AutoFlow: ${urls.join(", ")}`);
  run(DETECTOR, args);
}

const [action, ...args] = process.argv.slice(2);
if (!action || action === "--help" || action === "-h") usage();
else if (action === "check") check();
else if (action === "command") command(args);
else if (action === "context") run(CONTEXT, args);
else if (action === "signals") run(SIGNALS, args);
else if (action === "palette") run(PALETTE, args);
else if (action === "detect") detect(args);
else fail(`unknown action: ${action}`);

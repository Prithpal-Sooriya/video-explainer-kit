// node tests/test.ts   (the render tests skip themselves when Chrome or ffmpeg is missing)
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readdirSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { buildFfmpegArgs, buildFrameSchedule, findChrome, findFfmpeg, loadModule, resolveTiming, startServer, validateSegmentAdvances } from "../render/vw.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const KIT = dirname(HERE);
const VW = join(KIT, "render", "vw.ts");
const FIXTURE = join(HERE, "fixtures", "layout");
const canRender = [findChrome, findFfmpeg].every((f) => {
	try {
		return f();
	} catch {
		return false;
	}
});
const render = (...args: string[]) => spawnSync("node", [VW, "render", ...args], { encoding: "utf-8", timeout: 120000 });
const timeline = { segments: [{ id: "a" }, { id: "b" }] };

// ---- pure logic ----

test("frame schedule: beats land on rounded global frames and segments accumulate", () => {
	const s = buildFrameSchedule(timeline, { a: [1.0, 2.5], b: [1.0] }, 10);
	assert.deepEqual(s.map((x) => [x.globalFrame, x.segmentId, x.isLast]), [[10, "a", false], [25, "a", true], [35, "b", true]]);
});

test("the audio track's timing overrides segment advances", () => {
	const segs = [{ id: "a", advances: [1, 2] }, { id: "b", advances: [3] }];
	assert.deepEqual(resolveTiming(segs), { a: [1, 2], b: [3] });
	assert.deepEqual(resolveTiming(segs, { timing: { perSegment: { a: [5, 6] } } }), { a: [5, 6], b: [3] });
});

test("advances must be present, positive and strictly increasing", () => {
	assert.deepEqual(validateSegmentAdvances(timeline, { a: [1, 2], b: [1] }), []);
	const bad = validateSegmentAdvances(timeline, { a: [2, 1], b: [] }).join("\n");
	assert.match(bad, /strictly increasing/);
	assert.match(bad, /missing or empty/);
});

test("ffmpeg: audio is padded and clipped to the video length", () => {
	assert.ok(!buildFfmpegArgs(30, "o.mp4").includes("-shortest"));
	const a = buildFfmpegArgs(30, "o.mp4", "a.mp3");
	assert.ok(a.includes("apad") && a.includes("-shortest") && a.at(-1) === "o.mp4");
});

test("loader: the example timeline loads in Node with its CSS no-op'd", async () => {
	const timelineModule = await loadModule(join(KIT, "example", "example.timeline.ts"));
	assert.deepEqual(timelineModule.default.segments.map((s: any) => s.id), ["why", "how", "proof"]);
	assert.equal(timelineModule.default.default_audio_track.timing.perSegment.why.length, 2);
});

// ---- server ----

test("server: serves the project, the kit at the site root, wraps CSS, guards paths", { skip: !canRender && !existsSync(VW) }, async () => {
	const server = await startServer(FIXTURE, join(FIXTURE, "fixture.timeline.ts"), 30);
	const get = (p: string) => fetch(server.url + p);
	try {
		assert.match(await (await get("/render.html")).text(), /"videowright":"\/__vw\/vw\.ts"/);
		const browser = await (await get("/__vw/vw.ts")).text();
		assert.match(browser, /export function defineSegment/);
		assert.ok(!browser.includes("node:child_process") && !browser.includes("startServer"), "Chrome must not receive the Node half");
		assert.match(await (await get("/c/segments/lockup")).text(), /export const lockup/);
		assert.match(await (await get("/c/kit/tailwind.css")).text(), /document\.head\.appendChild/);
		assert.match(await (await get("/kit/kit")).text(), /export function stage/, "kit files resolve from outside the project root");
		assert.match(await (await get("/themes/motion-engineering/tokens.css")).text(), /document\.head\.appendChild/);
		assert.equal((await get("/c/../../../etc/hosts")).status, 404, "dot-dot traversal is blocked");
		assert.equal((await get("/etc/hosts")).status, 404, "only indexed kit files are served");
		assert.equal((await get("/c/%2e%2e/%2e%2e/etc/hosts")).status, 404, "encoded traversal is blocked");
	} finally {
		await server.close();
	}
});

// ---- real renders ----

test("render: dry run reports the frame count", { skip: !canRender }, () => {
	const r = render(join(KIT, "example", "example.timeline.ts"), "--dry-run");
	assert.equal(r.status, 0, r.stderr);
	assert.match(r.stdout, /total frames: \d+ \(\d+\.\d+s\) at 1920x1080 30fps/);
});

test("render: writes an mp4", { skip: !canRender }, () => {
	const out = join(mkdtempSync(join(tmpdir(), "vw-out-")), "o.mp4");
	const r = render(join(FIXTURE, "fixture.timeline.ts"), "--fps", "5", "--output", out);
	assert.equal(r.status, 0, r.stderr);
	assert.match(r.stdout, /Rendered 27 frames/);
	const bytes = readFileSync(out);
	assert.ok(bytes.length > 1000 && bytes.subarray(4, 8).toString() === "ftyp");
});

test("render: a bad fixture fails the layout check", { skip: !canRender }, () => {
	const r = render(join(FIXTURE, "bad.timeline.ts"), "--check");
	assert.notEqual(r.status, 0);
	assert.match(r.stderr + r.stdout, /Layout check failed with \d+ errors/);
});

test("render: --frames writes one PNG per beat", { skip: !canRender }, () => {
	const dir = mkdtempSync(join(tmpdir(), "vw-frames-"));
	const r = render(join(FIXTURE, "fixture.timeline.ts"), "--check", "--frames", dir);
	assert.equal(r.status, 0, r.stderr + r.stdout);
	const pngs = readdirSync(dir).filter((f) => f.endsWith(".png"));
	assert.deepEqual(pngs, ["01-clean-cards-beat1.png", "02-clean-cards-beat2.png", "03-clean-code-beat1.png", "04-clean-image-beat1.png", "05-clean-type-beat1.png"]);
	for (const f of pngs) assert.ok(readFileSync(join(dir, f)).length > 1000, f);
});

test("tokens: the shipped sheet is in sync with the theme", () => {
	const r = spawnSync("python3", [join(KIT, "tools", "tokens.py"), "build", "--theme", "motion-engineering", "--check"], { encoding: "utf-8", cwd: KIT });
	assert.equal(r.status, 0, r.stdout + r.stderr);
	assert.match(r.stdout, /in sync/);
});

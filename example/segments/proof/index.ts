import { defineSegment } from "videowright";
import { clearTimers, scheduleCaptions, stage } from "../../../kit/kit";
import { advances, voiceover } from "../../timing";
import { cues } from "../../captions";

let host: HTMLElement | null = null;
let timers: number[] = [];

export default defineSegment({
	id: "proof",
	advances: advances.proof,
	voiceover: voiceover.proof,
	mount(el: HTMLElement) {
		host = el;
		el.innerHTML = stage(
			`<div class="grid grid-cols-2 gap-12">
				<div class="flex flex-col gap-4 rounded-lg border border-muted bg-section p-10">
					<span class="self-start rounded-full bg-subsection px-4 py-1 text-body-sm-medium text-alternative">PER BEAT</span>
					<div class="text-display-xl text-default">1 s</div>
					<p class="text-body-md text-alternative">per scene, checked while it plays</p>
				</div>
				<div class="flex flex-col gap-4 rounded-lg border-2 border-accent-default bg-section p-10">
					<span class="self-start rounded-full bg-accent-default px-4 py-1 text-body-sm-medium text-accent-inverse">CLEAN RUN</span>
					<div class="text-display-xl text-default">0</div>
					<p class="text-body-md text-alternative">layout findings left in the video</p>
				</div>
			</div>
			<span class="font-mono text-body-sm text-alternative">1920x1080 · 30 fps · MP4</span>`,
			`<span class="font-mono text-body-xs text-alternative">video-explainer-kit</span>`,
		);
	},
	async play(ctx: any) {
		timers = scheduleCaptions(host!, cues.proof);
		await ctx.waitForNext();
	},
	unmount() {
		clearTimers(timers);
	},
});

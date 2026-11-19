import { defineSegment } from "videowright";
import { clearTimers, scheduleCaptions, stage } from "../../../kit/kit";
import { advances, voiceover } from "../../timing";
import { cues } from "../../captions";

const step = (n: string, title: string, body: string, extra = "") =>
	`<div class="flex flex-col gap-4 rounded-md border border-muted bg-section p-8 ${extra}">
		<span class="font-mono text-body-xs-medium text-alternative">${n}</span>
		<div class="text-heading-sm text-default">${title}</div>
		<p class="text-body-md text-alternative">${body}</p>
	</div>`;

let host: HTMLElement | null = null;
let timers: number[] = [];

export default defineSegment({
	id: "how",
	advances: advances.how,
	voiceover: voiceover.how,
	mount(el: HTMLElement) {
		host = el;
		el.innerHTML = stage(
			`<div class="vw-title">From script to video</div>
			<div class="grid grid-cols-4 gap-8">
				${step("01", "prep", "Rewrite spoken lines for the voice.")}
				${step("02", "synth", "Local narration, cached per line.")}
				${step("03", "verify-audio", "Whisper checks every chunk.", "border-accent-default")}
				${step("04", "render", "Frames to MP4, check included.")}
			</div>`,
			`<span class="font-mono text-body-xs text-alternative">video-explainer-kit</span>`,
		);
	},
	async play(ctx: any) {
		timers = scheduleCaptions(host!, cues.how);
		await ctx.waitForNext();
	},
	unmount() {
		clearTimers(timers);
	},
});

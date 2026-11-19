import { defineSegment } from "videowright";
import { card, clearTimers, grid, pill, scheduleCaptions, stage } from "../../../kit/kit";
import { advances, voiceover } from "../../timing";
import { cues } from "../../captions";

let host: HTMLElement | null = null;
let timers: number[] = [];

export default defineSegment({
	id: "why",
	advances: advances.why,
	voiceover: voiceover.why,
	mount(el: HTMLElement) {
		host = el;
		el.innerHTML = stage(
			`${pill("WHY", { accent: true })}
			<div class="vw-title">Take layout off your plate</div>
			${grid(
				3,
				card("Script", "scenes.json carries display and spoken lines.", { attr: "data-s" }),
				card("Voice", "Kokoro runs locally, offline, in the setup venv.", { attr: "data-v" }),
				card("Check", "One command reads the scene like a reviewer.", { attr: "data-c", focus: true }),
			)}`,
			`<span class="font-mono text-body-xs text-alternative">video-explainer-kit</span>`,
		);
	},
	async play(ctx: any) {
		const el = host!;
		timers = scheduleCaptions(el, cues.why);
		for (const k of ["s", "v", "c"]) el.querySelector(`[data-${k}]`)!.animate([{ opacity: 0, transform: "translateY(24px)" }, { opacity: 1, transform: "none" }], { duration: 400, fill: "both", easing: "cubic-bezier(0.2, 0.8, 0.2, 1)" });
		await ctx.waitForNext();
	},
	unmount() {
		clearTimers(timers);
	},
});

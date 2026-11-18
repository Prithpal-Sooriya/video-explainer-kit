import { defineSegment } from "videowright";
import { stage } from "../../kit/kit";
import { lockup } from "../lockup";

let host: HTMLElement | null = null;

export default defineSegment({
	id: "tw-title",
	advances: [1.2, 2.4],
	mount(el: HTMLElement) {
		host = el;
		el.innerHTML = stage(
			`<div class="flex flex-col gap-6">
				<span class="self-start rounded-full bg-accent-default px-6 py-3 text-body-sm-medium text-accent-inverse">LAYOUT CHECK</span>
				<h1 class="text-display-lg text-default">Every card sits in the safe area</h1>
				<p class="text-body-lg text-alternative" data-sub>Kit · layout check · <span class="text-accent-default">one file</span></p>
				<span class="font-mono text-body-sm text-alternative">kit · prep · synth · check · render</span>
			</div>`,
			lockup(),
		);
	},
	async play(ctx: any) {
		host!.querySelector("[data-sub]")!.animate([{ opacity: 0, transform: "translateY(24px)" }, { opacity: 1, transform: "none" }], { duration: 420, fill: "both", easing: "cubic-bezier(0.2, 0.8, 0.2, 1)" });
		await ctx.waitForNext();
	},
	unmount() {
		host = null;
	},
});

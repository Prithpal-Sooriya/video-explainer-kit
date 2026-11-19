import { defineSegment } from "videowright";

export default defineSegment({
	id: "bad-contrast",
	advances: [1],
	mount(el: HTMLElement) {
		el.innerHTML = `<div class="vw-stage">
			<div class="vw-lockup"><span>EXPLAINER KIT</span></div>
			<div class="vw-safe">
				<div class="vw-title" style="color:#000">What changed</div>
				<div class="vw-row">
					<div class="vw-card"><div class="vw-card-title" style="color:#111">Safe area</div><div class="vw-body" style="color:#333">Grew from 0px to 96px.</div></div>
					<div class="vw-card"><div class="vw-card-title">Layout check</div><div class="vw-body" style="color:#66676a;font-size:20px">Now catches every spill.</div></div>
				</div>
				<span class="vw-pill" style="background:#ff8800;color:#fff;font-size:20px">KIT-0001</span>
			</div>
		</div>`;
	},
	async play() {},
});

import { defineSegment } from "videowright";

export default defineSegment({
	id: "bad-overlap",
	advances: [1, 2],
	mount(el: HTMLElement) {
		el.innerHTML = `<div class="vw-stage">
			<div class="vw-lockup"><span>EXPLAINER KIT</span></div>
			<h1 data-title style="position:absolute;left:120px;top:90px;font-size:96px;margin:0">Heading overlaps the lockup</h1>
			<div data-a class="vw-card" style="position:absolute;left:200px;top:340px;width:700px;height:300px"><div class="vw-card-title">Before</div><div class="vw-body">The card sits on its neighbour.</div></div>
			<div data-b class="vw-card" style="position:absolute;left:760px;top:420px;width:700px;height:300px"><div class="vw-card-title">After</div><div class="vw-body">The card keeps its distance.</div></div>
			<div data-cap class="vw-captions" style="opacity:1">The caption used to cover the content.</div>
		</div>`;
	},
	async play(ctx: any) {
		await ctx.waitForNext();
	},
});

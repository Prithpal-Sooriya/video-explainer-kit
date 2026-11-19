import { defineSegment } from "videowright";
import { stage } from "../../kit/kit";
import { lockup } from "../lockup";

export default defineSegment({
	id: "notes-measure",
	advances: [1],
	mount(el: HTMLElement) {
		el.innerHTML = stage(
			`<h2 class="text-display-md text-default">Why the safe area grew</h2>
			<p class="text-body-xs text-alternative">The safe area used to be measured from the frame edge, which meant that on wide layouts the content sat in the far left of the canvas and left more than half of the frame empty, so the stage now insets content by 96px on the sides and 152px from the top, which keeps every beat balanced at 1920x1080.</p>`,
			lockup(),
		);
	},
	async play() {},
});

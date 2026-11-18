import { defineSegment } from "videowright";
import { card, grid, stage, stack } from "../../kit/kit";
import { lockup } from "../lockup";

export default defineSegment({
	id: "clean-type",
	advances: [1],
	mount(el: HTMLElement) {
		el.innerHTML = stage(
			`${grid(
				3,
				stack(
					`<div class="vw-display-md">Display md</div>`,
					`<div class="vw-heading-lg">Heading lg</div>`,
					`<div class="vw-heading-md">Heading md</div>`,
					`<div class="vw-heading-sm vw-muted">Heading sm, muted</div>`,
				),
				card(
					"Surface 1",
					`<div class="vw-body-lg">Body lg on section</div><div class="vw-body-sm vw-muted">Body sm, alternative text</div><div class="vw-body-xs vw-muted">Body xs, dim text</div>`,
				),
				card(
					"Surface 2",
					`<div class="vw-body-md-bold" style="color:#7ee2a8">Success</div><div class="vw-body-md-medium" style="color:#ff6b6b">Error</div><div class="vw-body-sm-medium" style="color:#ffc857">Warning</div><div class="vw-body-xs-medium" style="color:#9b8cff">Primary</div>`,
					{ level: 2 },
				),
			)}`,
			lockup(),
		);
	},
	async play() {},
});

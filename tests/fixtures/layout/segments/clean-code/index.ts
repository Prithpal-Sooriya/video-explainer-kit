import { defineSegment } from "videowright";
import { card, code, row, stack, stage } from "../../kit/kit";
import { lockup } from "../lockup";

export default defineSegment({
	id: "clean-code",
	advances: [1],
	mount(el: HTMLElement) {
		el.innerHTML = stage(
			`<div class="vw-title">The fix</div>
			${row(
				code("render/layout-check.js", `<span class="vw-muted">  const safe = { left: 96, top: 152 };</span>\n<span style="color:#ff6b6b">-   left: 0, top: 0,</span>\n<span style="color:#7ee2a8">+   left: 96, top: 152,</span>\n<span class="vw-muted">  };</span>`),
				stack(card("Why", "The content ran under the lockup."), card("Effect", "The check reports every spill.", { level: 2 })),
			)}`,
			lockup(),
		);
	},
	async play() {},
});

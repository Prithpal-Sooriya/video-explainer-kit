import { defineSegment } from "videowright";
import { image, pill, stage } from "../../kit/kit";
import { lockup } from "../lockup";

export default defineSegment({
	id: "clean-image",
	advances: [1],
	mount(el: HTMLElement) {
		el.innerHTML = stage(`${pill("SCREENSHOT")}<div class="vw-title">After the change</div>${image("/c/image.svg", "A placeholder graphic inside a frame")}`, lockup());
	},
	async play() {},
});

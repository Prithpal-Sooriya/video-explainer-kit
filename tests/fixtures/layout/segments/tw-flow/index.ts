import { defineSegment } from "videowright";
import { stage } from "../../kit/kit";
import { lockup } from "../lockup";

const step = (n: string, title: string, body: string, extra = "") =>
	`<div class="flex flex-col gap-4 rounded-md border border-muted bg-section p-8 ${extra}">
		<span class="text-body-xs-medium font-mono text-alternative">${n}</span>
		<div class="text-heading-sm text-default">${title}</div>
		<p class="text-body-md text-alternative">${body}</p>
	</div>`;

export default defineSegment({
	id: "tw-flow",
	advances: [1],
	mount(el: HTMLElement) {
		el.innerHTML = stage(
			`<h2 class="text-heading-lg text-default">How the layout check runs</h2>
			<div class="grid grid-cols-3 gap-8">
				${step("01", "Mount", "Each segment renders into the stage.")}
				${step("02", "Measure", "Every box is compared to the safe area.", "border-accent-default")}
				${step("03", "Report", "Findings fail, notes do not.")}
			</div>
			<div class="flex flex-row items-center gap-3">
				<span class="rounded-full border border-muted bg-subsection px-4 py-1 font-mono text-body-sm text-primary-default">render/layout-check.js</span>
				<span class="text-body-sm text-success-default">+12 −4</span>
			</div>`,
			lockup(),
		);
	},
	async play() {},
});

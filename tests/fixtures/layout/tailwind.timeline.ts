import "./styles/fixture/style.css";
import "./kit/kit.css";
import "./kit/tailwind.css";

export default {
	meta: { title: "Layout check: clean (fixture + tailwind)", style: "fixture" },
	segments: [{ id: "tw-title" }, { id: "tw-flow", transition: "fade" }, { id: "tw-code", transition: "fade" }, { id: "tw-stat", transition: "fade" }],
};

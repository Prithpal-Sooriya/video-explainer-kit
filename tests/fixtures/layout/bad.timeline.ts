import "./styles/fixture/style.css";
import "./kit/kit.css";

export default {
	meta: { title: "Layout check: deliberate defects", style: "fixture" },
	segments: [{ id: "bad-overlap" }, { id: "bad-bounds", transition: "fade" }, { id: "bad-contrast", transition: "fade" }],
};

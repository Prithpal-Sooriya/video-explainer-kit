import "./styles/fixture/style.css";
import "./kit/kit.css";
import "./kit/tailwind.css";

export default {
	meta: { title: "Layout check: notes that do not fail", style: "fixture" },
	segments: [{ id: "notes-tight" }, { id: "notes-sparse", transition: "fade" }, { id: "notes-measure", transition: "fade" }],
};

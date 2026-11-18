import track from "./audio/tracks/v1/track";
import "../../themes/motion-engineering/style.css";
import "../../themes/motion-engineering/tokens.css";
import "../../themes/motion-engineering/tailwind.css";
import "../../kit/kit.css";

export default {
	meta: { title: "video-explainer-kit", style: "motion-engineering" },
	default_audio_track: track,
	segments: [{ id: "why" }, { id: "how", transition: "fade" }, { id: "proof", transition: "fade" }],
};

import type { Cue } from "./segments/shared";

export const cues: Record<string, Cue[]> = {
 "why": [
  {
   "start": 0.29,
   "end": 2.26,
   "text": "An explainer is a script, a voice,"
  },
  {
   "start": 2.58,
   "end": 4.32,
   "text": "and a hundred small layout decisions:"
  },
  {
   "start": 5.16,
   "end": 7.1,
   "text": "spacing, contrast, caption timing."
  },
  {
   "start": 8.055,
   "end": 9.755,
   "text": "The kit takes the decisions off your"
  },
  {
   "start": 9.755,
   "end": 12.235,
   "text": "plate: one check reads every scene like"
  },
  {
   "start": 12.235,
   "end": 12.955,
   "text": "a picky reviewer."
  }
 ],
 "how": [
  {
   "start": 0.3,
   "end": 2.12,
   "text": "Write scenes.json,"
  },
  {
   "start": 2.7,
   "end": 4.96,
   "text": "then run prep, synth, and verify-audio."
  },
  {
   "start": 5.62,
   "end": 7.2,
   "text": "The narration is timed to the words"
  },
  {
   "start": 7.2,
   "end": 8.12,
   "text": "you actually show."
  },
  {
   "start": 9.05,
   "end": 10.47,
   "text": "Then render with the check flag."
  },
  {
   "start": 11.19,
   "end": 12.15,
   "text": "Overlapping titles,"
  },
  {
   "start": 12.67,
   "end": 15.15,
   "text": "clipped cards, and unreadable grey text all"
  },
  {
   "start": 15.15,
   "end": 15.87,
   "text": "fail the build."
  }
 ],
 "proof": [
  {
   "start": 0.28,
   "end": 2.26,
   "text": "The check covers overlap, bounds,"
  },
  {
   "start": 2.72,
   "end": 3.22,
   "text": "safe area,"
  },
  {
   "start": 3.68,
   "end": 4.64,
   "text": "clipping, contrast,"
  },
  {
   "start": 5.12,
   "end": 7.28,
   "text": "and unknown utility classes in about 1"
  },
  {
   "start": 7.28,
   "end": 8.0,
   "text": "second per scene."
  },
  {
   "start": 8.885,
   "end": 11.385,
   "text": "A clean run renders the final MP4"
  },
  {
   "start": 11.385,
   "end": 14.465,
   "text": "at 1920x1080 and 30 fps,"
  },
  {
   "start": 15.145,
   "end": 16.865,
   "text": "with captions that follow the voice."
  }
 ]
};

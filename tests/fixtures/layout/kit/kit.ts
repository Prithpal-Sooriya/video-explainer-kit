export interface Cue {
	start: number;
	end: number;
	text: string;
}

export function raw(html: string): string {
	return html;
}

function esc(text: string): string {
	return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

export function stage(content: string, lockup = ""): string {
	return `<div class="vw-stage">${lockup ? `<div class="vw-lockup">${lockup}</div>` : ""}<div class="vw-safe">${content}</div><div class="vw-captions" data-cap></div></div>`;
}

export function row(...items: string[]): string {
	return `<div class="vw-row">${items.join("")}</div>`;
}

export function stack(...items: string[]): string {
	return `<div class="vw-stack">${items.join("")}</div>`;
}

export function grid(cols: number, ...items: string[]): string {
	return `<div class="vw-grid" style="--cols:${cols}">${items.join("")}</div>`;
}

export function card(title: string, body = "", opts: { attr?: string; focus?: boolean; level?: 1 | 2 } = {}): string {
	const cls = ["vw-card", opts.level === 2 ? "vw-card-2" : "", opts.focus ? "vw-focus" : ""].filter(Boolean).join(" ");
	return `<div class="${cls}" ${opts.attr ?? ""}><div class="vw-card-title">${esc(title)}</div>${body ? `<div class="vw-body">${esc(body)}</div>` : ""}</div>`;
}

export function pill(text: string, opts: { attr?: string; accent?: boolean } = {}): string {
	return `<span class="vw-pill${opts.accent ? " vw-pill-accent" : ""}" ${opts.attr ?? ""}>${esc(text)}</span>`;
}

export function code(file: string, html: string, attr = ""): string {
	return `<div class="vw-code" ${attr}><div class="vw-code-head">${esc(file)}</div>${html}</div>`;
}

export function image(src: string, alt: string, attr = ""): string {
	const scheme = /^([a-z][a-z0-9+.-]*):/i.exec(src)?.[1]?.toLowerCase();
	if (src.startsWith("//") || (scheme && scheme !== "data")) {
		throw new Error(`image() src must be a relative or data: URL, got: ${src}`);
	}
	return `<div class="vw-frame vw-fill" ${attr}><img src="${esc(src)}" alt="${esc(alt)}"></div>`;
}

export function fitText(root: ParentNode, selector = "[data-fit]", minPx = 20): void {
	for (const el of Array.from(root.querySelectorAll<HTMLElement>(selector))) {
		let size = parseFloat(getComputedStyle(el).fontSize);
		while (size > minPx && (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1)) {
			size -= 2;
			el.style.fontSize = `${size}px`;
		}
	}
}

export function scheduleCaptions(root: ParentNode, cues: Cue[]): number[] {
	const pill = root.querySelector<HTMLElement>("[data-cap]");
	if (!pill) return [];
	const timers: number[] = [];
	for (const cue of cues) {
		timers.push(
			window.setTimeout(() => {
				pill.textContent = cue.text;
				pill.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 200, fill: "forwards" });
			}, cue.start * 1000),
			window.setTimeout(() => pill.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 200, fill: "forwards" }), Math.max(cue.start * 1000 + 200, cue.end * 1000 - 200)),
		);
	}
	return timers;
}

export function clearTimers(timers: number[]): void {
	for (const t of timers) window.clearTimeout(t);
	timers.length = 0;
}

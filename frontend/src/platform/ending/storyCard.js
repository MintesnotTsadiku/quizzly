import { t } from "@/i18n";

// Draw only the explicitly previewed aggregate story, never a screenshot of the podium.
export async function drawStory({ brand, accent, ending, moment, locale }) {
	const font = locale === "am" ? '"Gather Ethiopic", sans-serif' : "sans-serif";
	if (locale === "am") await document.fonts.load('500 32px "Gather Ethiopic"');
	const canvas = document.createElement("canvas");
	canvas.width = 1080;
	canvas.height = 1080;
	const ctx = canvas.getContext("2d");
	const purple = /^#[a-f\d]{6}$/i.test(accent || "") ? accent : "#745098";
	let y = 85;
	function line(text, size = 32, weight = 500, color = "#302344", maxLines = 6) {
		ctx.font = `${weight} ${size}px ${font}`;
		ctx.fillStyle = color;
		const lines = [];
		let current = "";
		// Keep words together in both languages; wrap long unbroken user text safely.
		for (const word of String(text).split(/\s+/)) {
			const candidate = current ? current + " " + word : word;
			if (ctx.measureText(candidate).width <= 900) {
				current = candidate;
				continue;
			}
			if (current) lines.push(current);
			current = "";
			for (const char of word) {
				if (ctx.measureText(current + char).width > 900) {
					lines.push(current);
					current = "";
				}
				current += char;
			}
		}
		if (current) lines.push(current);
		const shown = lines.slice(0, maxLines);
		if (lines.length > maxLines) shown[maxLines - 1] = shown[maxLines - 1].slice(0, -2) + "…";
		for (const row of shown) {
			ctx.fillText(row, 90, y);
			y += size * 1.45;
		}
	}
	ctx.fillStyle = "#fff5e5";
	ctx.fillRect(0, 0, 1080, 1080);
	ctx.fillStyle = purple;
	ctx.fillRect(0, 0, 1080, 18);
	line(brand, 26, 800, "#302344", 1);
	y += 15;
	line(t("Crowd Compass"), 25, 600, "#705195", 1);
	y += 35;
	line(t("Played together. Remembered together."), 25, 600, "#705195", 2);
	y += 12;
	line(t("How well do you know your people?"), 48, 800, "#302344", 3);
	y += 12;
	line(
		t("{rounds} rounds · {entries} playing entries", {
			rounds: ending.rounds_completed,
			entries: ending.entries,
		}),
		26,
		500,
		"#6e625f",
		2,
	);
	y += 35;
	y = Math.max(y, 520);
	if (moment) {
		line(moment.prompt, 30, 500, "#302344", 3);
		y += 12;
		line(moment.choice, 38, 800, "#302344", 2);
		line(
			t(moment.ranked ? "{percent}% of weighted votes" : "{percent}% of votes", {
				percent: moment.percent,
			}),
			27,
			600,
			"#705195",
			1,
		);
	} else
		line(
			t("We chose for ourselves. Then we tried to read the room. Your turn?"),
			37,
			600,
			"#302344",
			4,
		);
	y = 1005;
	line(t("Vote. Predict. Reveal."), 26, 700, "#302344", 1);
	return new Promise((resolve, reject) =>
		canvas.toBlob(
			(blob) => (blob ? resolve(blob) : reject(new Error("No image"))),
			"image/png",
		),
	);
}

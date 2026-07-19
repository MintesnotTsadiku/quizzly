// Words come from the boot context so the server-side profanity test covers
// exactly the combinations this generator can produce.
const { adjectives = [], nouns = [] } = window.nickname_words || {};

function pick(list) {
	return list[Math.floor(Math.random() * list.length)];
}

export function suggestNicknames(count = 3) {
	// Distinct nouns, not just distinct names: three "…Narwhal" options read as
	// one option with a typo.
	const used = new Set();
	while (used.size < count && adjectives.length && nouns.length >= count) {
		used.add(pick(nouns));
	}
	return [...used].map((noun) => `${pick(adjectives)}${noun}`);
}

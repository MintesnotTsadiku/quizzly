import frappeUIPreset from "frappe-ui/tailwind";

export default {
	presets: [frappeUIPreset],
	content: [
		"./index.html",
		"./src/**/*.{vue,js,ts,jsx,tsx}",
		"./node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}",
	],
	theme: {
		extend: {
			colors: {
				night: "#16111F",
				dusk: "#241C31",
				haze: "#3A2F4D",
				paper: "#F4F0FA",
				ember: "#FF5A36",
				lagoon: "#17B0BE",
				gold: "#FFC43D",
				orchid: "#9B6BFF",
			},
			fontFamily: {
				display: ['"Bricolage Grotesque"', "system-ui", "sans-serif"],
				sans: ['"Instrument Sans"', "system-ui", "sans-serif"],
				mono: ['"Martian Mono"', "ui-monospace", "monospace"],
			},
			// frappe-ui's preset caps fontSize at 3xl (24px); add display sizes for the big screen
			fontSize: {
				"4xl": ["2.25rem", "1.05"],
				"5xl": ["3rem", "1.02"],
				"6xl": ["3.75rem", "1"],
				"7xl": ["4.5rem", "0.95"],
				"8xl": ["6rem", "0.9"],
				"9xl": ["8rem", "0.88"],
			},
		},
	},
	plugins: [],
};

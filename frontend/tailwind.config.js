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
			// frappe-ui's preset caps fontSize at 3xl (24px); add display sizes for the big screen
			fontSize: {
				"4xl": ["2.25rem", "1.1"],
				"5xl": ["3rem", "1.1"],
				"6xl": ["3.75rem", "1"],
				"8xl": ["6rem", "1"],
			},
		},
	},
	plugins: [],
};

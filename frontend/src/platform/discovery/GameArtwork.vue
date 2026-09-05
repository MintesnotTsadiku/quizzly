<template>
	<div class="gp-art" :class="`gp-art-${color}`" aria-hidden="true">
		<svg viewBox="0 0 440 270" focusable="false">
			<g fill="none" stroke="currentColor" stroke-width="2" opacity=".18">
				<circle cx="220" cy="135" r="98" />
				<circle cx="220" cy="135" r="128" />
			</g>
			<g
				v-if="gameKey === 'common-ground'"
				stroke="#30203e"
				stroke-width="3"
				stroke-linejoin="round"
			>
				<path
					d="M82 80q0-20 20-20h140q20 0 20 20v69q0 20-20 20h-76l-34 28 2-28h-32q-20 0-20-20z"
					fill="#fff9e9"
					transform="rotate(-9 172 120)"
				/>
				<path
					d="M210 119q0-18 18-18h104q18 0 18 18v61q0 18-18 18h-20l3 23-31-23h-56q-18 0-18-18z"
					fill="#beafff"
					transform="rotate(9 280 156)"
				/>
				<path
					d="M133 116q27 36 56-2m67 38q18 23 38 0"
					fill="none"
					stroke-linecap="round"
				/>
				<circle cx="128" cy="100" r="3" fill="#30203e" />
				<circle cx="188" cy="97" r="3" fill="#30203e" />
			</g>
			<g v-else-if="gameKey === 'crowd-compass'" transform="translate(220 133) rotate(-18)">
				<circle r="87" fill="#fffaf0" stroke="#30203e" stroke-width="3" />
				<circle
					r="67"
					fill="none"
					stroke="#30203e"
					stroke-dasharray="2 14"
					stroke-width="5"
				/>
				<path
					d="M0-61 22 12 0 61-22-12Z"
					fill="#7650cd"
					stroke="#30203e"
					stroke-width="3"
				/>
				<path d="M0-61 22 12-22-12Z" fill="#ff956f" />
				<circle r="9" fill="#30203e" />
			</g>
			<g
				v-else-if="gameKey === 'cuecast'"
				fill="#30203e"
				stroke="#30203e"
				stroke-width="9"
				stroke-linecap="round"
			>
				<circle cx="218" cy="72" r="20" />
				<path
					d="m218 105-10 61m6-40-52-14-15-35m64 42 48-21 30-40m-80 108-40 56m41-54 48 41 31-6"
					fill="none"
				/>
				<path d="m106 85-17-9m12 28-22 3m237-47 19-9m-13 30 23 2" stroke-width="4" />
			</g>
			<g
				v-else-if="gameKey === 'doodle-dash'"
				stroke="#30203e"
				stroke-width="3"
				fill="#fffaf0"
			>
				<rect
					x="116"
					y="38"
					width="204"
					height="186"
					rx="12"
					transform="rotate(-8 220 135)"
				/>
				<path
					d="m154 150 22-58 22 24 36-3 28-25 15 58q-55 72-123 4"
					fill="#d3bcff"
					stroke-linejoin="round"
				/>
				<circle cx="191" cy="147" r="3" fill="#30203e" />
				<circle cx="246" cy="145" r="3" fill="#30203e" />
				<path
					d="m210 163 8 7 8-7m-66-9-35-5m41 18-39 7m140-19 34-8m-35 23 35 4"
					fill="none"
				/>
			</g>
			<g v-else-if="gameKey === 'sequence-sprint'" stroke="#30203e" stroke-width="3">
				<rect
					x="80"
					y="93"
					width="90"
					height="110"
					rx="15"
					fill="#bda8f5"
					transform="rotate(-12 125 148)"
				/>
				<rect x="178" y="50" width="90" height="110" rx="15" fill="#fffaf0" />
				<rect
					x="278"
					y="98"
					width="90"
					height="110"
					rx="15"
					fill="#b9d77c"
					transform="rotate(12 323 153)"
				/>
				<g
					stroke-width="0"
					fill="#30203e"
					font-size="50"
					font-family="system-ui"
					font-weight="800"
					text-anchor="middle"
				>
					<text x="126" y="166">2</text>
					<text x="223" y="123">1</text>
					<text x="320" y="171">3</text>
				</g>
			</g>
			<g v-else stroke="#30203e" stroke-width="3" fill="#fffaf0">
				<path
					d="m220 43 25 47 53 8-39 39 9 54-48-25-48 25 9-54-39-39 53-8z"
					fill="#9472df"
				/>
				<path
					d="m172 185-24 46 45-12 26 22 8-56m22-3 39 41-44-5-25 24-8-57"
					fill="#ffae89"
				/>
			</g>
			<g fill="#30203e">
				<path d="m351 38 3 11 11 3-11 3-3 11-3-11-11-3 11-3z" />
				<circle cx="72" cy="206" r="4" />
				<circle cx="362" cy="221" r="3" />
			</g>
		</svg>
	</div>
</template>
<script setup>
defineProps({ gameKey: String, color: { type: String, default: "peach" } });
</script>

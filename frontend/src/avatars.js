const pack = window.avatar_pack || { avatars: [], attribution: null };
const urls = Object.fromEntries(pack.avatars.map((avatar) => [avatar.id, avatar.url]));

export const avatars = pack.avatars;
export const attribution = pack.attribution;

export function avatarUrl(id) {
	return urls[id];
}

export function randomAvatar() {
	return avatars[Math.floor(Math.random() * avatars.length)]?.id;
}

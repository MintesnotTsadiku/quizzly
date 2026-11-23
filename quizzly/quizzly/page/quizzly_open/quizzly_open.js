// "Open app screens": opens a standalone screen of this app. Sidebar items link here with the screen path
// (/desk/quizzly-open/<path>); the Page roles decide who sees those items (docs/desk-navigation.md).
frappe.pages["quizzly-open"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({ parent: wrapper, title: __("Opening..."), single_column: true });
};

frappe.pages["quizzly-open"].on_page_show = function () {
	// Only a path on this site: leading slashes, backslashes and white space are dropped, so the target can never be another host.
	const path = frappe.get_route().slice(1).join("/").replace(/^[\s\\/]+/, "");
	window.location.replace("/" + path);
};

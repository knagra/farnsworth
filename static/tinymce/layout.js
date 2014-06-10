tinyMCE.init({
	selector: "textarea",
	height: 300,
	width: "100%",
	toolbar_items_size: 'small',
	browser_spellcheck: true,
	plugins: "paste searchreplace emoticons link image textcolor charmap media preview autolink",
	toolbar1: "styleselect | fontselect | fontsizeselect | bullist numlist | outdent indent hr | pastetext",
	toolbar2: "bold italic underline | searchreplace | link unlink charmap | emoticons image media | forecolor backcolor | preview undo redo",
	resize: "both",
	menubar: false,
	relative_urls: false
});

tinyMCE.init({
	selector: ".editable",
	inline: true,
	height: 300,
	width: "100%",
	toolbar_items_size: 'small',
	browser_spellcheck: true,
	plugins: "paste searchreplace emoticons link image textcolor charmap media preview autolink code",
	toolbar1: "styleselect | fontselect | fontsizeselect | bullist numlist | outdent indent hr | pastetext",
	toolbar2: "bold italic underline | searchreplace | link unlink charmap | emoticons image media | forecolor backcolor | preview undo redo",
	resize: "both",
	menubar: false,
	relative_urls: false
});

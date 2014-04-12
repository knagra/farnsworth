tinyMCE.init({
	selector: "textarea.thread",
	theme: "modern",
	height: 300,
	width: "100%",
	plugins: "paste searchreplace emoticons link image textcolor charmap media preview",
	toolbar1: "styleselect | fontselect | fontsizeselect | bullist numlist | outdent indent hr | undo redo",
	toolbar2: "bold italic underline | cut copy paste pastetext pasteword | search replace | link unlink charmap | emoticons image media | forecolor backcolor | preview",
	resize: "both",
	menubar: false,
});

tinyMCE.init({
	selector: "textarea.message",
	theme: "modern",
	height: 200,
	width: "100%",
	resize: "both",
	plugins: "paste searchreplace emoticons link image textcolor charmap media preview",
	toolbar1: "styleselect | fontselect | fontsizeselect | bullist numlist | outdent indent hr | undo redo",
	toolbar2: "bold italic underline | cut copy paste pastetext pasteword | search replace | link unlink charmap | emoticons image media | forecolor backcolor | preview",
	menubar: false,
});

tinyMCE.init({
	selector: "textarea.request",
	theme: "modern",
	height: 300,
	width: 750,
	plugins: "paste searchreplace emoticons link image textcolor charmap media preview",
	toolbar1: "styleselect | fontselect | fontsizeselect | bullist numlist | outdent indent hr | undo redo",
	toolbar2: "bold italic underline | cut copy paste pastetext pasteword | search replace | link unlink charmap | emoticons image media | forecolor backcolor | preview",
	resize: "both",
	menubar: false,
});

tinyMCE.init({
	selector: "textarea.response",
	theme: "modern",
	height: 100,
	width: 640,
	plugins: "paste searchreplace emoticons link image textcolor charmap media preview",
	toolbar1: "styleselect | fontselect | fontsizeselect | bullist numlist | outdent indent hr | undo redo",
	toolbar2: "bold italic underline | cut copy paste pastetext pasteword | search replace | link unlink charmap | emoticons image media | forecolor backcolor | preview",
	menubar: false,
});

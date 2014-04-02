tinyMCE.init({
	selector: "textarea.thread",
	theme: "modern",
	height: 300,
	width: 750,
	plugins: "paste searchreplace emoticons link image textcolor code visualchars charmap",
	toolbar1: "bold italic underline strikethrough | alignleft aligncenter alignright | bullist numlist | outdent indent hr | undo redo | forecolor backcolor",
	toolbar2: "cut copy paste pastetext pasteword | search replace | link unlink charmap | blockquote subscript superscript | emoticons link image visualchars charmap",
	resize: "both",
	menubar: false,
});

tinyMCE.init({
	selector: "textarea.message",
	theme: "modern",
	height: 300,
	width: 640,
	plugins: "paste searchreplace emoticons link image textcolor code visualchars charmap",
	toolbar1: "bold italic underline strikethrough | alignleft aligncenter alignright | bullist numlist | outdent indent hr | undo redo | forecolor backcolor",
	toolbar2: "cut copy paste pastetext pasteword | search replace | link unlink charmap | blockquote subscript superscript | emoticons link image visualchars charmap",
	menubar: false,
});

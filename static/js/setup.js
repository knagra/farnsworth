/* Project: Farnsworth
 * Author: Karandeep Singh Nagra
 * 
 * Do some setup used everywhere in Farnsworth
 */
   <!-- prevent multiple form submissions by disabling submit button on all forms after post -->
	$("form").submit(function() {
		$(this).submit(function() {
			return false;
		});
		return true;
	});
<!-- add Bootstrap form control to select elements -->
	$("input[type=text]").addClass("form-control");
	$("input[type=password]").addClass("form-control");
	$("select").addClass("form-control");

<!-- change display format for some things depending on window width -->
	$(window).ready(function() {
		var wi = $(window).width();
		if (wi <= 300) {
			$(".large_title").css("font-size", "39%");
			$(".medium_title").css("font-size", "55%");
			$(".small_title").css("font-size", "75%");
			$("#bottom").html('Click: <a class="footer_link" href="mailto:{{ ADMIN.1 }}">E-mail for support</a>.');
		} else if (wi <= 380) {
			$(".large_title").css("font-size", "45%");
			$(".medium_title").css("font-size", "75%");
			$(".small_title").css("font-size", "85%");
			$("#bottom").html('Click: <a class="footer_link" href="mailto:{{ ADMIN.1 }}">E-mail for support</a>.');
		} else if (wi <= 440) {
			$(".large_title").css("font-size", "55%");
			$(".medium_title").css("font-size", "85%");
			$(".small_title").css("font-size", "100%");
			$("#bottom").html('Click: <a class="footer_link" href="mailto:{{ ADMIN.1 }}">E-mail for support</a>.');
		} else if (wi <= 480) {
			$(".large_title").css("font-size", "75%");
			$(".medium_title").css("font-size", "100%");
			$(".small_title").css("font-size", "100%");
			$("#bottom").html('Click: <a class="footer_link" href="mailto:{{ ADMIN.1 }}">E-mail for support</a>.');
		} else if (wi <= 550) {
			$(".large_title").css("font-size", "85%");
			$(".medium_title").css("font-size", "100%");
			$(".small_title").css("font-size", "100%");
			$("#bottom").html('For support, click to e-mail: <a class="footer_link" href="mailto:{{ ADMIN.1 }}">{{ ADMIN.0 }}</a>.');
		} else if (wi <= 768) {
			$(".large_title").css("font-size", "100%");
			$(".medium_title").css("font-size", "100%");
			$(".small_title").css("font-size", "100%");
			$("#bottom").html('For support, click to e-mail: <a class="footer_link" href="mailto:{{ ADMIN.1 }}">{{ ADMIN.0 }}</a>.');
		} else if (wi > 768) {
			$(".large_title").css("font-size", "100%");
			$(".medium_title").css("font-size", "100%");
			$(".small_title").css("font-size", "100%");
			$("#bottom").html('Powered by <a class="footer_link" href="http://www.python.org" target="_blank">Python</a> and <a class="footer_link" href="https://www.djangoproject.com" target="_blank">Django</a>.  Contact {{ ADMIN.0 }} (<a class="footer_link" href="mailto:{{ ADMIN.1 }}">{{ ADMIN.1 }}</a>) for support.');
		}
		
		$(window).resize(function() {
			var wi = $(window).width();
			if (wi <= 300) {
				$(".large_title").css("font-size", "39%");
				$(".medium_title").css("font-size", "55%");
				$(".small_title").css("font-size", "75%");
				$("#bottom").html('Click: <a class="footer_link" href="mailto:{{ ADMIN.1 }}">E-mail for support</a>.');
			} else if (wi <= 380) {
				$(".large_title").css("font-size", "45%");
				$(".medium_title").css("font-size", "75%");
				$(".small_title").css("font-size", "85%");
				$("#bottom").html('Click: <a class="footer_link" href="mailto:{{ ADMIN.1 }}">E-mail for support</a>.');
			} else if (wi <= 440) {
				$(".large_title").css("font-size", "55%");
				$(".medium_title").css("font-size", "85%");
				$(".small_title").css("font-size", "100%");
				$("#bottom").html('Click: <a class="footer_link" href="mailto:{{ ADMIN.1 }}">E-mail for support</a>.');
			} else if (wi <= 480) {
				$(".large_title").css("font-size", "75%");
				$(".medium_title").css("font-size", "100%");
				$(".small_title").css("font-size", "100%");
				$("#bottom").html('Click: <a class="footer_link" href="mailto:{{ ADMIN.1 }}">E-mail for support</a>.');
			} else if (wi <= 550) {
				$(".large_title").css("font-size", "85%");
				$(".medium_title").css("font-size", "100%");
				$(".small_title").css("font-size", "100%");
				$("#bottom").html('For support, click to e-mail: <a class="footer_link" href="mailto:{{ ADMIN.1 }}">{{ ADMIN.0 }}</a>.');
			} else if (wi <= 768) {
				$(".large_title").css("font-size", "100%");
				$(".medium_title").css("font-size", "100%");
				$(".small_title").css("font-size", "100%");
				$("#bottom").html('For support, click to e-mail: <a class="footer_link" href="mailto:{{ ADMIN.1 }}">{{ ADMIN.0 }}</a>.');
			} else if (wi > 768) {
				$(".large_title").css("font-size", "100%");
				$(".medium_title").css("font-size", "100%");
				$(".small_title").css("font-size", "100%");
				$("#bottom").html('Powered by <a class="footer_link" href="http://www.python.org" target="_blank">Python</a> and <a class="footer_link" href="https://www.djangoproject.com" target="_blank">Django</a>.  Contact {{ ADMIN.0 }} (<a class="footer_link" href="mailto:{{ ADMIN.1 }}">{{ ADMIN.1 }}</a>) for support.');
			}
		});
	});

/*
 * Author: ggearloose
 * License: AGPLv3
 */
$(function () {

	function LightSliderPluginViewModel(parameters) {
		//'use strict';
		var self = this;

		self.settings = parameters[0];
		self.control = parameters[1];
		self.loginState = parameters[2];

		self.control.lightIntensity = new ko.observable(100);			//this,
		self.settings.defaultIntensity = new ko.observable(80);	//this,
		self.settings.minIntensity = new ko.observable(0); 		//this,
		self.settings.maxIntensity = new ko.observable(100);		//and this are percents 0 - 100%
		self.settings.notifyDelay = new ko.observable(4000); 	//time in milliseconds
		self.settings.rpi_output = new ko.observable(25);	//decimal number of GPIO Pin

		self.settings.commonTitle = ko.observable(gettext("\n\nThis allows for seamless adjusting of the print bed lighting.\n\nUtilizing PWM function thru GPIO pins and a mosfet."));
		self.settings.defaultTitle = ko.observable(gettext("This is the value the slider will default to when the UI is loaded / refreshed."));
		self.settings.minTitle = ko.observable(gettext("Sets the lowest value you will be able to choose with the slider.") + self.settings.commonTitle());
		self.settings.maxTitle = ko.observable(gettext("Set this <100% if your lighting is too bright on full.") + self.settings.commonTitle());
		self.settings.noticeTitle = ko.observable(gettext("Notifications only apply when setting the intensity via the slider + button in the UI. Set to 0 (zero) to disable notifications."));
		self.settings.rpiTitle = ko.observable(gettext("Set the GPIO Pin you want to use for the pwm signal."));

		self.showNotify = function (self, options) {
			options.hide = true;
			options.title = "Bed Illumination Control";
			options.delay = self.settings.notifyDelay();
			options.type = "info";
			if (options.delay != "0") {
				new PNotify(options);
			}
		};

		self.control.checkSliderValue = ko.pureComputed(function () {
			if (self.control.lightIntensity() < self.settings.minIntensity() && self.control.lightIntensity() != "0") {
				console.log("Bed Illumination Control Plugin: " + self.control.lightIntensity() + "% is less than the minimum intensity (" + self.settings.minIntensity() + "%), increasing.");
				self.control.lightIntensity(self.settings.minIntensity());
				var options = {
					text: gettext('Light intensity increased to meet minimum intensity requirement.'),
					addclass:  'light_intensity_notice_low',
				}
				if ($(".light_intensity_notice_low").length <1) {
					self.showNotify(self, options);
				}
			}
			else if (self.control.lightIntensity() > self.settings.maxIntensity()) {
				console.log("Bed Illumination Control Plugin: " + self.control.lightIntensity() + "% is more than the maximum intensity (" + self.settings.maxIntensity() + "%), decreasing.");
				self.control.lightIntensity(self.settings.maxIntensity());
				var options = {
					text: gettext('Light intensity decreased to meet maximum intensity requirement.'),
					addclass:  'light_intensity_notice_high',
				}
				if ($(".light_intensity_notice_high").length <1) {
					self.showNotify(self, options);
				}
			}
		});

		//send apirequest
		self.control.sendPwmRequest = function(data){
			$.ajax({
			url: API_BASEURL + "plugin/octoprint_lightslider",
			type: "POST",
			dataType: "json",
			data: JSON.stringify({
				command: "dim",
				percentage: data
			}),
			contentType: "application/json; charset=UTF-8"
			});
		}

		//send command to dim the led strip
		self.control.lightsDim = function() {
			self.control.checkSliderValue();
			self.control.sendPwmRequest(self.control.lightIntensity())
		}

		//send command to turn off the led strip
		self.control.lightsOut = function() {
			self.control.sendPwmRequest(0)
		}

		//ph34r
		try {
			//for some reason touchui uses "jog general" for the fan controls? Oh well, makes my job easier
			$("#control-jog-general").find("button").eq(0).attr("id", "motors-off");
			$("#control-jog-general").find("button").eq(1).attr("id", "fan-on");
			$("#control-jog-general").find("button").eq(2).attr("id", "fan-off");
			//If not TouchUI
			if ($("#touch body").length == 0) {
				//add new light controls
				$("#control-jog-general").find("button").eq(2).after("\
					<input type=\"number\" style=\"width: 95px\" data-bind=\"slider: {min: 00, max: 100, step: 1, value: lightIntensity, tooltip: 'hide'}\">\
					<button class=\"btn btn-block control-box\" id=\"dim-lights\" data-bind=\"enable: isOperational() && loginState.isUser(), click: function() { $root.lightsDim() }\">" + gettext("Light Intensity") + ":<span data-bind=\"text: lightIntensity() + '%'\"></span></button>\
					<button class=\"btn btn-block control-box\" id=\"lights-out\" data-bind=\"enable: isOperational() && loginState.isUser(), click: function() { $root.lightsOut() }\">" + gettext("Lights out") + "</button>\
				");
			} else {
				//replace touch UI's fan on button with one that sends whatever speed is set in this plugin
				$("#control-jog-general").find("button").eq(2).after("\
					<button class=\"btn btn-block control-box\" id=\"dim-lights\" data-bind=\"enable: isOperational() && loginState.isUser(), click: function() { $root.lightsDim() }\">" + gettext("Set Intensity") + "</button>\
				");
				//also add spin box + button below in its own section, button is redundant but convenient
				$("#control-jog-feedrate").append("\
					<input type=\"number\" style=\"width: 150px\" data-bind=\"slider: {min: 00, max: 100, step: 1, value: lightIntensity, tooltip: 'hide'}\">\
					<button class=\"btn btn-block\" style=\"width: 169px\" data-bind=\"enable: isOperational() && loginState.isUser(), click: function() { $root.lightsDim() }\">" + gettext("Light Intensity:") + "<span data-bind=\"text: lightIntensity() + '%'\"></span></button>\
				");
			}
		}
		catch (error) {
			console.log(error);
		}

		self.updateSettings = function () {
			try {
				self.settings.minIntensity(parseInt(self.settings.settings.plugins.octoprint_lightslider.minIntensity()));
				self.settings.maxIntensity(parseInt(self.settings.settings.plugins.octoprint_lightslider.maxIntensity()));
				self.settings.notifyDelay(parseInt(self.settings.settings.plugins.octoprint_lightslider.notifyDelay()));
				self.settings.rpi_output(parseInt(self.settings.settings.plugins.octoprint_lightslider.rpi_output()));
			}
			catch (error) {
				console.log(error);
			}
		}

		self.onBeforeBinding = function () {
			self.settings.defaultIntensity(parseInt(self.settings.settings.plugins.octoprint_lightslider.defaultIntensity()));
			self.updateSettings();
			//if the default brightness is above or below max/min then set to either max or min
			if (self.settings.defaultIntensity() < self.settings.minIntensity()) {
				self.control.lightIntensity(self.settings.minIntensity());
			}
			else if (self.settings.defaultIntensity() > self.settings.maxIntensity()) {
				self.control.lightIntensity(self.settings.maxIntensity());
			}
			else {
				self.control.lightIntensity(self.settings.defaultIntensity());
			}
		}

		//update settings in case user changes them, otherwise a refresh of the UI is required
		self.onSettingsHidden = function () {
			self.updateSettings();
		}
	}

	OCTOPRINT_VIEWMODELS.push({
		construct: LightSliderPluginViewModel,
		additionalNames: [],
		dependencies: ["settingsViewModel", "controlViewModel", "loginStateViewModel"],
		optional: [],
		elements: []
	});
});
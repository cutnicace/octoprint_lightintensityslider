# coding=utf-8
from __future__ import absolute_import

import RPi.GPIO as GPIO
import re
import octoprint.plugin
from octoprint.server import user_permission

class LighSliderPlugin(octoprint.plugin.StartupPlugin,
					octoprint.plugin.TemplatePlugin,
					octoprint.plugin.SettingsPlugin,
					octoprint.plugin.AssetPlugin,
					octoprint.plugin.SimpleApiPlugin,
					octoprint.plugin.ShutdownPlugin):

	def on_after_startup(self):
		self._logger.info("entering on_after_startup...")
		self.get_settings_updates() #loads saved values from the config.yaml into the variables
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(self.rpi_output, GPIO.OUT)
		self.pwm_instance = GPIO.PWM(self.rpi_output, 800)
		self.pwm_instance.start(self.defaultLightIntensity)
		self.current_pwm_value=self.defaultLightIntensity
		self._logger.info("value of current_pwm_value: " + str(self.current_pwm_value))
		self._logger.info("exiting on_after_startup.")


	def on_shutdown(self):
		self.pwm_instance.stop()
		GPIO.cleanup()

	def get_settings_defaults(self):
		return dict(
			defaultLightIntensity=80,
			rpi_output=21,
			minIntensity=0,
			maxIntensity=100,
			notifyDelay=4000,
		)

	def on_settings_save(self, data):
		s = self._settings
		if "defaultLightIntensity" in data.keys():
			s.setInt(["defaultLightIntensity"], data["defaultLightIntensity"])
		if "notifyDelay" in data.keys():
			s.setInt(["rpi_output"], data["rpi_output"])
		if "minIntensity" in data.keys():
			s.setInt(["minIntensity"], data["minIntensity"])
		if "maxIntensity" in data.keys():
			s.setInt(["maxIntensity"], data["maxIntensity"])
		if "notifyDelay" in data.keys():
			s.setInt(["notifyDelay"], data["notifyDelay"])
		self.get_settings_updates()
		#clean up settings if everything's default
		self.on_settings_cleanup()
		s.save()

	#function stolen...err borrowed :D from types.py @ 1663
	def on_settings_cleanup(self):
		import octoprint.util
		from octoprint.settings import NoSuchSettingsPath

		try:
			config = self._settings.get_all_data(merged=False, incl_defaults=False, error_on_path=True)
		except NoSuchSettingsPath:
			return

		if config is None:
			self._settings.clean_all_data()
			return

		if self.config_version_key in config and config[self.config_version_key] is None:
			del config[self.config_version_key]

		defaults = self.get_settings_defaults()
		diff = octoprint.util.dict_minimal_mergediff(defaults, config)

		if not diff:
			self._settings.clean_all_data()
		else:
			self._settings.set([], diff)

	def get_assets(self):
		return dict(
			js=["js/lightslider.js"],
			css=["css/style.css"]
		)

	def get_template_configs(self):
		return [
			dict(type="settings", custom_bindings=False)
		]

	def get_settings_updates(self):
		self.defaultLightIntensity = self._settings.getInt(["defaultLightIntensity"])
		self.rpi_output = self._settings.getInt(["rpi_output"])
		self.minIntensity = self._settings.getInt(["minIntensity"])
		self.maxIntensity = self._settings.getInt(["maxIntensity"])
		self.notifyDelay = self._settings.getInt(["notifyDelay"])

	def get_api_commands(self):
		return dict(dim=["percentage"])

	def on_api_command(self, command, data):
		self._logger.info("received an api_command: " + str(command) +" , "+ str(data))
		if not user_permission.can():
			from flask import make_response
			return make_response("Insufficient rights", 403)

		if command == 'dim':
			self.pwm_instance.ChangeDutyCycle(data)
			self.current_pwm_value=data
			self._logger.info("changed current_pwm_value: " + str(self.current_pwm_value))

__plugin_name__ = "Illumination Control"
__plugin_version__ = "1.0.0"
__plugin_description__ = "Dim your printbed light with the help of a mosfet and some pwm directly from a slider in the octoprint UI."

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = __plugin_implementation__ = LighSliderPlugin()
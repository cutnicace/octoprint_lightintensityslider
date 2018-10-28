# coding=utf-8
# this plugin was adapted from the fanslider plugin by ntoff
from __future__ import absolute_import

import RPi.GPIO as GPIO
import re
import octoprint.plugin
from octoprint.server import user_permission

class LightSliderPlugin(octoprint.plugin.StartupPlugin,
			octoprint.plugin.TemplatePlugin,
			octoprint.plugin.SettingsPlugin,
			octoprint.plugin.AssetPlugin,
			octoprint.plugin.SimpleApiPlugin,
			octoprint.plugin.ShutdownPlugin):

	def on_after_startup(self):
		self.get_settings_updates() #load saved values from the config.yaml into the variables
		self.setup_pwm(self.rpi_output, self.frequency)

	def on_shutdown(self):
		#clean up after yourself
		self.teardown_pwm()

	def get_settings_defaults(self):
		return dict(
			defaultIntensity=75, #duty cycle
			frequency=800,
			rpi_output=18,
			minIntensity=0,
			maxIntensity=100,
			notifyDelay=4000,
		)

	def on_settings_save(self, data):
		freq = self.frequency #get current values
		pin = self.rpi_output #get current values
		pwm_changed = False   #arm selector
		s = self._settings
		if "defaultIntensity" in data.keys():
			s.setInt(["defaultIntensity"], data["defaultIntensity"])
		if "frequency" in data.keys():
			s.setInt(["frequency"], data["frequency"])
			if s.getInt(["frequency"]) != freq: #compare if value changed
				freq = s.getInt(["frequency"]) #overwrite with new value
				pwm_changed = True #set modifier
		if "rpi_output" in data.keys():
			s.setInt(["rpi_output"], data["rpi_output"])
			if s.getInt(["rpi_output"]) != pin: #compare if value changed
				pin = s.getInt(["rpi_output"]) #overwrite with new value
				pwm_changed = True #set modifier
		if "minIntensity" in data.keys():
			s.setInt(["minIntensity"], data["minIntensity"])
		if "maxIntensity" in data.keys():
			s.setInt(["maxIntensity"], data["maxIntensity"])
		if "notifyDelay" in data.keys():
			s.setInt(["notifyDelay"], data["notifyDelay"])
		self.get_settings_updates()
		#clean up settings if everything's default
		self.on_settings_cleanup()
		#modify pwm_instance if pin or frequency changed
		if (pwm_changed):
			self.modify_pwm_instance(pin, freq)
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
		self.defaultIntensity = self._settings.getInt(["defaultIntensity"])
		self.frequency = self._settings.getInt(["frequency"])
		self.rpi_output = self._settings.getInt(["rpi_output"])
		self.minIntensity = self._settings.getInt(["minIntensity"])
		self.maxIntensity = self._settings.getInt(["maxIntensity"])
		self.notifyDelay = self._settings.getInt(["notifyDelay"])

	def get_api_commands(self):
		return dict(dim=["percentage"])

	def on_api_command(self, command, data):
		self._logger.debug("received an api_command: " + str(command) +" , "+ str(data["percentage"]))
		if not user_permission.can():
			from flask import make_response
			return make_response("Insufficient rights", 403)

		if command == 'dim':
			self.pwm_instance.ChangeDutyCycle(float(data["percentage"]))
			self.current_pwm_value= data["percentage"]
			self._logger.debug("changed current_duty_cycle: " + str(self.current_pwm_value))

	def setup_pwm(self, pin, freq):
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(pin, GPIO.OUT)
		self.pwm_instance = GPIO.PWM(pin, freq)
		self.pwm_instance.start(self.defaultIntensity)
		self.current_pwm_value=self.defaultIntensity
		self._logger.debug("current pwm_setup: duty_cycle " + str(self.current_pwm_value) + ", gpio_pin " + str(pin) +", frequency " + str(freq))

	def teardown_pwm(self):
		self.pwm_instance.stop()
		GPIO.cleanup()
		self._logger.debug("former pwm_instance decomissioned...")

	def modify_pwm_instance(self, pin, freq):
		self.teardown_pwm()
		self.setup_pwm(pin, freq)
		self._logger.debug("pwm_instance modified: gpio_pin " + str(pin) + ", frequency " + str(freq))

__plugin_name__ = "LightSlider"
__plugin_version__ = "1.0.0"
__plugin_description__ = "Dim your printbed light with the help of a mosfet and some pwm directly from a slider in the octoprint UI."

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = LightSliderPlugin()
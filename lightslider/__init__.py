# coding=utf-8
# this plugin was adapted from the fanslider plugin by ntoff
from __future__ import absolute_import

from subprocess import call
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
		self.setup_pwm(self.pwmPin, self.pwmClock)

	def on_shutdown(self):
		#clean up after yourself
		self.teardown_pwm(self.pwmPin)

	def get_settings_defaults(self):
		return dict(
			defaultIntensity=75, #duty cycle
			pwmClock=240,
			pwmPin=18,
			minIntensity=0,
			maxIntensity=100,
			notifyDelay=4000,
		)

	def on_settings_save(self, data):
		clock = self.pwmClock #get current values
		pin = self.pwmPin #get current values
		pwm_changed = False   #arm selector
		s = self._settings
		if "defaultIntensity" in data.keys():
			s.setInt(["defaultIntensity"], data["defaultIntensity"])
		if "pwmClock" in data.keys():
			s.setInt(["pwmClock"], data["pwmClock"])
			if s.getInt(["pwmClock"]) != clock: #compare if value changed
				pwm_changed = True #set modifier
		if "pwmPin" in data.keys():
			s.setInt(["pwmPin"], data["pwmPin"])
			if s.getInt(["pwmPin"]) != pin: #compare if value changed
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
		#modify pwm_instance if pin or clock changed
		if (pwm_changed):
			self.teardown_pwm(pin)
			self.setup_pwm(s.getInt(["pwmPin"]), s.getInt(["pwmClock"]))
			self._logger.debug("pwm output modified: gpio_pin " + str(s.getInt(["pwmPin"])) + ", pwm_clock " + str(s.getInt(["pwmClock"])))
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
		self.pwmClock = self._settings.getInt(["pwmClock"])
		self.pwmPin = self._settings.getInt(["pwmPin"])
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
			call("gpio -g pwm " + str(self.pwmPin) + " " + str(data["percentage"]), shell=True) #pin, duty cycle
			self.current_pwm_value= data["percentage"]
			self._logger.debug("changed current_duty_cycle: " + str(self.current_pwm_value))

	def setup_pwm(self, pin, clock):
		call("gpio -g mode "+ str(pin) + " pwm", shell=True) #using Broadcom numbering scheme setup pin 12 as pwm output
		call("gpio pwm-ms", shell=True) #set for mark:space mode
		call("gpio pwmr 100", shell=True) #set to 100 for 800MHz
		call("gpio pwmc " + str(clock), shell=True) #set to 240 for 800MHz
		call("gpio -g pwm " + str(pin) + " " + str(self.defaultIntensity), shell=True) #pin, duty cycle
		self.current_pwm_value = self.defaultIntensity
		self._logger.debug("current pwm_setup: duty_cycle " + str(self.current_pwm_value) + ", gpio_pin " + str(pin) +", pwm_clock " + str(clock))

	def teardown_pwm(self, pin):
		call("gpio -g mode " + str(pin) + " in", shell=True)
		self._logger.debug("reset former pwm_pin " + str(pin) + " pin_mode back to INPUT." )

__plugin_name__ = "LightSlider"
__plugin_version__ = "1.1.0"
__plugin_description__ = "Dim your printbed light with the help of a mosfet and some pwm directly from a slider in the octoprint UI."

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = LightSliderPlugin()
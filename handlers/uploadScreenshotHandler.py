import os
import sys
import traceback

import tornado.gen
import tornado.web
from raven.contrib.tornado import SentryMixin
from PIL import Image

from common.log import logUtils as log
from common.ripple import userUtils
from common.web import requestsManager
from constants import exceptions
from common import generalUtils
from objects import glob
from common.sentry import sentry

MODULE_NAME = "screenshot"
class handler(requestsManager.asyncRequestHandler):
	"""
	Handler for /web/osu-screenshot.php
	"""
	@tornado.web.asynchronous
	@tornado.gen.engine
	@sentry.captureTornado
	def asyncPost(self):
		try:
			if glob.debug:
				requestsManager.printArguments(self)

			# Make sure screenshot file was passed
			if "ss" not in self.request.files:
				raise exceptions.invalidArgumentsException(MODULE_NAME)

			# Check user auth because of sneaky people
			if not requestsManager.checkArguments(self.request.arguments, ["u", "p"]):
				raise exceptions.invalidArgumentsException(MODULE_NAME)
			username = self.get_argument("u")
			password = self.get_argument("p")
			ip = self.getRequestIP()
			userID = userUtils.getID(username)
			if not userUtils.checkLogin(userID, password):
				raise exceptions.loginFailedException(MODULE_NAME, username)
			if userUtils.check2FA(userID, ip):
				raise exceptions.need2FAException(MODULE_NAME, username, ip)

			# Rate limit
			if glob.redis.get("lets:screenshot:{}".format(userID)) is not None:
				self.write("no")
				return
			glob.redis.set("lets:screenshot:{}".format(userID), 1, 60)

			# Get a random screenshot id
			found = False
			screenshotID = ""
			while not found:
				screenshotID = generalUtils.randomString(8)
				if not os.path.isfile(".data/screenshots/{}.png".format(screenshotID)):
					found = True

			# Write screenshot file to .data folder
			with open(".data/screenshots/{}.png".format(screenshotID), "wb") as f:
				f.write(self.request.files["ss"][0]["body"])

			# Add Akatsuki's watermark
			base_screenshot = Image.open('.data/screenshots/{}.png'.format(screenshotID))
			watermark = Image.open('constants/watermark.png')
			width, height = base_screenshot.size

			position = (width - 330, height - 200)

			transparent = Image.new('RGBA', (width, height), (0,0,0,0))
			transparent.paste(base_screenshot, (0,0))
			transparent.paste(watermark, position, mask=watermark)
			transparent.show()
			transparent.save('.data/screenshots/{}.png'.format(screenshotID))

			# Output
			log.info("New screenshot ({})".format(screenshotID))

			# Return screenshot link
			self.write("{}/ss/{}.png".format(glob.conf.config["server"]["servername"], screenshotID))
		except exceptions.need2FAException:
			pass
		except exceptions.invalidArgumentsException:
			pass
		except exceptions.loginFailedException:
			pass
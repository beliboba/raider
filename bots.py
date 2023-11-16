import asyncio
import logging
import random

from playwright.async_api import async_playwright, Page, Browser, Playwright, expect


class Bot:
	playwright = None
	browser = None
	page = None

	async def set_username(self):
		username_input = self.page.locator(
			"//*[@id='premeeting-name-input']"
		)
		for letter in list(self.username):
			await username_input.press(letter)

	async def join(self):
		try:
			locator = self.page.locator(
				"//*[@id='react']/div[3]/div[3]/div/div[3]/button[1]"
			)
			await expect(locator).to_be_visible(timeout=100)
			await locator.click(timeout=100)
		except AssertionError:
			pass

		join_button = self.page.locator(
			"//*[@id='videoconference_page']/div[4]/div[1]/div/div/div[1]/div[2]/div/div"
		)
		try:
			checkbox = self.page.locator(
				"//*[@id='videoconference_page']/div[4]/div[1]/div/div/label"
			)
			await checkbox.check(force=True)
		except AssertionError:
			pass
		
		await join_button.click()

	async def open_chat(self):
		await self.page.mouse.move(640, 360)
		chat_button = self.page.locator(
			"//*[@id='new-toolbox']/div/div/div/div[4]"
		)
		await chat_button.click()

	async def send_chat_message(self, message: str):
		chat_input = self.page.locator(
			"//*[@id='chat-input-messagebox']"
		)

		await chat_input.fill(message)

		send_button = self.page.locator(
			"//*[@id='chat-input']/button"
		)
		await send_button.click()

	async def spam_messages(self, amount: int):
		if amount == 0:
			return

		while not await self.page.locator("//*[@id='sideToolbarContainer']").is_visible():
			await self.open_chat()

		async def send_randomly():
			for _ in range(0, amount):
				await self.send_chat_message(random.choice(self.message_list))
				await asyncio.sleep(0.1)

		async def send_all():
			for i in range(0, amount):
				if amount > len(self.message_list) - 1:
					i = -1
				await self.send_chat_message(self.message_list[i])
				await asyncio.sleep(0.1)

		if amount == -1:
			if self.messages_random:
				while True:
					await send_randomly()
			else:
				while True:
					await send_all()
		else:
			await send_all()

	async def kick_users(self):
		while not await self.page.locator("//*[@id='layout_wrapper']/div[3]").is_visible():
			await self.page.locator("//*[@id='new-toolbox']/div/div/div/div[6]/div/div/div").click()  # Opening participants pane
		participants_list = await self.page.locator("//*[@id='layout_wrapper']/div[2]/div[2]/div[3]/div").all()
		for participant in participants_list:
			try:
				if (
					await participant.locator("./div[2]/div[1]/div/span").is_visible()
					or self.hidden_username in await participant.locator("./div[2]/div[1]/div/div").text_content()
				):
					continue

				await participant.hover()
				await self.page.locator("./div[2]/div[3]/button[2]").click()
				await self.page.locator("//div[aria-label='Отключить']").click()
			except:
				pass
		await asyncio.sleep(random.randint(1, 3))
		await self.kick_users()

	async def start(self):
		async with async_playwright() as p:
			self.browser = await p.chromium.launch(
				headless=False,
				args=['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream']
			)
			self.page = await self.browser.new_page()
			await self.page.goto(self.url)

			await self.set_username()
			await self.toggle("mic", self.mic_switch)
			await self.toggle("cam", self.cam_switch)
			await self.join()
			if self.yt:
				await self.play_video()
			if self.kick:
				asyncio.ensure_future(self.kick_users())

			asyncio.ensure_future(self.spam_messages(self.message_num))
			while True:
				await self.page.wait_for_timeout(300)

	async def toggle(self, toggle: str, state: bool):
		mapping = {
			"mic": 1,
			"cam": 2
		}
		switch = self.page.locator(
			f"//*[@id='new-toolbox']/div/div/div/div[{mapping[toggle]}]"
		)
		current_state = bool(switch.locator(
			"./div/div/div[1]"
		).get_attribute("aria-pressed"))

		if current_state != state:
			await switch.click()

	async def play_video(self):
		await self.page.locator("//*[@id='new-toolbox']/div/div/div/div[8]/div/div/div/div").click()
		play_button_available = False
		while not play_button_available:
			try:
				await self.page.locator("//*[@id='overflow-context-menu']/div/div[3]/div[1]").click()
				await self.page.locator("///*[@id='shared-video-url-input']").fill(self.yt_url)
				await self.page.locator("//*[@id='modal-dialog-ok-button'']").click()
			except:
				await asyncio.sleep(1)

	def __init__(
			self,
			url: str,
			username: str,
			hidden_username: str,
			message_list: list,
			message_num: int,
			messages_random: bool,
			kick: bool,
			mute: bool,
			disable_cam: bool,
			yt_url: str = None,
			mic_switch: bool = False,
			cam_switch: bool = False,
			yt: bool = False
	):
		self.url = url
		self.username = username
		self.hidden_username = hidden_username

		self.message_list = message_list
		self.message_num = message_num
		self.messages_random = messages_random

		self.kick = kick
		self.mute = mute
		self.disable_cam = disable_cam

		self.yt_url = yt_url
		self.yt = yt

		self.mic_switch = mic_switch
		self.cam_switch = cam_switch

		self.playwright: Playwright
		self.browser: Browser
		self.page: Page


async def start(data: dict):
	bots = []

	print("created browser")

	for i in range(0, data["bot_num"]):
		username = data['username']
		if data["add_numbers"]:
			username += f"{i+1}"

		if data["yt"]:
			yt_url = data["yt_url"]
		else:
			yt_url = None

		bot = Bot(
			data["url"],
			username,
			data["username"],
			data["messages"].splitlines(),
			data["message_num"],
			data["messages_random"],
			data["kick"],
			data["mute"],
			data["disable_cam"],
			yt_url,
			data["mic_switch"],
			data["cam_switch"],
			data["yt"]
		)
		bots.append(bot)

	return bots

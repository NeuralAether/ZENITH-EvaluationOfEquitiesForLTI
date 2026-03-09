import time
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import warnings
import os


class SimpleCrawler:
	def __init__(self, headless: bool = True):
		options = webdriver.ChromeOptions()
		if headless:
			options.add_argument("--headless=new")
		if not headless:
			warnings.warn("Running in non-headless mode may cause issues with some websites that detect automation (and scroll bar cannot be interacted with properly). Use headless mode for better compatibility.")
		self.driver = webdriver.Chrome(options=options)
		self.soup = None

	def load_website(self, url: str) -> dict:
		self.driver.get(url)
		self.soup = BeautifulSoup(self.driver.page_source, "html.parser")
		return {
			"url": self.driver.current_url,
			"title": self.driver.title,
			"soup": self.soup
		}

	def close(self) -> None:
		self.driver.quit()

class MacrotrendsCrawler(SimpleCrawler): 
	def __init__(self, headless = True):
		super().__init__(headless)
		self.data = None
		self.ticker = None
		self.company = None
		self.document = None
		self.frequency = None
	
	def load_website(self, ticker, company, document, frequency = "Q", simplify=True, **kwargs):
		url = f"https://www.macrotrends.net/stocks/charts/{ticker}/{company}/{document}?freq={frequency}"
		res = super().load_website(url)
		# Remove privacy banner if exists
		self.__click_reject_all_button(kwargs.get("reject_button_delay", 2)	)
		# Check if something to correct
		scroll_bar_id = kwargs.get("scroll_bar_id", None)
		if simplify and scroll_bar_id is not None:
			# Check if scroll bar ID provided
			scroll = -1
			while scroll != 0:  # Try scrolling multiple times to ensure all content is loaded
				# Update soup after scrolling
				self.__build_table_chunk()
				scroll_bar = self.__scroller_definition(scroll_bar_id)
				scroll = self.__scroll(scroll_bar, offset_x=kwargs.get("scroll_offset_x", 100), offset_y=kwargs.get("scroll_offset_y", 0))  # Scroll right by 100 pixels
				res["soup"] = BeautifulSoup(self.driver.page_source, "html.parser")
		self.__build_table_chunk()
		scroll_bar = self.__scroller_definition(scroll_bar_id)
		scroll = self.__scroll(scroll_bar, offset_x=kwargs.get("scroll_offset_x", -4000), offset_y=kwargs.get("scroll_offset_y", 0))  # Scroll right by 100 pixels
		self.close() 
		# Set vars 
		self.ticker = ticker
		self.company = company
		self.document = document
		self.frequency = frequency
		# Set data
		return res
	
	def __click_reject_all_button(self, delay):
		time.sleep(delay)
		try:
			# Try multiple text variations (case-insensitive)
			xpaths = [
				"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'reject all')]",
				"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'reject all')]",
				"//button[contains(@class, 'Button') and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'reject')]"
			]
			
			reject_button = None
			for xpath in xpaths:
				try:
					reject_button = self.driver.find_element(By.XPATH, xpath)
					if reject_button:
						break
				except:
					continue
			
			if reject_button:
				reject_button.click()
			else:
				print("Reject All button not found after trying multiple selectors")
				self.driver.close() 
		except Exception as e:
			print(f"Reject All button could not be clicked: {e}")
			self.driver.close()
	
	def __scroller_definition(self, scroll_bar_id): 
		try:
			scroll_bar = WebDriverWait(self.driver, 10).until(
				EC.presence_of_element_located((By.ID, scroll_bar_id))
			)
			return scroll_bar
		except Exception:
			raise ValueError(f"Scroll bar with ID {scroll_bar_id} not found.")
		
	def __scroll(self, scroll_bar, offset_x=50, offset_y=0):
		# Scroll element into view first
		self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", scroll_bar)
		time.sleep(0.3)
		
		curr_x = scroll_bar.location['x']
		actions = ActionChains(self.driver)
		actions.move_to_element(scroll_bar)
		actions.pause(0.2)
		actions.click_and_hold(scroll_bar)
		actions.pause(0.1)
		actions.move_by_offset(offset_x, offset_y)
		actions.pause(0.1)
		actions.release()
		actions.perform()
		
		# Wait for browser to update element position
		time.sleep(0.5)
		new_x = scroll_bar.location['x']
		return new_x - curr_x
	
	def __build_table_chunk(self):
		soup = BeautifulSoup(self.driver.page_source, "html.parser")
		cols = [s.text.strip() for h in soup.select('[role=columnheader]') if (s := h.find('span')) and '-' in s.text]
		rows = {}
		for r in soup.select('[role=row]'):
			cells = r.select('[role=gridcell]')
			if len(cells) > 2:
				rows[cells[0].get_text(strip=True)] = [c.get_text(strip=True) for c in cells[2:]]
		df = pd.DataFrame(rows, index=cols).T
		self.data = df if self.data is None else self.data.combine_first(df)
		
	def save_data(self, rep = "__data/"):
		folder_name = f"{rep}{self.company}/{self.ticker}"
		# Create folder if it doesn't exist
		if not os.path.exists(folder_name):
			os.makedirs(folder_name)
		# Dates between and save
		dates_in_data_between = f"{self.data.columns[0].rsplit('-')[0]}_{self.data.columns[-1].rsplit('-')[0]}"
		filename = f"{folder_name}/{self.document}_{self.frequency}_{dates_in_data_between}.csv"
		if self.data is not None:
			self.data.to_csv(filename)
		else:
			print("No data to save.")
from selenium import webdriver


class DriverFactory:
    @staticmethod
    def get_driver(browser_name: str, headless: bool = False):
        browser_name = browser_name.lower()
        if browser_name == "chrome":
            options = webdriver.ChromeOptions()
            if headless:
                options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")  # Standard size
            # Selenium Manager resolves the driver when it is not on PATH.
            return webdriver.Chrome(options=options)
        elif browser_name == "firefox":
            options = webdriver.FirefoxOptions()
            if headless:
                options.add_argument("--headless")
            options.add_argument("--width=1920")
            options.add_argument("--height=1080")
            # Selenium Manager resolves the driver when it is not on PATH.
            return webdriver.Firefox(options=options)
        elif browser_name == "edge":
            options = webdriver.EdgeOptions()
            if headless:
                options.add_argument("--headless")  # Edge uses "headless" too
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
            # Selenium Manager resolves the driver when it is not on PATH.
            return webdriver.Edge(options=options)
        else:
            raise ValueError(f"Browser '{browser_name}' is not supported or implemented yet.")

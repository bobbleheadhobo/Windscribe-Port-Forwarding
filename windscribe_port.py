import sys
import os
import logging
import time
import requests
from dotenv import load_dotenv
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import qbittorrentapi


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('windscribe_port_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when required configuration is missing"""
    pass


class WindscribePortManager:
    """Manages Windscribe ephemeral port forwarding"""
    
    
    def __init__(self):
        """Initialize the port manager and load configuration"""
        logger.info("\n" * 3)
        logger.info("=" * 60)
        logger.info("Starting Windscribe Port Manager")
        logger.info("=" * 60)

        load_dotenv()
        self.config = self._load_config()
        self.browser = None
        

    def _load_config(self) -> dict:
        """Load and validate environment variables"""
        logger.info("Loading configuration from environment variables")
        
        required_vars = [
            'ws_username', 'ws_password',
            'qbt_username', 'qbt_password', 'qbt_host', 'qbt_port',
            'discord_webhook_url'
        ]
        
        config = {}
        missing_vars = []
        
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
            config[var] = value
            
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
            
        logger.info("Configuration loaded successfully")
        return config
    

    def _init_browser(self):
        """Initialize Chrome browser"""
        logger.info("Initializing Chrome browser")
        
        try:
            self.browser = Driver(uc=True, browser='chrome')
            logger.info("Browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise
    

    def _wait_for_element(self, by: By, value: str, timeout: int = 20):
        """Wait for element to be present and return it"""
        try:
            element = WebDriverWait(self.browser, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            logger.error(f"Timeout waiting for element: {value}")
            raise
    

    def _wait_for_clickable(self, by: By, value: str, timeout: int = 20):
        """Wait for element to be clickable and return it"""
        try:
            element = WebDriverWait(self.browser, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except TimeoutException:
            logger.error(f"Timeout waiting for clickable element: {value}")
            raise
    

    def get_windscribe_port(self) -> str:
        """
        Login to Windscribe and request an ephemeral port
        
        Returns:
            str: The acquired port number
            
        Raises:
            Exception: If login fails or port cannot be acquired
        """
        logger.info("Starting Windscribe port fetcher")
        
        try:
            self._init_browser()
            
            # Navigate to login page
            logger.info("Navigating to Windscribe login page")
            self.browser.get('https://windscribe.com/login')

            '''
            # Check for Cloudflare challenge
            # cant scrape the cloudflare page for some reason
            try:
                captcha = self._wait_for_element(By.XPATH, '//*[@id="challenge-success-text"]', timeout=5)
            except Exception:
                captcha = None

            if captcha:
                logger.info("Cloudflare challenge detected")
                try:
                    username_field = self._wait_for_element(By.XPATH, '//*[@id="username"]', timeout=45)
                    if username_field:
                        logger.info("Cloudflare challenge bypassed")
                except Exception:
                    raise Exception("Failed to bypass Cloudflare challenge")
            '''     

            time.sleep(1)
            if ('cloudflare-challenge' in self.browser.page_source.lower()):
                logger.info("Cloudflare challenge detected")
                try:
                    username_field = self._wait_for_element(By.XPATH, '//*[@id="username"]', timeout=45)
                    if username_field:
                        logger.info("Cloudflare challenge bypassed")
                except Exception:
                    raise Exception("Failed to bypass Cloudflare challenge")   

            try:
                # Wait for and fill username
                logger.info("Entering credentials")
                username_field = self._wait_for_element(By.XPATH, '//*[@id="username"]', timeout=45) 
                username_field.send_keys(self.config['ws_username'])
                
                # Fill password and submit
                password_field = self._wait_for_element(By.XPATH, '//*[@id="pass"]')
                password_field.send_keys(self.config['ws_password'])
                password_field.submit()
                
                logger.info("Login submitted, waiting for authentication")
                
                # Wait for successful login by checking for account page element
                self._wait_for_element(By.ID, "menu-account")
                logger.info("Successfully logged into Windscribe")
            except TimeoutException:
                login_error = self._wait_for_element(By.XPATH, '//*[@id="loginform"]/div/div[1]', timeout=10)
                error_msg = f"Login failed because {login_error.text}" if login_error else "timeout exceeded"
                raise Exception(error_msg)
            
            # Navigate to ephemeral port page
            logger.info("Navigating to ephemeral port page")
            self.browser.get('https://windscribe.com/myaccount#porteph')
            
            # Wait for port management section to load
            self._wait_for_element(By.ID, 'request-port-cont', timeout=15)
            
            # Check if we need to delete existing port
            delete_button = self._wait_for_clickable(By.XPATH, '//*[@id="request-port-cont"]/button')
            
            button_text = delete_button.text
            logger.info(f"Port button text: {button_text}")
            
            if button_text == "Delete Port":
                logger.info("Deleting existing port")
                delete_button.click()
                
                # Wait for deletion to complete
                WebDriverWait(self.browser, 30).until(EC.text_to_be_present_in_element((By.XPATH, '//*[@id="request-port-cont"]/button'),"Request Matching Port"))
                logger.info("Existing port deleted")
            
            # Request new port
            logger.info("Requesting new ephemeral port")
            request_button = self._wait_for_clickable(By.XPATH,"//button[normalize-space()='Request Matching Port']")
            request_button.click()
            
            # Wait for port to be displayed
            port_element = self._wait_for_element(By.XPATH,'//div[@id="epf-port-info"]//span[1]',timeout=15)
            port = port_element.text.strip()
            
            # Validate port
            if not port.isdigit():
                raise ValueError(f"Invalid port received: {port}")
                
            logger.info(f"Successfully acquired port: {port}")
            return port
            
        except TimeoutException as e:
            error_msg = "Timeout while acquiring Windscribe port"
            logger.error(error_msg)
            raise Exception(error_msg) from e
            
        except Exception as e:
            logger.error(e)
            raise
            
        finally:
            if self.browser:
                img_dir = os.path.join(os.getcwd(), 'img')
                os.makedirs(img_dir, exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                screenshot_path = os.path.join(img_dir, f"windscribe_{timestamp}.png")
                try:
                    self.browser.save_screenshot(screenshot_path)
                except WebDriverException as e:
                    logger.error(f"Failed to capture screenshot: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error while saving screenshot: {e}")
                logger.info("Closing browser")
                self.browser.quit()
    

    def update_qbittorrent_port(self, port: str) -> bool:
        """
        Update qBittorrent listening port
        
        Args:
            port: The port number to set
            
        Returns:
            bool: True if successful
            
        Raises:
            Exception: If connection or update fails
        """
        logger.info(f"Updating qBittorrent port to {port}")
        
        try:
            # Connect to qBittorrent
            client = qbittorrentapi.Client(
                host=self.config['qbt_host'],
                port=self.config['qbt_port'],
                username=self.config['qbt_username'],
                password=self.config['qbt_password']
            )
            
            # Attempt login
            try:
                client.auth_log_in()
                logger.info("Successfully authenticated with qBittorrent")
            except qbittorrentapi.LoginFailed as e:
                error_msg = f"qBittorrent login failed: {str(e)}"
                logger.error(error_msg)
                raise Exception(error_msg) from e
            
            # Update port
            prefs = client.application.preferences
            prefs['listen_port'] = int(port)
            client.app.preferences = prefs
            
            logger.info(f"Successfully set qBittorrent listening port to {port}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to update qBittorrent port: {str(e)}"
            logger.error(error_msg)
            raise
    

    def send_discord_notification(self, message: str, is_error: bool = False):
        """
        Send notification to Discord via webhook
        
        Args:
            message: The message to send
            is_error: Whether this is an error message
        """
        try:
            webhook_url = self.config['discord_webhook_url']
            
            # Format message with emoji based on type
            emoji = "❌" if is_error else "✅"
            formatted_message = f"{emoji} **Windscribe Port Manager**\n{message}"
            
            payload = {
                "content": formatted_message,
                "username": "Windscribe Port Manager"
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Discord notification sent: {message}")
            
        except Exception as e:
            # Don't raise exception for notification failures
            logger.error(f"Failed to send Discord notification: {str(e)}")
    

    def run(self):
        """Main execution method"""
        try:
            # Step 1: Get port from Windscribe
            port = self.get_windscribe_port()
            
            # Step 2: Update qBittorrent
            self.update_qbittorrent_port(port)
            
            # Step 3: Send success notification
            success_message = f"Port forwarding updated successfully!\n\n**New Port:** {port}"
            self.send_discord_notification(success_message, is_error=False)
            
            logger.info("=" * 60)
            logger.info("Windscribe Port Manager completed successfully")
            logger.info("=" * 60)
            
            return 0
            
        except ConfigurationError as e:
            error_message = f"Configuration Error:\n{str(e)}"
            self.send_discord_notification(error_message, is_error=True)
            logger.error("Exiting due to configuration error")
            return 1
            
        except Exception as e:
            error_message = f"Error occurred:\n{str(e)}"
            self.send_discord_notification(error_message, is_error=True)
            logger.error(f"Exiting due to error: {str(e)}")
            return 1




def main():
    """Entry point for the script"""
    try:
        manager = WindscribePortManager()
        sys.exit(manager.run())
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
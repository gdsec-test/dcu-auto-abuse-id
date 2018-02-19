import logging
import signal
from requests import sessions
from selenium import webdriver


class URIHelper:

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def resolves(self, url, timeout=60):
        """
            Returns a boolean indicating whether the site resolves or not
            :param url:
            :param timeout:
            :return:
            NOTE: If we are using auth, requests library will not resend auth on a redirect (will result in a 401),
            so we need to manually check for one and re-issue the get with the redirected url and the auth credentials
            """
        try:
            with sessions.Session() as session:
                bad_site = session.request(method='GET', url=url, timeout=timeout)
                status = str(bad_site.status_code)
                if status[0] in ["1", "2", "3"]:
                    return True
                return status in ["406", "403"]
        except Exception as e:
            self._logger.error(
                "Error in determining if url resolves {} : {}".format(
                    url, e.message))
            return False

    def get_site_data(self, url, timeout=10):
        """
        Returns a tuple consisting of screenshot, and sourcecode for the url in question
        :param url:
        :param timeout:
        :return:
        """
        data = (None, None)
        try:
            browser = webdriver.PhantomJS()
            browser.set_page_load_timeout(timeout)
            browser.get(url)
            screenshot = browser.get_screenshot_as_png()
            sourcecode = browser.page_source.encode('ascii', 'ignore')
            data = (screenshot, sourcecode)
            return data
        except Exception as e:
            self._logger.error("Error while taking snapshot and/or source code for {}: {}".format(url, e))
        finally:
            try:
                browser.service.process.send_signal(signal.SIGTERM)
                browser.quit()
            except Exception:
                pass
        return data

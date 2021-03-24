from datetime import datetime, timedelta
import json
import logging
import os
from requests.auth import AuthBase
import requests.packages.urllib3
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from urllib.parse import urljoin


class HubAuth(AuthBase):
    """Base class for Hub authentication mechanisms"""
    def __init__(self, session):
        self._session = session  # for authenticating
        self._last_authentication = None
        self._bearer_token = None

    def __call__(self, r):
        if not self._last_authentication:
            self.authenticate()
            self._last_authentication = datetime.now()
            if not self._session.verify:
                # print warning message on first authentication but
                # disable it on each and every subsequent call
                requests.packages.urllib3.disable_warnings()

        if datetime.now() - self._last_authentication > timedelta(minutes=60):
            logging.info("Re-authenticating to refresh the bearer token")
            self.authenticate()
            self._last_authentication = datetime.now()

        return r

    def authenticate(self):
        raise NotImplementedError("authenticate must be implemented")


class HubAuthToken(HubAuth):
    def __init__(self, session, access_token):
        super().__init__(session)
        self._access_token = access_token
        self._csrf_token = None

    def __call__(self, r):
        super().__call__(r)
        r.headers.update({
            'authorization': "bearer " + self._bearer_token,
            'X-CSRF-TOKEN': self._csrf_token
        })
        return r

    def authenticate(self):
        headers = {'Authorization': "token " + self._access_token}
        response = self._session.post("/api/tokens/authenticate", headers=headers)

        if response.status_code == 200:
            try:
                self._bearer_token = response.json()['bearerToken']
                self._csrf_token = response.headers['X-CSRF-TOKEN']
                return
            except (json.JSONDecodeError, KeyError):
                logging.exception("HTTP response status code 200 but unable to obtain bearer token")
                # fall through

        if response.status_code == 401:
            logging.error("HTTP response status code = 401 (Unauthorized)")
            try:
                logging.error(response.json()['errorMessage'])
            except (json.JSONDecodeError, KeyError):
                logging.exception("unable to extract error message")
                logging.error("HTTP response headers: %s", response.headers)
                logging.error("HTTP response text: %s", response.text)
            raise RuntimeError("Unauthorized access token", response)

        # all unhandled responses fall through to here
        logging.error("Unhandled HTTP response")
        logging.error("HTTP response status code %i", response.status_code)
        logging.error("HTTP response headers: %s", response.headers)
        logging.error("HTTP response text: %s", response.text)
        raise RuntimeError("Unhandled HTTP response", response)


class HubAuthPassword(HubAuth):
    def __init__(self, session, username, password):
        super().__init__(session)
        self._username = username
        self._password = password

    def __call__(self, r):
        super().__call__(r)
        r.headers.update({'authorization': "bearer " + self._bearer_token})
        return r

    def authenticate(self):
        credentials = {'j_username': self._username, 'j_password': self._password}
        response = self._session.post("/j_spring_security_check", credentials)

        if response.status_code == 204:  # No Content
            try:
                cookie = response.headers['Set-Cookie']
                self._bearer_token = cookie[cookie.index('=')+1:cookie.index(';')]
                return
            except (KeyError, ValueError):
                logging.exception("HTTP response status code 204 but unable to obtain bearer token")
                # fall through

        if response.status_code == 401:
            logging.error("HTTP response status code = 401 (Unauthorized)")
            try:
                logging.error(response.json()['errorMessage'])
            except (json.JSONDecodeError, KeyError):
                logging.exception("unable to extract error message")
                logging.error("HTTP response headers: %s", response.headers)
                logging.error("HTTP response text: %s", response.text)
            raise RuntimeError("Unauthorized username/password", response)

        # all unhandled responses fall through to here
        logging.error("Unhandled HTTP response")
        logging.error("HTTP response status code %i", response.status_code)
        logging.error("HTTP response headers: %s", response.headers)
        logging.error("HTTP response text: %s", response.text)
        raise RuntimeError("Unhandled HTTP response", response)


class HubSession(requests.Session):
    """Hold urlbase, timeout, and provide sensible defaults"""

    def __init__(self, urlbase, timeout, verify):
        super().__init__()
        self.urlbase = urlbase
        self._timeout = timeout  # timeout is not a member of requests.Session
        self.verify = verify

        # use sane defaults to handle unreliable networks
        """HTTP response status codes:
                429 = Too Many Requests
                500 = Internal Server Error
                502 = Bad Gateway
                503 = Service Unavailable
                504 = Gateway Timeout
        """
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,  # exponential retry 1, 2, 4, 8, 16 sec ...
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=['GET']
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.mount("https://", adapter)
        self.mount("http://", adapter)

        self.proxies.update({
            'http': os.environ.get('http_proxy', ''),
            'https': os.environ.get('https_proxy', '')
        })

    def request(self, method, url, **kwargs):
        kwargs['timeout'] = self._timeout
        url = urljoin(self.urlbase, url)
        return super().request(method, url, **kwargs)


class HubCore:
    """Handle some of the more complex details of the REST-API such as:
       - authentication
       - bearer token expiry

       and provide a robust underlying connection:
       - reuse a single requests.Session
       - retries, timeouts, and proxies
       - TLS certificate verification (or lack of)
    """
    def __init__(self, urlbase,
                 access_token=None, access_token_file=None, username=None, password=None,
                 timeout=None, verify=None):
        """Specify named parameters instead of **kwargs to make them more apparent"""
        self.session = HubSession(urlbase, timeout, verify)
        session_for_authenticating = HubSession(urlbase, timeout, verify)  # with no auth attached
        self.session.auth = self.__get_authenticator(session_for_authenticating, access_token, access_token_file, username, password)

    @staticmethod
    def __get_authenticator(session_for_authenticating, access_token=None, access_token_file=None, username=None, password=None):
        """De-tangle the possibilities of specifying credentials"""
        if access_token:
            return HubAuthToken(session_for_authenticating, access_token)
        elif access_token_file:
            tf = open(access_token_file, 'r')
            access_token = tf.readline().strip()
            return HubAuthToken(session_for_authenticating, access_token)
        elif username and password:
            return HubAuthPassword(session_for_authenticating, username, password)
        else:
            raise SystemError("Authentication credentials not specified")

    def execute_get(self, url, **kwargs):
        """Same method declaration as requests.session.get"""
        response = self.session.get(url, **kwargs)
        response.raise_for_status()

        if 'internal' in response.headers['content-type']:
            logging.warning("Response contains internal proprietary content-type: " + response.headers['content-type'])

        try:
            json_result = response.json()
            return json_result
        except json.decoder.JSONDecodeError:
            logging.exception("Caught unexpected JSONDecodeError")
            logging.error("HTTP response status code %i", response.status_code)
            logging.error("HTTP response headers: %s", response.headers)
            logging.error("HTTP response text: %s", response.text)
            raise

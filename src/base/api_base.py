import requests

from src.utils.logger import get_logger

logger = get_logger(__name__)


class APIBase:
    def __init__(self, config: dict):
        self.base_url = config.get("base_api_url", "")
        if not self.base_url:
            logger.error("base_api_url not found in config. API tests may fail.")
        self.session = requests.Session()  # Use a session for cookie persistence
        self.default_timeout = config.get("default_timeout", 10)
        self.config = config  # Store config for auth endpoint if needed
        self.auth_token = None  # To store the auth token

        common_headers = {"Content-Type": "application/json", "Accept": "application/json"}
        self.session.headers.update(common_headers)

    def authenticate(self):
        """Authenticates with Restful-booker and stores the token."""
        self.auth_token = None
        auth_endpoint = self.config.get("api_auth_endpoint")
        api_creds = self.config.get("credentials", {}).get("api_user", {})
        username = api_creds.get("username")
        password = api_creds.get("password")

        if not all([auth_endpoint, username, password]):
            logger.error("API authentication credentials or endpoint not fully configured.")
            return False

        auth_url = f"{self.base_url}{auth_endpoint}"
        payload = {"username": username, "password": password}
        logger.info(f"Attempting API authentication to {auth_url}")
        try:
            response = self.session.post(auth_url, json=payload, timeout=self.default_timeout)
            response.raise_for_status()  # Will raise an HTTPError for bad responses
            token_data = response.json()
            token = token_data.get("token") if isinstance(token_data, dict) else None
            if isinstance(token, str) and token.strip():
                self.auth_token = token
                logger.info("API Authentication successful. Token received.")
                return True
            logger.error("API Authentication failed: response did not contain a valid token.")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"API Authentication request failed: {e}")
            return False

    def _request(
        self,
        method: str,
        endpoint: str,
        params=None,
        data=None,
        json=None,
        headers=None,
        requires_auth=False,
        **kwargs,
    ):
        if requires_auth and not self.auth_token:
            logger.warning(f"Endpoint {endpoint} requires auth, but no token. Attempting to authenticate...")
            if not self.authenticate():
                raise requests.exceptions.RequestException(
                    "Authentication failed. Cannot proceed with authenticated request."
                )

        url = f"{self.base_url}{endpoint}"
        request_headers = self.session.headers.copy()  # Start with session headers

        if headers:
            request_headers.update(headers)

        # Restful-booker returns the token in JSON, rather than setting a cookie.
        if requires_auth and self.auth_token and method.upper() in {"PUT", "PATCH", "DELETE"}:
            if "Cookie" not in request_headers and "token" not in self.session.cookies:
                request_headers["Cookie"] = f"token={self.auth_token}"

        logger.info(f"API Request: {method.upper()} {url}")
        try:
            response = self.session.request(
                method,
                url,
                params=params,
                data=data,
                json=json,
                headers=request_headers,  # Use the combined headers
                timeout=kwargs.pop("timeout", self.default_timeout),
                **kwargs,
            )
            logger.info(f"API Response: {response.status_code} for {method.upper()} {url}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"API Request Exception for {method.upper()} {url}: {e}")
            raise

    # GET, POST, etc. methods can now accept 'requires_auth'
    def get(self, endpoint: str, params=None, requires_auth=False, **kwargs) -> requests.Response:
        return self._request("GET", endpoint, params=params, requires_auth=requires_auth, **kwargs)

    def post(self, endpoint: str, data=None, json=None, requires_auth=False, **kwargs) -> requests.Response:
        # Auth POST is special, doesn't require prior token
        if endpoint == self.config.get("api_auth_endpoint"):
            return self._request("POST", endpoint, data=data, json=json, requires_auth=False, **kwargs)
        return self._request("POST", endpoint, data=data, json=json, requires_auth=requires_auth, **kwargs)

    def put(self, endpoint: str, data=None, json=None, requires_auth=True, **kwargs) -> requests.Response:
        return self._request("PUT", endpoint, data=data, json=json, requires_auth=requires_auth, **kwargs)

    def delete(self, endpoint: str, requires_auth=True, **kwargs) -> requests.Response:
        return self._request("DELETE", endpoint, requires_auth=requires_auth, **kwargs)

    def patch(self, endpoint: str, data=None, json=None, requires_auth=True, **kwargs) -> requests.Response:
        return self._request("PATCH", endpoint, data=data, json=json, requires_auth=requires_auth, **kwargs)

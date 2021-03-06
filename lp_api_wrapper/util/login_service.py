"""
The LoginService class allows other Python LiveEngage API Wrapper classes to login via the Login Service API or using
OAuth1 authentication with app_key, app_secret, access_token, and access_token secret values.

Documentation:
https://developers.liveperson.com/login-getting-started.html
"""

import requests
from requests_oauthlib import OAuth1
from .domain_service import DomainService
from typing import (Union, Optional, NamedTuple)


UserLogin = NamedTuple('UserLogin', [('account_id', str), ('username', str), ('password', str)])

OAuthLogin = NamedTuple('OAuthLogin', [('account_id', str), ('app_key', str), ('app_secret', str),
                                       ('access_token', Optional[str]), ('access_token_secret', Optional[str])])


class LoginService(DomainService):
    def __init__(self, auth: Union[UserLogin, OAuthLogin]) -> None:
        self.bearer = None
        self.csrf = None
        self.oauth = None
        self.auth = auth

        # Checks Authentication
        if type(auth) in (UserLogin, OAuthLogin):
            super().__init__(account_id=auth.account_id)
            self.login_domain = self.get_domain(service_name='agentVep')
            if type(auth) == UserLogin:
                self.user_login(username=auth.username, password=auth.password)
            if type(auth) == OAuthLogin:
                self.oauth_login(app_key=auth.app_key, app_secret=auth.app_secret, access_token=auth.access_token,
                                 access_token_secret=auth.access_token_secret)
        else:
            raise TypeError('Accepts UserLogin or OAuthLogin for authentication. Import from lp_api_wrapper.')

    def oauth_login(self, app_key: str, app_secret: str, access_token: str, access_token_secret: str) -> None:
        """
        Allows OAuth1 authentication from the requests_oauthlib library.

        :param app_key:
        :param app_secret:
        :param access_token:
        :param access_token_secret:
        """
        # Set bearer and csrf tokens to None
        self.bearer = None
        self.csrf = None

        # Establish OAuth1 Credentials
        self.oauth = OAuth1(
            client_key=app_key,
            client_secret=app_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret
        )

    def user_login(self, username: str, password: str) -> None:
        """
        Documentation:
        https://developers.liveperson.com/agent-user-login.html

        Uses the LoginServiceAPI to generate a bearer token via LPA username and password credentials.

        :param username: LPA username
        :param password: LPA password
        """
        self.oauth = None

        # User Login URL
        url = 'https://{}/api/account/{}/login?v=1.3'

        # Generate request
        r = requests.post(
            url=url.format(self.login_domain, self.account_id),
            json={'username': username, 'password': password},
            headers={'content-type': 'application/json', 'accept': 'application/json'}
        )

        # Check request status
        if r.status_code == requests.codes.ok:
            self.bearer = r.json()['bearer']
            self.csrf = r.json()['csrf']
        else:
            print('Error: {}'.format(r.json()))
            r.raise_for_status()

    def refresh(self) -> None:
        """
        Documentation:
        https://developers.liveperson.com/agent-refresh.html

        Refreshes bearer token that is issued from the Login Service API
        """

        # Refresh URL
        url = 'https://{}/api/account/{}/refresh'

        # Generate request
        r = requests.post(
            url=url.format(self.login_domain, self.account_id),
            json={'csfr': self.csrf},
            headers={'content-type': 'application/json', 'accept': 'application/json'}
        )

        # Check request status
        if r.status_code == requests.codes.ok:
            print('Bearer token has been refreshed!')
        else:
            print('Error: {}'.format(r.json()))
            r.raise_for_status()

    def logout(self) -> None:
        """
        Documentation:
        https://developers.liveperson.com/agent-logout.html

        Logs out of current user session from the login service API.  Bearer token will be expired once logged out.
        """

        # Logout URL
        url = 'https://{}/api/account/{}/logout'

        # Generate request
        r = requests.post(
            url=url.format(self.login_domain, self.account_id),
            json={'csfr': self.csrf},
            headers={'content-type': 'application/json', 'accept': 'application/json'}
        )

        # Check request status
        if r.status_code == requests.codes.ok:
            print('User has been logged out!')
        else:
            print('Error: {}'.format(r.json()))
            r.raise_for_status()

    def authorize(self, headers: dict) -> dict:
        """
        Method is used to authorize API requests.

        :param headers:
        :return: dict of authorization parameters.
        """
        auth_args = {'headers': headers}
        if self.bearer:
            auth_args['headers']['authorization'] = 'Bearer {}'.format(self.bearer)
        elif self.oauth:
            auth_args['auth'] = self.oauth
        return auth_args

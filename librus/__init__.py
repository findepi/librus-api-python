import datetime

import requests_html

URI_BASE = 'https://synergia.librus.pl'


class LibrusSession(object):

    def __init__(self, *, uri_base=URI_BASE):
        self._uri_base = uri_base
        self._html_session = requests_html.HTMLSession()

    def login(self, username, password):
        """
        Authenticates session.
        """
        self._get('/loguj')  # Grab the cookie testing cookie support
        response = self._post('/loguj', data=dict(login=username, passwd=password, ed_pass_keydown='', ed_pass_keyup='', captcha='', czy_js=1))

        success, reason = self._check_login_success(response)
        if not success:
            raise RuntimeError("Login failed: " + reason)

    @staticmethod
    def _check_login_success(response):
        if not response.history:
            return False, "no redirect occurred after filling login form"

        redirect_location = response.history[-1].headers['Location']
        expected_redirects = {
            # The Location should be full URIs, but they just happen to be relative paths.
            '/uczen_index',
            '/uczen/index',
        }
        if redirect_location not in expected_redirects:
            return False, "unrecognized redirect after filling login form: " + repr(redirect_location)

        return True, None

    def list_announcements(self):
        """
        Gets announcements (AKA 'ogłoszenia')
        """
        response = self._get('/ogloszenia')

        for element in response.html.find('table.decorated.big'):
            yield self._parse_announcement(element)

    @staticmethod
    def _parse_announcement(element):
        title = _only_element(element.find('thead')).full_text.strip()
        content = author = date = None
        for data_row in element.find('tbody tr'):
            description = _only_element(data_row.find('th')).full_text.strip()
            text = _only_element(data_row.find('td')).full_text.strip()

            if description == "Dodał":
                assert author is None, "author already set"
                author = text

            elif description == "Treść":
                assert content is None, "content already set"
                content = text

            elif description == "Data publikacji":
                assert date is None, "date already set"
                date = datetime.datetime.strptime(text, '%Y-%m-%d')
                current_year = datetime.datetime.now().year
                assert current_year - 2 <= date.year <= current_year  # Sanity check

            else:
                raise RuntimeError(f"{repr(description)} is unrecognized")

        return Announcement(title, content, author, date)

    def _get(self, path, **kwargs):
        assert path[0] == '/'
        return self._html_session.get(url=self._uri_base + path, **kwargs)

    def _post(self, path, **kwargs):
        assert path[0] == '/'
        return self._html_session.post(url=self._uri_base + path, **kwargs)


class Announcement(object):
    def __init__(self, title, content, author, date):
        self.title = title
        self.content = content
        self.author = author
        self.date = date


def _only_element(values):
    value, = values
    return value

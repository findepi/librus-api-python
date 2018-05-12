import requests_html

URI_BASE = 'https://synergia.librus.pl'

_ANNOUNCEMENT_DESCRIPTION_TO_KEY = {
    "Dodał": 'author',
    "Data publikacji": 'date',
    "Treść": 'content',
}


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

        if not self._login_successful(response):
            raise RuntimeError("Login failed")

    def list_announcements(self):
        """
        Gets announcements (AKA 'ogłoszenia')
        """
        response = self._get('/ogloszenia')

        for element in response.html.find('table.decorated.big'):
            announcement = {
                'title': _only_element(element.find('thead')).full_text.strip(),
            }

            for data_row in element.find('tbody tr'):
                description = _only_element(data_row.find('th')).full_text.strip()
                text = _only_element(data_row.find('td')).full_text.strip()
                key = _ANNOUNCEMENT_DESCRIPTION_TO_KEY[description]
                if key in announcement:
                    raise RuntimeError(f"{key} already set in {repr(announcement)}")
                announcement[key] = text

            yield announcement

    @staticmethod
    def _login_successful(response):
        return response.history and \
               response.history[-1].headers['Location'] in {
                   '/uczen_index',  # The Location should be full URI, but it just happens to be a relative path.
               }

    def _get(self, path, **kwargs):
        assert path[0] == '/'
        return self._html_session.get(url=self._uri_base + path, **kwargs)

    def _post(self, path, **kwargs):
        assert path[0] == '/'
        return self._html_session.post(url=self._uri_base + path, **kwargs)


def _only_element(values):
    value, = values
    return value

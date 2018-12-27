import datetime
import requests_html
from urllib.parse import urljoin


class LibrusSession(object):

    def __init__(self):
        self._html_session = None

    def login(self, username, password):
        """
        Creates authenticated session.
        """

        self._html_session = requests_html.HTMLSession()
        self._html_session.get(url='https://api.librus.pl/OAuth/Authorization?client_id=46&response_type=code&scope=mydata')
        response = self._html_session.post(url='https://api.librus.pl/OAuth/Authorization?client_id=46',
                                           data={'action': 'login', 'login': username, 'pass': password})
        if not response.json().get('status') == 'ok' or not response.json().get('goTo'):
            raise RuntimeError("Login failed")
        self._html_session.get(url=urljoin(response.url, response.json()['goTo']))
        # TODO somehow validate the login was truly successful

    def list_announcements(self):
        """
        Gets announcements (AKA 'ogłoszenia')
        """
        response = self._html_session.get(url='https://synergia.librus.pl/ogloszenia')

        for element in response.html.find('table.decorated.big'):
            yield self._parse_announcement(element)

    def list_exams(self):
        """
        Gets Exams from Calendar
        """
        response = self._html_session.get(url="https://synergia.librus.pl/terminarz")
        # TODO we should be iterating explicitly over links to calendar items' details; doing unstructured "grepping" for now
        for element in response.html.search_all("szczegoly/{}'"):
            details = self._html_session.get(url=f"https://synergia.librus.pl/terminarz/szczegoly/{element[0]}")
            yield self._parse_exam(details.html.find('table.decorated.small'))

    @staticmethod
    def _parse_exam(element):
        date = lesson = teacher = category = subject = classroom = specification = publish_date = interval = None
        for data_row in element[0].find("tbody tr"):
            description = _only_element(data_row.find('th')).full_text.strip()
            text = _sanitize_text(_only_element(data_row.find('td')).full_text.strip())
            if description == "Data":
                assert date is None, "date already set"
                date = text

            elif description == "Nr lekcji":
                assert lesson is None, "lesson already set"
                lesson = text

            elif description == "Nauczyciel":
                assert teacher is None, "teacher already set"
                teacher = text

            elif description == "Rodzaj":
                assert category is None, "category already set"
                category = text

            elif description == "Przedmiot":
                assert subject is None, "subject already set"
                subject = text

            elif description == "Sala":
                assert classroom is None, "classroom already set"
                classroom = text

            elif description == "Opis":
                assert specification is None, "specification already set"
                specification = text

            elif description == "Data dodania":
                assert publish_date is None, "publish date already set"
                publish_date = text

            elif description == "Przedział czasu":
                assert interval is None, "interval already set"
                interval = text
            else:
                print(f"{repr(description)} is unrecognized")

        return Exam(date, lesson, teacher, category, subject,
                    classroom, specification, publish_date, interval)

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


class Announcement(object):
    def __init__(self, title, content, author, date):
        self.title = title
        self.content = content
        self.author = author
        self.date = date


class Exam(object):
    def __init__(self, date, lesson, teacher, category, subject,
                 classroom, specification, publish_date, interval):
        self.date = date
        self.lesson = lesson
        self.teacher = teacher
        self.category = category
        self.subject = subject
        self.classroom = classroom
        self.specification = specification
        self.publish_date = publish_date
        self.interval = interval


def _only_element(values):
    value, = values
    return value


def _sanitize_text(text):
    return text.replace('\N{NO-BREAK SPACE}', '')

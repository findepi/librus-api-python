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
            yield self._parse_exam(details.html.find('table.decorated.medium'))

    def list_absences(self):
        """
        Get Absences (AKA 'nieobecnosci')
        """
        response = self._html_session.get(url='https://synergia.librus.pl/przegladaj_nb/uczen')
        for element in response.html.search_all("szczegoly/{}'"):
            details = self._html_session.get(url=f"https://synergia.librus.pl/przegladaj_nb/szczegoly/{element[0]}")
            yield self._parse_absence(details.html.find('table.decorated.medium'))

    @staticmethod
    def _parse_exam(element):
        date = lesson = teacher = category = subject = classroom = specification = publish_date = interval = online_lesson_link = None
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

        # for online lessons it additionally saves a link to zoom meeting
        if "lekcja online" in category and len(element[0].absolute_links) == 1:
            online_lesson_link = list(element[0].absolute_links)[0]

        return Exam(date, lesson, teacher, category, subject,
                    classroom, specification, publish_date, interval, online_lesson_link)

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

    def list_grades(self):
        response = self._html_session.get(url='https://synergia.librus.pl/przegladaj_oceny/uczen')
        grades = []
        for grade_row in response.html.find('table.decorated.stretch')[1].find('tr.detail-grades'):
            grade_data = grade_row.find('td')
            grade = grade_data[0].text  # ocena
            comment = grade_data[1].text  # komentarz
            title = grade_data[2].text  # tytuł oceny
            added_date = grade_data[3].text  # data wstawienia
            teacher = grade_data[4].text  # nauczyciel
            correction_grade = grade_data[5].text  # poprawa oceny
            added_by = grade_data[6].text  # dodał
            grades.append(Grade(grade, comment, title, added_date, teacher, correction_grade, added_by))
        return grades

    def list_subject_semester_info(self):
        response = self._html_session.get(url='https://synergia.librus.pl/przegladaj_oceny/uczen')
        subjects = []
        for subject in response.html.find('.line0') + response.html.find('.line1'):
            if len(subject.find('td')) == 10 and subject.find('td')[1].text != 'Ocena' and subject.find('td')[1].text != '1':
                subject_name = subject.find('td')[1].text
                grades_first_semester = subject.find('td')[2].text
                grade_first_semester_prediction = subject.find('td')[3].text
                grade_first_semester = subject.find('td')[4].text
                grades_second_semester = subject.find('td')[5].text
                grade_second_semester_prediction = subject.find('td')[6].text
                grade_second_semester = subject.find('td')[7].text
                grade_final_prediction = subject.find('td')[8].text
                grade_final = subject.find('td')[9].text
                subjects.append(SubjectSemesterInfo(subject_name, grades_first_semester, grade_first_semester_prediction, grade_first_semester,
                                                    grades_second_semester, grade_second_semester_prediction, grade_second_semester,
                                                    grade_final_prediction, grade_final))
        return subjects

    def schedule(self):
        response = self._html_session.get(url='https://synergia.librus.pl/przegladaj_plan_lekcji')
        lessons = []
        for subject_line in response.html.find('tr.line1'):
            index = subject_line.find('td')[0].text
            time = _sanitize_text(subject_line.find('th')[0].text)
            for day, cell in enumerate(subject_line.find('td')[1:]):
                if not cell.find('div.text'):
                    continue
                subject_data = _only_element(cell.find('div.text')).text.split('-')
                subject_name = _sanitize_text(subject_data[0])
                teacher = subject_data[1]
                classroom = None
                if 's.' in teacher:
                    subject_data = teacher.split('s.')
                    teacher = _sanitize_text(subject_data[0])
                    classroom = _sanitize_text(subject_data[1])
                else:
                    teacher = _sanitize_text(teacher)
                lessons.append(Lesson(day, index, subject_name, time, teacher, classroom))
        lessons.sort(key=(lambda lesson: (lesson.day, lesson.index)))
        return lessons

    def list_messages(self, get_content=False):
        """
        Gets messages (AKA 'wiadomości')
        """
        response = self._html_session.get(url='https://synergia.librus.pl/wiadomosci')

        for row in response.html.find('.stretch > tbody > tr'):
            cells = row.find('td')
            messages_available = len(cells) >= 4
            if messages_available:
                href = cells[3].find('a')[0].attrs['href']
                message = Message(
                    message_id=href.strip(),
                    sender=cells[2].text,
                    subject=cells[3].text,
                    sent_at=datetime.datetime.strptime(cells[4].text, '%Y-%m-%d %H:%M:%S'),
                    is_read=('font-weight: bold' not in cells[3].attrs.get('style', ''))
                )
                if get_content:
                    url = 'https://synergia.librus.pl' + href
                    content = self._html_session.get(url=url).html.find('.container-message-content')[0]
                    message.content = content.text

                yield message

    @staticmethod
    def _parse_absence(element):
        category = date = subject = topic = lesson = teacher = school_trip = added_by = None
        for data_row in element[0].find('tbody tr'):
            if not data_row.find('th'):
                continue
            description = _only_element(data_row.find('th')).full_text.strip()
            text = _sanitize_text(_only_element(data_row.find('td')).full_text.strip())
            if description == "Data":
                assert date is None, "date already set"
                date = text

            elif description == "Godzina lekcyjna":
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
            elif description == "Temat zajęć":
                assert topic is None, "topic already set"
                topic = text
            elif description == "Czy wycieczka":
                assert school_trip is None, "school_trip already set"
                school_trip = text
            elif description == "Dodał":
                assert added_by is None, "added_by already set"
                added_by = text
            else:
                print(f"{repr(description)} is unrecognized")

        return Absence(date, lesson, teacher, category, subject, topic, school_trip, added_by)


class Announcement(object):
    def __init__(self, title, content, author, date):
        self.title = title
        self.content = content
        self.author = author
        self.date = date


class Exam(object):
    def __init__(self, date, lesson, teacher, category, subject,
                 classroom, specification, publish_date, interval, online_lesson_link=None):
        self.date = date
        self.lesson = lesson
        self.teacher = teacher
        self.category = category
        self.subject = subject
        self.classroom = classroom
        self.specification = specification
        self.publish_date = publish_date
        self.interval = interval
        self.online_lesson_link = online_lesson_link


class Grade(object):
    def __init__(self, grade, comment, title, added_date, teacher, correction_grade, added_by):
        self.grade = grade
        self.comment = comment
        self.title = title
        self.added_date = added_date
        self.teacher = teacher
        self.correction_grade = correction_grade
        self.added_by = added_by


class SubjectSemesterInfo(object):
    def __init__(self, subject_name, grades_first_semester, grade_first_semester_prediction, grade_first_semester, grades_second_semester,
                 grade_second_semester_prediction, grade_second_semester, grade_final_prediction, grade_final):
        self.subject_name = subject_name
        self.grades_first_semester = grades_first_semester
        self.grade_first_semester_prediction = grade_first_semester_prediction
        self.grade_first_semester = grade_first_semester
        self.grades_second_semester = grades_second_semester
        self.grade_second_semester_prediction = grade_second_semester_prediction
        self.grade_second_semester = grade_second_semester
        self.grade_final_prediction = grade_final_prediction
        self.grade_final = grade_final


class Lesson(object):
    def __init__(self, day, index, subject, time, teacher, classroom):
        self.day = day
        self.index = index
        self.name = subject
        self.time = time
        self.teacher = teacher
        self.classroom = classroom


class Message(object):
    def __init__(self, message_id, sender, subject, sent_at, is_read):
        self.message_id = message_id
        self.sender = sender
        self.subject = subject
        self.sent_at = sent_at
        self.is_read = is_read
        self.content = None


class Absence(object):  # nieobecność
    def __init__(self, date, lesson, teacher, category, subject, topic, school_trip, added_by):
        self.date = date
        self.lesson = lesson
        self.teacher = teacher
        self.category = category
        self.subject = subject
        self.topic = topic
        self.school_trip = school_trip
        self.added_by = added_by


def _only_element(values):
    value, = values
    return value


def _sanitize_text(text):
    text = text.replace('\N{NO-BREAK SPACE}', ' ')
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&nbsp', ' ')
    text = text.strip()
    return text


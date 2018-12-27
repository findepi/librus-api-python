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

    def list_grades(self):
        response = self._html_session.get(url='https://synergia.librus.pl/przegladaj_oceny/uczen')
        grades = []
        for row in grade_session.html.find('table.decorated')[1].find('[class*="line"]'):
            #conditions to find only the needed rows
            if len(row.attrs["class"])==1 and "name" not in row.attrs and len(vals)>=10:
                vals = row.find("td")
                lesson_name = vals[1].text
                for grade in vals[2].find('a.ocena'):
                    values = grade.attrs["title"].split("<br>")
                    category = values[0].split(": ")[1] #IT LOOKS LIKE "Kategoria: xyz"
                    date = values[1].split(": ")[1].split(" (")[0] #LOOKS LIKE "Data: yyy-mm-dd (day.)"
                    teacher = values[2].split(": ")[1] #LOOKS LIKE "Nauczyciel: xyz"
                    addedBy = values[3].split(": ")[1].replace("<br/>","") #LOOKS LIKE "Dodal: xyz<br/>"
                    grade = grade.text
                    grades.append(Grade(lesson_name, grade, date, teacher, addedBy))
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


class Grade(object):
    def __init__(self, lesson_name, grade, date, teacher, added_by):
        self.lesson_name = less
        self.grade = grade
        self.date = date
        self.teacher = teacher
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


def _only_element(values):
    value, = values
    return value


def _sanitize_text(text):
    text = text.replace('\N{NO-BREAK SPACE}', ' ')
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&nbsp', ' ')
    text = text.strip()
    return text

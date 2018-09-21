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

    def getSchedule(self,day):
        response = self._html_session.get(url='https://synergia.librus.pl/przegladaj_plan_lekcji')
        lessonArray = []
        for subjectLine in response.html.find('tr.line1'):
            subjectIndex = subjectLine.find('td')[0].text
            subjectTime = subjectLine.find('th')[0].text
            try:
                subjectName = subjectLine.find('td')[1+day].find('div.text')[0].text
                subjectData = subjectName.split('-')
                subjectTeacher = subjectData[1]
                subjectName = subjectData[0]
                subjectRoom = None
                if 's.' in subjectTeacher:
                    subjectData = subjectTeacher.split('s.')
                    subjectTeacher = subjectData[0]
                    subjectRoom = subjectData[1]
                lessonArray.append(lessonUnit(subjectIndex,subjectName,subjectTime,subjectTeacher,subjectRoom))
            except:
                pass
        return lessonArray

    def getDetailGrades(self):
        response = self._html_session.get(url='https://synergia.librus.pl/przegladaj_oceny/uczen')
        grades = []
        for grade in response.html.find('table.decorated.stretch')[1].find('tr.detail-grades'):
            gradeData = grade.find('td')
            #ocena
            gradeB = gradeData[0].text
            #komentarz
            comment = gradeData[1].text
            #tytuł oceny
            title = gradeData[2].text
            #data wstawienia
            addedDate = gradeData[3].text
            #nauczyciel
            teacher = gradeData[4].text
            #poprawa oceny
            correctionGrade = gradeData[5].text
            #dodał
            addedBy = gradeData[6].text
            grades.append(detailGrade(gradeB,comment,title,addedDate,teacher,correctionGrade,addedBy))
        return grades
    def getSubjectInfov1(self):
        response = self._html_session.get(url='https://synergia.librus.pl/przegladaj_oceny/uczen')
        subjectArray = []
        for subject in response.html.find('.line0') + response.html.find('.line1'):
            if len(subject.find('td'))==10 and subject.find('td')[1].text != 'Ocena' and subject.find('td')[1].text != '1':
                subjectName = subject.find('td')[1].text
                gradesFirstSemester = subject.find('td')[2].text
                gradeFirstSemesterPrediction = subject.find('td')[3].text
                gradeFirstSemester = subject.find('td')[4].text
                gradesSecondSemester = subject.find('td')[5].text
                gradeSecondSemesterPrediction = subject.find('td')[6].text
                gradeSecondSemester = subject.find('td')[7].text
                gradeFinalPrediction = subject.find('td')[8].text
                gradeFinal = subject.find('td')[9].text
                subjectArray.append(subjectInfov1(subjectName, gradesFirstSemester, gradeFirstSemesterPrediction, gradeFirstSemester,gradesSecondSemester,gradeSecondSemesterPrediction,gradeSecondSemester,gradeFinalPrediction,gradeFinal))
        return subjectArray
class lessonUnit(object):
    def __init__(self,subjectIndex,subjectName,subjectTime,subjectTeacher,subjectRoom):
        self.index = subjectIndex
        self.name = subjectName
        self.time = subjectTime
        self.teacher = subjectTeacher
        self.room = subjectRoom
class subjectInfov1(object):
    def __init__(self, subjectName, gradesFirstSemester, gradeFirstSemesterPrediction, gradeFirstSemester,gradesSecondSemester,gradeSecondSemesterPrediction,gradeSecondSemester,gradeFinalPrediction,gradeFinal):
        self.subjectName = subjectName
        self.grades1S = gradesFirstSemester
        self.grade1SPrediction = gradeFirstSemesterPrediction
        self.grade1S = gradeFirstSemester
        self.grades2S = gradesSecondSemester
        self.grade2SPrediction = gradeSecondSemesterPrediction
        self.grade2S = gradeSecondSemester
        self.gradeFPrediction = gradeFinalPrediction
        self.gradeF = gradeFinal
class detailGrade(object):
    def __init__(self,grade,comment,title,addedDate,teacher,correctionGrade,addedBy):
        self.grade = grade
        self.comment = comment
        self.title = title
        self.addedDate = addedDate
        self.teacher = teacher
        self.correctionGrade = correctionGrade
        self.addedBy = addedBy

class Announcement(object):
    def __init__(self, title, content, author, date):
        self.title = title
        self.content = content
        self.author = author
        self.date = date


def _only_element(values):
    value, = values
    return value

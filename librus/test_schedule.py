from collections import defaultdict
#timetable_session is 
#self._html_session.get(url='https://synergia.librus.pl/przegladaj_plan_lekcji')
maxLessons = 14
timespans = []
lessons = defaultdict(lambda: [])
for i in range(maxLessons):
    #time spans
    raw = timetable_session.html.find('table')[1].find("tr")[i*2 + 1].find("th")[0].text
    format_spans = {
        "raw":raw,
        "start":raw.split("\xa0-\xa0")[0],
        "end":raw.split("\xa0-\xa0")[1]
    }
    timespans.append(format_spans)
    #lessons
    for day in range(5):
        raw = timetable_session.html.find('table')[1].find("tr")[i*2 + 1].find("td")[day+1].text.replace("\xa0"," ").replace("\n","").replace("&nbsp","")
        if raw!='':
            substitution_teacher = True if str(raw).startswith("zastępstwo") else False
            lesson_canceled = True if str(raw).startswith("odwołane") else False
            room = None if "s. " not in str(raw) else str(raw).split("s. ")[-1].strip()
            teacher = raw.split("-")[1].split(" s. ")[0] if room is not None else raw.split("- ")[1]
            name = raw.split("-")[0].replace("zastępstwo","").replace("odwołane","")
            lesson = {
                "substitution_teacher":substitution_teacher,
                "lesson_canceled":lesson_canceled,  #using .strip() to remove unneeded spaces
                "room":room,
                "name":name.strip(),
                "teacher":teacher.strip(),
                "index":i,
            }
            lessons[day].append(lesson)
lessons["timespans"] = timespans
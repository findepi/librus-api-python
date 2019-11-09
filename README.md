# Librus API

## Usage

```python
from librus import LibrusSession 
session = LibrusSession()
session.login("1234567u", "p4ssw0rD")
for announcement in session.list_announcements():
    print(announcement.title)
```

## API completeness

3%. Currently only announcements, messages and exams are covered. PRs welcomed.

# Librus API

## Usage

```python
from librus import LibrusSession 
session = LibrusSession()
session.login("1234567u", "p4ssw0rD")
for announcement in session.list_announcements():
    print(announcement['title'])
```

## API completeness

1%. Currently only announcements are covered. PRs welcomed. 

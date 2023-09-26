# new-imdb
A selenium semi-automation tool to assist IMDb contributors creating new film entries through the [Adding a New Title](https://contribute.imdb.com/updates/edit?update=title) page.

Must be logged in to IMDb.

### Installation
---
```
pip install git+https://github.com/famgz/new-imdb.git
```

### Usage
---
- organize data
```python
url = "https://url-for-some-film.com"

data = {
    'original_title' : str
    'title_eng'      : str
    'directors'      : list
    'countries'      : list
    'country_code'   : str
    'year'           : str
    'length'         : int
    'languages'      : list
    'genres'         : list
    'production'     : list
    'producer'       : list
    'screenplay'     : list
    'cinematography' : list
    'editing'        : list
    'synopsis'       : str
}
```
- import and run
```python
from new_imdb import new_imdb

new_imdb(url, data)
```
- follow the prompt instructions
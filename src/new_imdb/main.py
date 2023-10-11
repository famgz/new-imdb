from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.by import By
from time import sleep
import shlex
import subprocess
from famgz_utils import print, timeit, kill_process, translate_, clean_name, open_selenium

from .config import cookies

IMDB_FORM_URL = 'https://contribute.imdb.com/updates?update=title'

url_test = 'https://pro.festivalscope.com/film/much-in-common'

driver = None


def get_url_type(url):
    url_type = 'Festival'
    if 'pro.festivalscope' in url:
        url_type = 'Festival Scope'
    elif 'festivaldegramado.net' in url:
        url_type = 'Festival de Gramado'
    elif 'olhardecinema.com' in url:
        url_type = 'Olhar de Cinema - Festival Internacional de Curitiba'
    elif 'ecofalante.org' in url:
        url_type = 'Mostra Ecofalante de Cinema'
    elif '.mostra.org/' in url:
        url_type = 'Mostra Internacional de Cinema em São Paulo'

    return url_type


def check_keys(film_data: dict, url_type):
    # check missing keys
    required_keys = ['original_title', 'title_eng', 'directors', 'countries', 'country_code', 'year', 'length', 'languages',
                     'genres', 'production', 'producer', 'screenplay', 'cinematography', 'editing', 'synopsis']
    for key in required_keys:
        if key not in film_data.keys():
            film_data[key] = None

    if film_data['length']:
        if not isinstance(film_data['length'], int):
            film_data['length'] = int(film_data['length'])

    # check data language
    if url_type != 'Festival Scope':
        for key in ['countries', 'languages', 'genres']:
            if film_data[key]:
                film_data[key] = [translate_(i) for i in film_data[key]]
                # film_data[key] = [translate_(i).text for i in film_data[key] if translate_(i).src is not 'en']

    # filling missing staff with directors
    for key in ['producer', 'screenplay', 'cinematography', 'editing']:
        if not film_data[key]:
            film_data[key] = film_data['directors']

    if not film_data['production']:
        film_data['production'] = film_data['directors'][0]

    if not film_data['synopsis'] and 'synopsis_eng' in film_data.keys():
        film_data['synopsis'] = film_data['synopsis_eng']

    # treat titles
    if not film_data['title_eng'] and film_data['original_title']:
        film_data['title_eng'] = film_data['original_title']
        film_data['original_title'] = None

    if film_data['title_eng'] and film_data['original_title']:
        if clean_name(film_data['original_title']) == clean_name(film_data['title_eng']):
            film_data['original_title'] = None

    if not film_data['title_eng']:
        if film_data['title_pt']:
            film_data['title_eng'] = film_data['title_pt']

    return film_data


@timeit
def new_imdb(url, data):

    global driver
    if driver is None:
        driver = open_selenium(headless=False)

    url_type = get_url_type(url)
    data = check_keys(data, url_type)

    def click_by_id(id):
        driver.execute_script("arguments[0].click();", driver.find_element_by_id(id))

    def click_by_name(name):
        driver.execute_script("arguments[0].click();", driver.find_element_by_name(name))

    def continue_(wait=False):
        click_by_name('action__Continue')
        sleep(3.5)
        if wait is True:
            input('hit Enter to continue...')

    def submit():
        input('Submit data?')
        click_by_name('action__Submit')
        sleep(2)

    sleep(1)
    print(f'[blue]{url}')
    print(f"{data['title_eng']} ({data['original_title']})")
    print(data['year'], data['length'], 'min')
    print(data['directors'], highlight=True)
    print(data['countries'], highlight=True)
    print(data['genres'], highlight=True)
    sleep(2)
    driver.get(IMDB_FORM_URL)
    sleep(2)


    # --> 1 ROUND
    if data['original_title']:
        driver.find_element_by_name("o.1.title.new.1.edit.plain").send_keys(data['original_title'])
    else:
        driver.find_element_by_name("o.1.title.new.1.edit.plain").send_keys(data['title_eng'])

    click_by_id('o.1.title.new.1.edit.first_type.film')
    click_by_id('o.1.title.new.1.edit.status.released')
    driver.find_element_by_name('o.1.title.new.1.edit.source').send_keys('...none of the above')
    continue_()


    # --> 2 ROUND
    if int(data['length']) > 45:
        click_by_id('o.1.title.new.1.edit.second_type.feature')
    else:
        click_by_id('o.1.title.new.1.edit.second_type.short')
    driver.find_element_by_id('o.1.title.new.1.edit.year').send_keys(data['year'])
    continue_(wait=True)


    # --> 3 ROUND
    try:
        click_by_name('o.1.title.new.1.error.title_format_all_lowercase.ignore')  # confirm ignore lowercase
    except:
        pass
    try:
        click_by_name('o.1.title.new.1.error.new_title_exists.fixed')
        sleep(0.3)
        click_by_name('o.1.title.new.1.error.title_format_all_uppercase.ignore')
    except:
        pass

    answer = input('Title already exist? [y]\n>')
    if answer.lower() == 'y':
        track_link = input('insert existing IMDb ID\n>')
        # driver.close()
        sleep(2)
        # kill_process()
        print(f'[bright_black]{track_link}')
        print('-'*70)
        return track_link
    else:
        continue_()


    # --> 4 ROUND
    sleep(1)
    # Release Dates
    driver.find_element_by_name('o.1.release_dates.new.1.edit.country').send_keys(data['countries'][0])
    driver.find_element_by_id('o.1.release_dates.new.1.edit.year').send_keys(data['year'])

    # Miscellaneous Link
    try:
        driver.find_element_by_id('o.1.title_urls_msc.new.1.edit.url').send_keys(url)
        driver.find_element_by_id('o.1.title_urls_msc.new.1.edit.desc').send_keys(url_type)
    except:
        pass

    # Basic Identifying Information
    # Country of Origin
    if len(data['countries']) == 1:
        driver.find_element_by_name('o.1.countries.choose').send_keys("Add 1 item")
        driver.find_element_by_name('o.1.countries.new.1.edit.data').send_keys(data['countries'][0])
    elif len(data['countries']) > 1:
        driver.find_element_by_name('o.1.countries.choose').send_keys(f"Add {len(data['countries'])} items")

    # Languages
    if data['languages']:
        if len(data['languages']) == 1:
            driver.find_element_by_name('o.1.language.choose').send_keys("Add 1 item")
            driver.find_element_by_name('o.1.language.new.1.edit.data').send_keys(data['languages'][0])
        elif len(data['languages']) > 1:
            driver.find_element_by_name('o.1.language.choose').send_keys(f"Add {len(data['languages'])} items")

    # Genres
    if data['genres']:
        if len(data['genres']) == 1:
            driver.find_element_by_name('o.1.genres.choose').send_keys("Add 1 item")
            driver.find_element_by_name('o.1.genres.new.1.edit.data').send_keys(data['genres'][0])
        elif len(data['genres']) > 1:
            driver.find_element_by_name('o.1.genres.choose').send_keys(f"Add {len(data['genres'])} items")

    # Directors
    if len(data['directors']) == 1:
        driver.find_element_by_name('o.1.directors.choose').send_keys("Add 1 credit")
        driver.find_element_by_name('icicle-search-o.1.directors.new.1.edit.name').send_keys(data['directors'][0])
    elif len(data['directors']) > 1:
        driver.find_element_by_name('o.1.directors.choose').send_keys(f"Add {len(data['directors'])} credits")

    # Production Companies
    if data['production']:
        driver.find_element_by_name('icicle-search-o.1.production_companies.new.1.edit.company').send_keys(data['production'])

    # Major Credits
    sleep(1)
    if data['screenplay']:
        driver.find_element_by_name('o.1.writers.choose').send_keys("Add 1 credit")
    if data['producer']:
        driver.find_element_by_name('o.1.producers.choose').send_keys("Add 1 credit")
    else:
        print('[yellow]Warning! No producer found!')
    if data['cinematography']:
        driver.find_element_by_name('o.1.cinematographers.choose').send_keys("Add 1 credit")
    if data['editing']:
        driver.find_element_by_name('o.1.editors.choose').send_keys("Add 1 credit")

    # Recommended Information
    if data['length']:
        driver.find_element_by_name('o.1.running_times.choose').send_keys("Add 1 item")
    if data['synopsis']:
        if len(data['synopsis']) < 239:
            driver.find_element_by_name('o.1.outlines.choose').send_keys("Add 1 item")
        else:
            driver.find_element_by_name('o.1.plot.choose').send_keys("Add 1 item")

    # Alternative title, if exists
    if data['original_title']:
        click_by_name('o.1.choose_again')

    for i in ['genres', 'production']:
        if not data[i]:
            print(f'[yellow]{i} information is missing!')
    continue_(wait=True)


    # --> 5 ROUND
    sleep(1)
    click_by_name('o.1.release_dates.new.1.error.release_date_new_title_no_attribute.ignore')

    # Multiple items, if exists
    if len(data['countries']) > 1:
        for i, v in enumerate(data['countries']):
            driver.find_element_by_name(f'o.1.countries.new.{i+1}.edit.data').send_keys(v)

    if data['languages']:
        if len(data['languages']) > 1:
            for i, v in enumerate(data['languages']):
                driver.find_element_by_name(f'o.1.language.new.{i+1}.edit.data').send_keys(v)

    if data['genres']:
        if len(data['genres']) > 1:
            for i, v in enumerate(data['genres']):
                driver.find_element_by_name(f'o.1.genres.new.{i+1}.edit.data').send_keys(v)

    if len(data['directors']) > 1:
        for i, v in enumerate(data['directors']):
            driver.find_element_by_name(f'icicle-search-o.1.directors.new.{i+1}.edit.name').send_keys(v)

    # Major Credits
    if data['screenplay']:
        driver.find_element_by_name('icicle-search-o.1.writers.new.1.edit.name').send_keys(data['screenplay'][0])
    if data['producer']:
        driver.find_element_by_name('icicle-search-o.1.producers.new.1.edit.name').send_keys(data['producer'][0])
        driver.find_element_by_name('o.1.producers.new.1.edit.job_menu').send_keys('producer')
    if data['cinematography']:
        driver.find_element_by_name('icicle-search-o.1.cinematographers.new.1.edit.name').send_keys(data['cinematography'][0])
    if data['editing']:
        driver.find_element_by_name('icicle-search-o.1.editors.new.1.edit.name').send_keys(data['editing'][0])
    # Recommended Information
    if data['length']:
        driver.find_element_by_name('o.1.running_times.new.1.edit.time').send_keys(data['length'])
    if data['synopsis']:
        if len(data['synopsis']) < 239:
            driver.find_element_by_name('o.1.outlines.new.1.edit.text').send_keys(data['synopsis'])
        else:
            driver.find_element_by_name('o.1.plot.new.1.edit.text').send_keys(data['synopsis'])

    # if data['genres']:
    #     if 'Documentary' in data['genres']:
    try:
        click_by_name('o.1.genres.new.1.error.genre_documentary.ignore')
    except:
        pass

    if data['original_title']:
        driver.find_element_by_name('o.1.akas.choose').send_keys("Add 1 item")
        continue_()
        sleep(2)
        driver.find_element_by_name('o.1.akas.new.1.edit.aka').send_keys(data['title_eng'])
        driver.find_element_by_name('o.1.akas.new.1.edit.countryn').send_keys('International: English title')
        driver.find_element_by_name('o.1.akas.new.1.edit.attrn').send_keys('imdb display title')

    continue_()
    try:
        click_by_name('o.1.plot.new.1.error.spelling.ignore')
    except:
        pass

    # print('press Enter to try check all new credits warnings')
    # continue_(wait=True)

    # existing_credits = [
    # 'o.1.directors.new.1.error.no_existing_credits.fix',
    # 'o.1.writers.new.1.error.no_existing_credits.fix',
    # 'o.1.producers.new.1.error.no_existing_credits.fix',
    # 'o.1.cinematographers.new.1.error.no_existing_credits.fix',
    # 'o.1.editors.new.1.error.no_existing_credits.fix',
    # ]
    # # for i in range(1):
    # for i in existing_credits:
    #     try:
    #         click_by_name(i)
    #         print(f"checked {i.split('.')[2]}")
    #         sleep(.5)
    #     except:
    #         pass
    # continue_()

    continue_(wait=True)
    submit()
    sleep(2)
    track_link = driver.find_element_by_class_name('trackbutton').get_attribute('href')
    sleep(.5)
    print(f'[bright_black]{track_link}')
    print('-'*70)
    # driver.close()
    # kill_process()
    return track_link

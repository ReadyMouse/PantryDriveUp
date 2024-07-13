from flask import Flask, render_template, request
from pandas import read_excel
from datetime import datetime

import os
import pdfkit   # pdfkit requires that wkhtmltopdf be installed in order to work
import platform
import shutil
import socket
from google.cloud import translate_v2
from flask import request

NAME_DICTIONARY = {
    'Fresh Food': 'fresh-food',
    'Freezer Meats': 'freezer-meats',
    'Freezer Bonus': 'freezer-bonus',
    'Fridge': 'fridge',
    'Canned Vegetables': 'canned-veg',
    'Broth': 'broth',
    'Canned Soup': 'canned-soup',
    'Canned Meat': 'canned-meat',
    'Beans & Lentils': 'beans',
    'Juice': 'juice',
    'Shelf-stable Milk': 'up-milk',
    'Snacks': 'snacks',
    'Pantry': 'pantry',
    'Rice': 'rice',
    'Canned Fruit': 'canned-fruit',
    'Pantry 2': 'pantry-2',
    'Breakfast': 'breakfast',
    'Peanut Butter & Jelly': 'pbj',
    'Canned Tomatoes': 'canned-tom',
    'Bonus Items': 'bonus',
    'Bonus Items 2': 'bonus-2',
    'Personal Hygiene Items': 'hygiene',
    'Paper Goods': 'paper',
    'Snack Bags for Kids': 'snack_bags',
    'Diapers & Pull-ups': 'diapers',
    'Formula': 'formula',
    'Baby Food': 'baby-food',
    'Coffee/Tea/Cocoa': 'coffee',
    'Vegetable Oil': 'oil'
}

TRANSLATE_DICTIONARY = {}

if not os.path.isfile(os.path.expanduser('~/Desktop/DriveThruGroceryList.xlsx')):
    if __name__ == '__main__':
        shutil.copy(os.path.dirname(__file__) + '/static/DriveThruGroceryList.xlsx',
                    os.path.expanduser('~/Desktop/DriveThruGroceryList.xlsx'))
    else:
        try:
            from importlib.resources.pkg_resources import resource_filename
        except ImportError:
            # Try backported to PY<37 `importlib_resources`.
            from pkg_resources import resource_filename
        spreadsheet = resource_filename(__package__, 'static/DriveThruGroceryList.xlsx')
        shutil.copy(spreadsheet, os.path.expanduser('~/Desktop/DriveThruGroceryList.xlsx'))

DriveThruGroceryList = read_excel(os.path.expanduser('~/Desktop/DriveThruGroceryList.xlsx'), engine='openpyxl')

app = Flask(__name__, static_url_path='/static')


def print_html(html, name):
    """ Convert HTML markup to PDF and then send the PDF to the default printer.
        Windows is unique in that it has no support on it's own for printing PDF
        files, so users of Windows must install PDFtoPrinter from this URL:
        http://www.columbia.edu/~em36/PDFtoPrinter.exe
    """
    packing_list_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'PackingLists')

    if not os.path.isdir(packing_list_path):
        try:
            os.makedirs(packing_list_path, 0o777)
        except Exception:
            print('Failed to create directory {}; could not create PDF'.format(packing_list_path))
            return

    pdf_path = os.path.join(packing_list_path, '{0} {1}.pdf'.format(datetime.now().strftime('%Y-%m-%d'), name))

    pdfkit.from_string(html, pdf_path, options={'page-size': 'Letter',
                                                'zoom': '1.22',
                                                'margin-bottom': '0',
                                                'margin-left': '5',
                                                'margin-right': '2'})
    operating_system = platform.system()

    if operating_system in ['Darwin', 'Linux']:  # send ot printer on Mac
        os.system('lp "{}"'.format(pdf_path))
        # os.system('cp "{}" ~/Desktop/packing_list.pdf && open ~/Desktop/packing_list.pdf'.format(pdf_path))
    elif operating_system == 'Windows':
        os.system('PDFtoPrinter.exe "{}"'.format(pdf_path))


def my_ip_address():
    """ Discover the current IP address (other than localhost) of this machine. """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


@app.template_filter('shortname')
def shortname(section):
    """ This is a Jinja2 filter that returns a short name for each grocery
        list section (the section names must not change). """
    return NAME_DICTIONARY[section]


@app.template_filter('simplify')
def simplify(stringlist):
    """ This is a Jinja2 filter that takes a list of strings and concatenates them. """
    return ', '.join(stringlist)

@app.template_filter('translate')
def translate(word, language):
    """ This function provides a cacheing feature to reduce translation time. """
    if language == 'english':
            return word 
    else: # not english
        test = TRANSLATE_DICTIONARY.get(language, 'nope') 
        if test == 'nope': 
            print('Adding new language to dictionary.')
            TRANSLATE_DICTIONARY[language] = {}
            
        test2 = TRANSLATE_DICTIONARY[language].get(word, 'nope')
        # Look if the language/word already in dictionary. 
        if test2 == 'nope':
            TRANSLATE_DICTIONARY[language]= {word: translate_text(word, language)}
            
        return TRANSLATE_DICTIONARY[language][word]
    
def translate_text(word, language):
    """Translates text into the target language.

    Target language must be an ISO 639-1 language code.
    See https://g.co/cloud/translate/v2/translate-reference#supported_languages
    """
    import six
    from google.cloud import translate_v2 as translate
    
    import os
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] ='C:\\Users\\lpk70\\anaconda3\\envs\\pantry\\Lib\\site-packages\\PantryDriveUp\\pantry-translation-b47a2a8f1b95.json'
    
    translate_client = translate.Client()

    if isinstance(word, six.binary_type):
        word = word.decode("utf-8")

    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    result = translate_client.translate(word, target_language=language)

    #print(u"Text: {}".format(result["input"]))
    #print(u"Translation: {}".format(result["translatedText"]))
    #print(u"Detected source language: {}".format(result["detectedSourceLanguage"]))
    
    return result["translatedText"]

    
@app.route('/')
def form():
    """ Get the grocery list form. """
    language = request.args.get('language') or "english"
    return render_template('order_form.html', grocery_options=DriveThruGroceryList, language=language)


@app.route('/print', methods=['POST'])
def print_form():
    """ Receive the grocery list, prepare a packing list, and print it. """
    fam_color = {'1: Yellow': '#ffff00', '2-4: Blue': '#6464ff', '5+: Pink': '#ff69b4'}[request.form['family_size']]
    grocery_list = request.form.to_dict(flat=False)
    packing_list = render_template('packing_list.html',
                                   grocery_list=grocery_list,
                                   timestamp=datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f%z'),
                                   fam_color=fam_color)
    print_html(packing_list, request.form['full_name'])

    return "Success"


@app.route('/reprint', methods=['GET', 'POST'])
def reprint_form():
    """ (Unimplemented) Reprint a previous list. """
    return 'This feature is currently not implemented.'


if __name__ == '__main__':
    app.run(host=my_ip_address())

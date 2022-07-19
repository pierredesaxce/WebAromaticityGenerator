# Guide to add a new language :

## Requirements : 

you need Python and Flask-Babel in order to add a new language.

You can download Python 3 here : https://www.python.org/downloads/

Once that is done, you can install Flask-Babel using this terminal command :

```
pip install Flask-Babel
```

## Procedure :

This need to be done everytime new content to translate is added to the website or to add a new language.
The language by default is french (fr) so it is not needed to add it.

### Adding content to an existing translation :

If new content has been added to a html file and needs to be translated, it must be marked in the following way :

```
{{_('Text to be translated')}}
```

It is also advised to keep a copy of the current translation (messages.po) when adding new content to an existing translation as during the next the already existing language file will be wiped clean and lost.
Keeping the old version allows to copy and paste the unchanged content and avoid losing the work already done.

### Generating language file :

In the root folder, execute the following commands : 
LANG_CODE needs to be replaced with the language code corresponding to the language you want to add (English=>en, French=>fr)
```
pybabel extract -F babel.cfg -o messages.pot .
pybabel init -i messages.pot -d translations -l LANG_CODE
```

This will generate a messages.po in the translations/LANG_CODE/LC_MESSAGES. The next step is to translate everything that needs to.
This file is formatted as follow :

```
#: templates/404.html:4                     File and line where the text to translate is located
msgid "Oops! Cette page n'existe pas"       Original version of the text (in french here)
msgstr ""                                   Translated version of the text (empty here)
```

```
#: templates/404.html:4
msgid "Oops! Cette page n'existe pas"
msgstr "Oops! This page doesn't exist."     Translated version of the text (completed here)
```

Once translated, you need to compile the messages.po file using the following command :

```
pybabel compile -d translations
```

Finally, you need to indicate to the server that you've added a new language.
To do that, in the server.py file, you need to modify the LANGUAGES config and add the new language using the following format : 

'LANG_CODE' : 'Language'
example below :

```
app.config.update(dict(
    LANGUAGES={
        'en': 'English',
        'fr': 'Francais'
    }
))
```

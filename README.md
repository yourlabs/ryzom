# Ryzom: Replace HTML Templates with Python Components

## Why?

Because while frameworks like Django claim that "templates include a restricted
language to avoid for the HTML coder to shoot themself in the foot", the GoF on
the other hand states that Decorator is the pattern that is most efficient for
designing GUIs, which is actually a big part of the success encountered by
frameworks such as React.

## What?

Ryzom basically offers Python Components, with extra sauce of bleeding edge
features such as "compiling Python code to JS", and "data binding" (DOM
refreshes itself when data changes in the DB) if you enable websockets.

## State

Currently in Beta stage, we are brushing up for a production release in an Open
Source project for an NGO defending democracy, with an online voting platform
secured with homomorphic encryption, basically a Django project built on top of
microsoft/electionguard-python.

It's **not** ready for general use, but should hopefully be pretty soon...
after all, this project has been under R&D sponsored by YourLabs for years now.

## Usage

See the supported usage patterns in `src/ryzom_django_example/urls.py` which
provides commented code using supported Ryzom APIs.

## Demo

```
git clone https://yourlabs.io/oss/ryzom.git
sudo -u postgres createdb -O $UTF -E UTF8 ryzom_django_example
cd ryzom
pip install -e .
./manage.py migrate
./manage.py runserver

# to run tests:
py.test
```

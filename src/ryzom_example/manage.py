#!/usr/bin/env python
from ryzom import manage


def main(settings_module=None):
    manage.main(settings_module or 'ryzom_example.settings')

if __name__ == '__main__':
    main()

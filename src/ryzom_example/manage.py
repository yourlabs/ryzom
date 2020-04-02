#!/usr/bin/env python
from ryzom.manage import main as ryzom_main


def main(settings_module='ryzom_example.settings'):
    ryzom_main(settings_module)


if __name__ == '__main__':
    main()

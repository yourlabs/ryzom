import sys
from .tokenizer import pyxl_tokenize, pyxl_untokenize

if __name__ == "__main__":
    with open(sys.argv[1], 'r') as file:
        print(pyxl_untokenize(pyxl_tokenize(file.readline)))

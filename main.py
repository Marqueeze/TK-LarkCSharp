import os
from sys import argv
import mel_parser
from analyzer import Analyzer
from code_generator import CodeGenerator


def main(prog):
    prog = mel_parser.parse(prog)
    #print(*prog.tree, sep=os.linesep)
    a = Analyzer()
    the_prog, _ = a.analyze(prog)
    # print(*the_prog.tree, sep=os.linesep)
    cg = CodeGenerator()
    cg.generate(the_prog)


if __name__ == "__main__":
    f = open(argv[1])
    main(os.linesep.join(f.readlines()))

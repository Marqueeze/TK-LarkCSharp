import os
import mel_parser
from analyzer import Analyzer
from code_generator import CodeGenerator


def main():
    prog = '''
        public void func(int i, int j){
       do {
           i = i + 1;
       }while(i<j);
    }
    '''
    prog = mel_parser.parse(prog)
    # print(*prog.tree, sep=os.linesep)
    a = Analyzer()
    the_prog, _ = a.analyze(prog)
    #print(*the_prog.tree, sep=os.linesep)
    cg = CodeGenerator()
    cg.generate(the_prog)


if __name__ == "__main__":
    main()

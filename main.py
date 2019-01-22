import os
import mel_parser
from analyzer import Analyzer
from code_generator import CodeGenerator


def main():
    prog = '''
        public int func(int b, int i){
            func2(b+2);
            return b;
        }
        
        public string func2(int i){
           return "foo";
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

import os
import mel_parser
from analyzer import Analyzer
from code_generator import CodeGenerator


def main():
    prog = '''
        int g = 1 - 2 - 3;
        int t = 4 + 5;
        double wow2 = 5.1 + 5;
        string[] str1 = new string[6];
        double[] dbl = new double[] { 2.1, 6.7, 14.91 };
        
        public int func(int b, int i){
            double w = g + b;
            return b;
        }
        
        private int func2(double db, int i){
            return 7;
        }
    '''
    prog = mel_parser.parse(prog)
    # print(*prog.tree, sep=os.linesep)
    a = Analyzer()
    the_prog, _ = a.analyze(prog)
    print(*the_prog.tree, sep=os.linesep)
    cg = CodeGenerator()
    cg.generate(the_prog)


if __name__ == "__main__":
    main()

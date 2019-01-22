import os
import mel_parser
from analyzer import Analyzer
from code_generator import CodeGenerator


def main():
    prog = '''
        
        int g = 1 - 2 - 3;
        double t = 4 + 5;
        
        
        string[] arr = new string[10];
        int[] kek = new int[]{ 1, 2, 3, 4, 5 };
        
        void pppppppp(int abc, char[] thhhh) { }
        
        
        public int what(int a, int b) 
        {
            for (int i = 0; i < 10; i = i + 1){
                b = b + 1;
            }
            int gh = 100 * a - b / 23;
            char abc = 'a';
            if (a > b) {
                return 0;
            }
            int[] c = new int[]{5, 4, 6, 5, 1};
            string fff = "asd";
            return c[0];
        }
        
        
        public static void whatElse(int a, int b) 
        {
            int c = 10 + 15 - what(a, a);
            while (true)
            {
                a = a + b;
                do
                {
                    b = a - b * b;
                }
                while (g + t > t)
            }
            return;
        }
    '''
    prog = mel_parser.parse(prog)
    # print(*prog.tree, sep=os.linesep)
    a = Analyzer()
    the_prog, _ = a.analyze(prog)
    gen = CodeGenerator(the_prog, '')
    gen.generate()
    # try:
    #     a.analyze(prog)
    # except ValueError as e:
    #     print(e)
    # print(*the_prog.tree, sep=os.linesep)
    # print(gen.generate()[0])
    # print(gen.constants)


if __name__ == "__main__":
    main()

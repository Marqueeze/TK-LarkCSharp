import os
import mel_parser
from analyzer import *


def main():
    prog = '''
        int g = 90;
        string g3 = "kek";
        int t = 4 + 5;
        
        t = 10 * 12 - (g + g);
    
        
        for (int i = 0, j = 8; ((i <= 5)); i = i + 1)
            for(; t < g;)
                if (t > 7 + g) {
                    t = t + g * (2 - 1) + 0;  // comment 2
                    g3 = "98\tура";
                }
        for(;;);
        
        string[] arr = new string[10];
        int[] kek = new int{ 1, 2, 3, 4, 5 };
        
        
        public int[] what(int a, int b) 
        {
            return (a + b) * 10;
        }
        
        
        public static void whatElse(int a, int b) 
        {
            int c = what(a, b);
            while (a > b)
            {
                a = a + b;
                do
                {
                    b = a - b * b;
                    c = 100 * 2;
                }
                while (g + t > c)
            }
        }
    '''
    prog = mel_parser.parse(prog)
    a = Analyzer()
    a.form_scope(prog)
    THE_prog, _ = a.analyze(prog)
    # try:
    #     a.analyze(prog)
    # except ValueError as e:
    #     print(e)
    print(*THE_prog.tree, sep=os.linesep)


if __name__ == "__main__":
    main()

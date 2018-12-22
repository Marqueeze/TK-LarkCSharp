import os
import mel_parser
from analyzer import *


def main():
    prog = '''
        int g, g2 = g, g = 90;
        string g3 = g * g2 + g;
    
        a = input(); b = input();  /* comment 1
        c = input();
        */
        for (int i = 0, j = 8; ((i <= 5)) && g; i = i + 1, print(5))
            for(; a < b;)
                if (a > 7 + b) {
                    c = a + b * (2 - 1) + 0;  // comment 2
                    b = "98\tура";
                }
                else if (f)            
                    output(c + 1, 89.89);
        for(;;);
        
        string[] arr = new string[10];
        int[] kek = new int{ 1, 2, 3, 4, 5 };
        
        
        public int[] what(int a, string b) 
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
                    b = a - b * y;
                    c = 100 * 2;
                }
                while (g + g2 > c)
            }
        }
    '''
    prog = mel_parser.parse(prog)
    a = Analyzer()
    a.form_scope(prog)
    try:
        a.analyze(prog)
    except ValueError as e:
        print(e)
    print(type(True).__name__)
    print(*prog.tree, sep=os.linesep)


if __name__ == "__main__":
    main()

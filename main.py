import os
import mel_parser
from analyzer import Analyzer
# from code_generator import CodeGenerator
from code_generator import CodeGenerator


def main():
    prog = '''
        int g = 1 - 2 - 3;
        bool axx = true;
        double dbl = 4.1;
        string strng = "Sosi";
        int[] bbb = new int[] {2, 3};
        int[] aaa = new int[10];
        aaa[0] = 10;
        string g3 = "kek";
        int t = 4 + 5;
        double wow = g + t;
        t = 10 * 12 - (g + g);
        double s = 90;
    
        
        for (int i = 0, j = 8; ((i <= 5)); i = i + 1)
            for(; t < g;)
                if (t > 7 + g) {
                    t = t + g * (2 - 1) + 0;  // comment 2
                    g3 = "98\tура";
                }
        for(;;);
        
        string[] arr = new string[10];
        int[] kek = new int[]{ 1, 2, 3, 4, 5 };
        
        
        public int[] what(int a, int b) 
        {
            int[] c = new int[]{5, 4, 6, 5, 1};
            string fff = "asd";
            return c;
        }
        
        
        public static void whatElse(int a, int b) 
        {
            int[] c = what(a, b);
            c[a + b] = 0;
            int e = c[3];
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
    print(*the_prog.tree, sep=os.linesep)
    cg = CodeGenerator()
    cg.generate(the_prog)


if __name__ == "__main__":
    main()

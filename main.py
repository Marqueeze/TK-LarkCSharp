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
    # cg = CodeGenerator(argv[1])
    cg = CodeGenerator("output.txt")
    cg.generate(the_prog)


if __name__ == "__main__":
    # f = open(argv[1])
    # main(os.linesep.join(f.readlines()))
    main('''
        int[] arr = new int[] {4, 3, 2};
string str = "Hello";

public int factorial(int n)
{
int s = 1;
for (int i = 1; i <= n; i = i + 1)
{
	s = s * i;
}
return s;
}

public void do(){
int out = factorial(3);
writeline("6");
out = arr[1];
writeline("3");
} ''')

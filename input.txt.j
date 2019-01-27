.class public test
.super java/lang/object
.field [i arr
.field ljava/lang/string; str


.method public <init>()v
l0:
aload 0
invokespecial java/lang/object/<init>()v
l1:
aload 0
bipush 3
newarray t_int
dup
bipush 4
iastore
dup
bipush 3
iastore
dup
bipush 2
iastore
astore i
putfield test.arr : [i
l2:
aload 0
ldc "hello"
putfield test.str : ljava/lang/string;
return
.end method

.method public factorial(i)i
l0:
bipush 1
istore 2
l1:
bipush 1
istore 3
l2:
iload 3
iload 1
if_icmpgt l3
l4:
iload 2
iload 3
imul
istore 2
l5:
iload 3
bipush 1
iadd
istore 3
goto l2
l3:
iload 2
ireturn
.end method
.method public do()v
l0:
aload 0
bipush 3
invokevirtual test.factorial (i)i
istore 1
l1:
ldc2_w 6
getstatic java/lang/system.out : ljava/io/printstream;
none
invokevirtual java/io/printstream.println (ljava/lang/string;)v
l2:
aload 0
getfield 1
ldc "int(const, v_type - 1)"
iload
istore 1
l3:
ldc2_w 3
getstatic java/lang/system.out : ljava/io/printstream;
none
invokevirtual java/io/printstream.println (ljava/lang/string;)v
l4:
return
.end method


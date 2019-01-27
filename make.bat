@echo off

if "%1"=="" (
  echo Usage %~nx0 ^<filename^>
  exit /b
)

set PYTHON=C:\Users\domin\Projects\PycharmProjects\TK-LarkCSharp\venv\Scripts\Python.exe
set JBC_SAMPLE=C:\Users\domin\OneDrive\Рабочий стол\JBC
set TK=C:\Users\domin\Projects\PycharmProjects\TK-LarkCSharp

set JASPER="java.exe" -jar "%JBC_SAMPLE%\jasper\jasper.jar"
set JASMIN="java.exe" -jar "%JBC_SAMPLE%\jasmin-2.4\jasmin.jar"



set FILENAME=%~nx1

del %FILENAME%.class %FILENAME%.j >nul 2>nul

"%PYTHON%" "%TK%\main.py" "%FILENAME%"
%JASMIN% %FILENAME%.j

exit /b

%JAVAC% -target 1.5 -source 1.5 %FILENAME%.java
rem %JAVAP% -p -c %FILENAME%.class >%FILENAME%.javap
%JASPER% %FILENAME%.class
del %FILENAME%.class >nul 2>nul
%JASMIN% %FILENAME%.j

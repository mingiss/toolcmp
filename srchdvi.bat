:: ieško failo %1.dvi, jei randa, išvalo failą diff.log
:: galima naudoti kaip toolcmp.cfg komandą DiffCmd:
::      DiffCmd = D:/kp/src/vtex/tex/toolcmp/toolcmp_src/srchdvi

dir > diff.log
if exist "%~n1.dvi" cat nul > diff.log

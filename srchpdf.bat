:: ieško pdf-inių projektų
:: diff.log išvalo, tik jei dokumento aplanke yra .pdf failas, bet nėra .dvi
:: galima naudoti kaip toolcmp.cfg komandą DiffCmd:
::      DiffCmd = D:/kp/src/vtex/tex/toolcmp/toolcmp_src/srchpdf

dir > diff.log
if exist "%~n1.pdf" cat nul > diff.log
if exist "%~n1.dvi" dir > diff.log

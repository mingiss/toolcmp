:: grupinio failų kompiliavimo rezultato lyginimo pavyzdys
:: TODO: sėkmingo dvidiff.log atpažinimui reiktų papildomo įrankio, kuris numestų paskutinę eilutę "Elapsed time: 7.76599979401"
Z:/data/texgr/utils/texware/dvidiffer.exe -s -f -w -o %1\dvidiff.dvi %1.dvi.sav %1.dvi > dvidiff.log 2>&1
diff dvidiff.log %~dp0dvidiff.log > diff.log

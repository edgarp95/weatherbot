Ilmaennustuse bot, loodud aine "Tehisintellekt" raames

Mida programm oskab:
* Tervitada kasutajat (tervitussõnadena arvestatakse tere, hei, privet, hi, tsau)
* Opereerida kasutajanimega (kui kasutaja on ennast tutvustanud, nt mina olen <nimi> või minu nimi on <nimi>
* Oskab valitud linna kohta ilmaennustust anda: oskab anda teavet kogu ilma kohta üldiselt (Kui nt küsida "Mis ilm on Tartus") ja oskab ka eraldi (nt Kui soe on Tartus). Ilma kohta annab teada: temperatuuri, niiskuse, rõhu, tuulekiiruse, tuulesuuna, missugune on ilm (pilvine, lumine)
* Oskab anda tutvustavat infot linna asukoha kohta (nt Kus asub Tartu?). Annab infot riigi kohta, kus linn asub ja linna koordinaadid

Lisavõimalused (boonuse jaoks):
* Oskab nimetada süsteemi kellaaega (nt Mis kell on? Kas ütleksid kella?)
* Saab öelda mitut ilmatingimust korraga (nt Kui soe ja niiske on Tartus?)
* Oskab käänata nimesid
* Oskab eestikeelsed kohanimed tõlkida inglise keelde api jaoks (nt Moskva -> Moscow, Pariis -> Paris , Võru -> Voru). Vajab googletrans importi! Seda saab installeerida käsuga $ pip install googletrans, või siis importida otse IDEst (vajutada importi peale ja install package). Juhul kui sellega tekkib mingeid probleeme, palun kirjutage!

Võimalikud probleemid:
* Mõned kohanimed töödeldakse valesti. Nt Los Angeles mingil põhjusel muutub "The Angels" <- thanks google translate
* "from googletrans import Translator" peab importima (import package, kõik ülejäänud peaks tegema see ise)
* Rasked linnanimed nagu Kohtla-Järve, ei tule süsteemil välja. Saadakse Kohtla-Järv, mis pole õige...
* Kui küsida üldiselt ilma kohta, siis tagastab api ühesõnalise ilma kirjelduse (nt Clear), need asjad on vastavalt tõlgitud eesti keelde (nt Clear - selge), kui aga satub mingi sõna, mida ma pole näinud, siis viskab programm erindi, sest sõnastikus seda sõna pole (loodetavasti sai enamus sõnadest kirjeldatud)

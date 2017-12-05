import requests, re, datetime, sys
from colorama import init, Fore, Back, Style
init() #Colorama

def printFaellig(data, c1, c2, d1, d2, temp):
    if(data.find("Keine Verlängerung möglich, Medium wurde vorgemerkt") != -1):
        print(Style.BRIGHT+c1+"   Fällig am      "+temp+" ("+str((d2-d1).days+1)+" Tag(e) verbleibend)"+Style.RESET_ALL)
        print(Style.BRIGHT+Fore.RED+"   vorgemerkt"+Style.RESET_ALL)
    elif(data.find("Keine Verlängerung möglich, Verlängerungslimit erreicht") != -1 or data.find("Dreimal verlängert") != -1 or data.find("Viermal verlängert") != -1): # "Viermal" noch nicht in freier Wildbahn gesehen
        print(Style.BRIGHT+c1+"   Fällig am      "+temp+" ("+str((d2-d1).days+1)+" Tag(e) verbleibend)"+Style.RESET_ALL)
        print(Style.BRIGHT+Fore.RED+"   nicht mehr verlängerbar"+Style.RESET_ALL)
    elif(data.find("Dieses Medium kann nicht verlängert werden") != -1):
        print(Style.BRIGHT+c1+"   Fällig am      "+temp+" ("+str((d2-d1).days+1)+" Tag(e) verbleibend)"+Style.RESET_ALL)
        print(Style.BRIGHT+Fore.RED+"   nicht verlängerbar"+Style.RESET_ALL)
    elif(data.find("Heute verlängert oder ausgeliehen") != -1):
        print(Style.BRIGHT+c1+"   Fällig am      "+temp+" ("+str((d2-d1).days+1)+" Tag(e) verbleibend)"+Style.RESET_ALL)
        print(Style.BRIGHT+Fore.GREEN+"   gerade verlängert ;)"+Style.RESET_ALL)
    else:
        print(Style.BRIGHT+c2+"   Fällig am      "+temp+" ("+str((d2-d1).days+1)+" Tag(e) verbleibend)"+Style.RESET_ALL)

def parseSingleEntry(data):
    # Titel
    p2 = re.compile('(<a href=\"/medium/\?cn=[a-zA-Z0-9]{,20}\">(.{,48})</a>)')
    print (Style.BRIGHT+Fore.WHITE+" "+p2.findall(data)[0][1]+Style.RESET_ALL)
    
    # Autor
    p3 = re.compile("Author\">(.{,100})</a>")
    if (len(p3.findall(data))>0):
        print("   Autor: ",p3.findall(data)[0])
    else:
        print("   Autor:")
    
    # Medienart
    p5 = re.compile("<em class=\"medienart.{,50}\">(.{,100})</em>")
    if (len(p5.findall(data))>0):
        print("   Typ:",p5.findall(data)[0])
    else:
        print("   Typ:")
    
    # Ausgeliehen
    p6 = re.compile('Ausgeliehen am (.{10})<br/> in der Bücherhalle (.{,50})</p>')
    print("   Ausgeliehen am",p6.findall(data)[0][0],"("+p6.findall(data)[0][1]+")")
    
    # Fällig
    # heute oder vorher fällig:        rot
    # in den nächsten 3 Tagen fällig:  gelb
    # beliebig fällig, unverlängerbar: gelb
    # in den nächsten 7 Tagen fällig:  grün
    # sonstig fällig:                  unfarbig
    p4 = re.compile('Fällig am <strong>(.{10})</strong><br/>')
    temp = p4.findall(data)[0]
    d1 = datetime.datetime.now()
    d2 = datetime.datetime(int(temp[6:10]), int(temp[3:5]), int(temp[0:2]))
    if (((d2-d1).days+1) <= 0):
        # heute fällig
        c1 = Fore.RED
        c2 = Fore.RED
        printFaellig(data, c1, c2, d1, d2, temp)
    elif (((d2-d1).days+1) > 7):
        # irgendwann fällig
        c1 = Fore.YELLOW
        c2 = Style.RESET_ALL
        printFaellig(data, c1, c2, d1, d2, temp)
    elif (((d2-d1).days+1) > 3):
        # in mehr als 3 Tagen fällig
        c1 = Fore.YELLOW
        c2 = Fore.GREEN
        printFaellig(data, c1, c2, d1, d2, temp)
    else:
        # in 1 bis 3 Tagen fällig
        c1 = Fore.YELLOW
        c2 = Fore.YELLOW
        printFaellig(data, c1, c2, d1, d2, temp)
    print("")

def listMedia(ID, PIN):
    raw = requests.post("https://buecherhallen.de/entliehene_medien", data={'borrowerNumber': ID, 'pin': PIN})
    rawText = raw.text
    rawText = rawText.replace('\n', '') # remove LF
    rawText = rawText.replace('\r', '') # remove CR
    rawText = rawText.replace('&amp;', '&')   # & anzeigbar machen
    rawText = rawText.replace('n&#771;', 'ñ') # ñ anzeigbar machen
    rawText = rawText.replace('a&#776;', 'ä') # ä anzeigbar machen
    rawText = rawText.replace('o&#776;', 'ö') # ö anzeigbar machen (ungetestet!)
    rawText = rawText.replace('u&#776;', 'ü') # ü anzeigbar machen (ungetestet!)
    while (rawText.find("  ") != -1):   # remove all "  ", maximum needed is " "
        rawText = rawText.replace('  ', ' ')

    pattern = re.compile('<li class=\"clearfix.{,1000}li>') # ich hoffe, die Einträge bleiben jeweils unter 1000 Zeichen, ansonsten: Problem!
    items = pattern.findall(rawText)

    print(Style.BRIGHT+Fore.WHITE+" "+ID+Style.RESET_ALL)
    # Hier nochmal vergleichen mit "Entliehene Medien x" auf der Website
    print(" "+str(len(items))+" Medien ausgeliehen:\n")

    for i in range(len(items)):
        parseSingleEntry(items[i])

for i in range(len(sys.argv)//2):
    #print(sys.argv[2*i+1], sys.argv[2*i+2])
    listMedia(sys.argv[2*i+1], sys.argv[2*i+2])
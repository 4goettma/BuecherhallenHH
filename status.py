#!/usr/bin/env python3
import requests, re, datetime, sys
from colorama import init, Fore, Back, Style
init() #Colorama
DEBUG = True
DEBUG = False

# TODO: überarbeiten mit Regex statt find(), um unbekannte Verlängerungs-Hinderungsgründe ausschließen zu könenn
def printFaellig(data, c1, c2, d1, d2, temp):
    global renewCounter
    temp = temp[0]+"."+temp[1]+"."+temp[2]
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
        print(Style.BRIGHT+c2+"   Fällig am      "+temp+" ("+str((d2-d1).days+1)+" Tag(e) verbleibend)"+Style.RESET_ALL)
        print(Style.BRIGHT+Fore.GREEN+"   gerade verlängert ;)"+Style.RESET_ALL)
    else:
        print(Style.BRIGHT+c2+"   Fällig am      "+temp+" ("+str((d2-d1).days+1)+" Tag(e) verbleibend)"+Style.RESET_ALL)
        # Medium wurde als nicht nicht verlängerbar eingestuft, daher sollte es verlängerbar sein (andernfalls Fehler beim Parsen)
        renewCounter += 1

def parseSingleItem(data):
    # Titel
    # r[0][0] = "T018311451"
    # r[0][1] = "Computerhardware für Fortgeschrittene"
    r = re.compile('<a href=\"\/medium\/\?cn=([a-zA-Z0-9]*?)\">(.*?)<\/a>').findall(data)
    print (Style.BRIGHT+Fore.WHITE+" "+r[0][1]+Style.RESET_ALL+" (", end="")

    # Mediennummer
    # r[0] = "M61 397 117 9"
    r = re.compile('Mediennummer: (.*?)<br\/>').findall(data)
    print (r[0]+")")

    # Autor
    # r[0] = "Eifert, Klaus"
    r = re.compile("df=Author\">(.*?)<\/a>").findall(data)
    if (len(r) > 0):
        print("   Autor:",r[0])
    else:
        print("   Autor:")
    
    # Medienart
    # r[0] = "Buch Erwachsene"
    r = re.compile("<em class=\"medienart.*?\">(.*?)</em>").findall(data)
    if (len(r) > 0):
        if (r[0] == "Blu-Ray-Disk" or r[0] == "DVD" or r[0] == "Bestseller"):
            print("   Typ:",Style.BRIGHT+Fore.BLUE+r[0]+Style.RESET_ALL)
        else:
            print("   Typ:",r[0])
    else:
        print("   Typ:")
    
    # Ausgeliehen
    # r[0][0] = "10.10.2017"
    # r[0][1] = "Eimsbüttel"
    r = re.compile('Ausgeliehen am (\d\d\.\d\d\.\d\d\d\d)<br/> in der Bücherhalle (.*?)</p>').findall(data)
    print("   Ausgeliehen am",r[0][0],"("+r[0][1]+")")
    
    # Fälligkeit
    #   heute oder vorher fällig:        rot
    #   in den nächsten 3 Tagen fällig:  gelb
    #   beliebig fällig, unverlängerbar: gelb
    #   in den nächsten 7 Tagen fällig:  grün
    #   sonstig fällig:                  unfarbig
    #r[0] = ('08', '12', '2017')
    r = re.compile('Fällig am <strong>(\d\d)\.(\d\d)\.(\d\d\d\d)</strong>').findall(data)
    d1 = datetime.datetime.now()
    d2 = datetime.datetime(int(r[0][2]), int(r[0][1]), int(r[0][0]))
    if (((d2-d1).days+1) <= 0):
        # heute fällig
        c1 = Fore.RED
        c2 = Fore.RED
    elif (((d2-d1).days+1) > 7):
        # irgendwann fällig
        c1 = Fore.YELLOW
        c2 = Style.RESET_ALL
    elif (((d2-d1).days+1) > 3):
        # in mehr als 3 Tagen fällig
        c1 = Fore.YELLOW
        c2 = Fore.GREEN
    else:
        # in 1 bis 3 Tagen fällig
        c1 = Fore.YELLOW
        c2 = Fore.YELLOW
    printFaellig(data, c1, c2, d1, d2, r[0])

    print("")

def abort():
    print(Style.BRIGHT+Fore.RED+" Fehler beim Parsen, bitte manuell überprüfen!"+Style.RESET_ALL)
    exit(0)

def listMedia(ID, PIN):
    global renewCounter, renewCounterMax
    raw = requests.post("https://buecherhallen.de/entliehene_medien", data={'borrowerNumber': ID, 'pin': PIN})
    rawText = raw.text
    rawText = rawText.replace('\n', '') # remove LF
    rawText = rawText.replace('\r', '') # remove CR
    rawText = rawText.replace('	', ' ') # remove tabs
    rawText = rawText.replace('&amp;', '&')   # & anzeigbar machen
    rawText = rawText.replace('n&#771;', 'ñ') # ñ anzeigbar machen
    rawText = rawText.replace('a&#776;', 'ä') # ä anzeigbar machen
    rawText = rawText.replace('o&#776;', 'ö') # ö anzeigbar machen (ungetestet!)
    rawText = rawText.replace('u&#776;', 'ü') # ü anzeigbar machen (ungetestet!)
    while (rawText.find("  ") != -1):   # remove all "  ", maximum needed is " "
        rawText = rawText.replace('  ', ' ')

    if(rawText.find("Wir bitten um Entschuldigung, leider steht Ihr Kundenkonto aus technischen Gründen im Augenblick nicht zur Verfügung. Bitte versuchen Sie es später noch einmal.") != -1):
        print(" Wir bitten um Entschuldigung, leider steht Ihr Kundenkonto aus technischen Gründen im Augenblick nicht zur Verfügung. Bitte versuchen Sie es später noch einmal.\n")
        abort()

    if (DEBUG): print(rawText)

    #renewCounter(Max) initialisieren
    renewCounter = 0
    r = re.compile('([\d]+) der ([\d]+) von Ihnen entliehenen Medien können verlängert werden').findall(rawText)
    if (len(r) > 0):
        renewCounterMax = int(r[0][0])
    else:
        renewCounterMax = 0

    # Kontonummer ausgeben
    print(Style.BRIGHT+Fore.WHITE+" "+ID+Style.RESET_ALL)

    # die einzelnen Medien-Blöcke parsen
    items = re.compile('<li class=\"clearfix.*?li>').findall(rawText)

    r = re.compile('<ul class=\"nav lev-1 konto\"><li class=\"active\"><strong><span class=\"txt\">Entliehene Medien <span class=\"info\">(\d+)<\/span><\/span><\/strong><\/li><li><a href=\"\/kontostand\/\"><span class=\"txt\">Kontostand <span class=\"info\">([-\+]?)(\d+),(\d+) &#8364;<\/span><\/span><\/a><\/li><li><a href=\"\/vormerkungen\/\"><span class=\"txt\">Vormerkungen <span class=\"info\">(\d+)<\/span><\/span><\/a><\/li><li><a href=\"\/vormerkguthaben\/\"><span class=\"txt\">Vormerkguthaben <span class=\"info\">([-\+]?)(\d+),(\d+) &#8364;<\/span><\/span><\/a><\/li>').findall(rawText)
    if (DEBUG): print(len(items), r[0][0])
    # Wenn die Anzahl der Elemente (geparst) nicht mit der Anzahl der Medien (angegeben) übereinstimmt
    if(len(items) != int(r[0][0])):
        abort()
    else:
        if (str(r[0][1]) == "-" and (int(r[0][2]) != 0 or int(r[0][3]) != 0)):
            print("   Kontostand:     ",Style.BRIGHT+Fore.RED+str(r[0][1])+str(r[0][2])+"."+str(r[0][3])+" €"+Style.RESET_ALL)
        else:
            if(len(str(r[0][1])) == 0):
                spacer = " "
            else:
                spacer = ""
            print("   Kontostand:     ",spacer+str(r[0][1])+str(r[0][2])+"."+str(r[0][3])+" €")
        print("   Vormerkungen:    ",str(r[0][4]))
        if(len(str(r[0][5])) == 0):
            spacer = " "
        else:
            spacer = ""
        print("   Vormerkguthaben:",spacer+str(r[0][5])+str(r[0][6])+"."+str(r[0][7])+" €")
        print("")
        print(" "+str(r[0][0])+" Medien ausgeliehen:\n")
        for item in items:
            parseSingleItem(item)
        if(renewCounter != renewCounterMax):
            print(Style.BRIGHT+Fore.RED+" Achtung:\n  Es sind vermutlich (weitere) Medien nicht verlängerbar! Bitte manuell überprüfen!"+Style.RESET_ALL)
        if(rawText.find("Ihr Kundenkonto ist derzeit gesperrt.") != -1):
            print(Style.BRIGHT+Fore.RED+" Achtung:\n  Ihr Kundenkonto ist derzeit gesperrt."+Style.RESET_ALL)

def main():
    if (len(sys.argv) <= 1 or (len(sys.argv) == 2 and sys.argv[1] == "--help")):
        print("usage: "+sys.argv[0]+" [[Nummer der Kundenkarte] [Passwort/PIN]]\nEs können mehrere Konten mit einem Aufruf abgefragt werden, indem mehrere Zugangsdaten-Paare angegeben werden!")
    else:
        for i in range(len(sys.argv)//2):
            if (DEBUG): print(sys.argv[2*i+1], sys.argv[2*i+2])
            listMedia(sys.argv[2*i+1], sys.argv[2*i+2])
            print("\n\n")

if __name__ == "__main__":
    # execute only if run as a script
    main()
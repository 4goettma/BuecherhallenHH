#!/usr/bin/env python3
import datetime, re, requests, sys
from colorama import init, Fore, Back, Style
init() #Colorama

class konto():
    def __init__(self, ID, PIN):
        self.userid  = ID
        self.userpw  = PIN
        self.token   = ""
        self.cookies = False

        self.renewableCounter    = 0
        self.renewableCounterMax = 0

        r1 = requests.get("https://www.buecherhallen.de/login.html")
        self.cookies = r1.cookies
        self.token   = re.search("name=\"REQUEST_TOKEN\" value=\"(?P<token>.+?)\"", r1.text).group("token")

    def abort(self):
        print(Style.BRIGHT+Fore.RED+" Fehler beim Parsen, bitte manuell überprüfen!"+Style.RESET_ALL)
        exit(0)

    def requestStatus(self):
        r1 = requests.post("https://www.buecherhallen.de/login.html",
                           data   ={'FORM_SUBMIT':   'tl_login',
                                    'REQUEST_TOKEN': self.token,
                                    'username':      self.userid,
                                    'password':      self.userpw},
                           cookies=self.cookies)
        return r1.status_code, r1.text

    def listLoans(self):
        raw = self.requestStatus()[1]
        text = raw.replace('\n', '').replace('\r', '').replace('\t', '')
        while (text.find("  ") != -1):
            text = text.replace("  ", " ")

        if(text.find("Wir bitten um Entschuldigung, leider steht Ihr Kundenkonto aus technischen Gründen im Augenblick nicht zur Verfügung. Bitte versuchen Sie es später noch einmal.") != -1):
            print(" Wir bitten um Entschuldigung, leider steht Ihr Kundenkonto aus technischen Gründen im Augenblick nicht zur Verfügung. Bitte versuchen Sie es später noch einmal.\n")
            abort()
        
        entries = re.findall("<li class=\"loans-item\">(?P<name>.+?)<\/li>", text)
        
        # Kontonummer ausgeben
        print(Style.BRIGHT+Fore.WHITE+" "+self.userid+Style.RESET_ALL)

        #renewableCounter(Max) initialisieren
        self.renewableCounter = 0
        r1 = re.search("(?P<renewable>\d+) der (\d+) von Ihnen entliehenen Medien (kann|können) verlängert werden\.", text)
        if (len(re.findall("(\d+) der (\d+) von Ihnen entliehenen Medien (kann|können) verlängert werden\.", text))):
            self.renewableCounterMax = int(r1.group("renewable"))
        else:
            self.renewableCounterMax = 0

        r2 = re.search("<ul class=\"level_1\"> <li class=\"first\"><strong class=\"first\">Entliehene Medien <span class=\"bereichsmenue-login-count\">(?P<infoMedienanzahl>\d+)<\/span><\/strong><\/li> <li><a href=\"kontostand.html\">Kontostand <span class=\"bereichsmenue-login-count\">(?P<infoKontostand>.*?)<\/span><\/a><\/li> <li><a href=\"vormerkungen.html\">Vormerkungen <span class=\"bereichsmenue-login-count\">(?P<infoVormerkungen>\d+)<\/span><\/a><\/li> <li><a href=\"vormerkguthaben.html\">Vormerkguthaben <span class=\"bereichsmenue-login-count\">(?P<infoGuthaben>.*?)<\/span><\/a><\/li> <li class=\"last\"><a href=\"kundendaten.html\" class=\"last\">Kundendaten <span class=\"bereichsmenue-login-count\"><\/span><\/a><\/li> <\/ul>", text)
        # Wenn die Anzahl der Elemente (geparst) nicht mit der Anzahl der Medien (angegeben) übereinstimmt
        if(len(entries) != int(r2.group("infoMedienanzahl"))):
            self.abort()
        else:
            # print general information
            print("   Vormerkguthaben:",r2.group("infoGuthaben"))
            print("   Vormerkungen:   ",r2.group("infoVormerkungen"))
            print("   Kontostand:     ",r2.group("infoKontostand"))
            print("")
            print(" "+r2.group("infoMedienanzahl")+" Medien ausgeliehen:\n")
            for entry in entries:
                self.listLoan(entry)
            if(self.renewableCounter != self.renewableCounterMax):
                print(Style.BRIGHT+Fore.RED+" Achtung:\n  Es sind vermutlich (weitere) Medien nicht verlängerbar! Bitte manuell überprüfen!"+Style.RESET_ALL)
            if(text.find("Ihr Kundenkonto ist derzeit gesperrt.") != -1):
                print(Style.BRIGHT+Fore.RED+" Achtung:\n  Ihr Kundenkonto ist derzeit gesperrt."+Style.RESET_ALL)

    def listLoan(self, text):        

        # Titel
        r1 = re.search("<a href=\"suchergebnis-detail\/medium\/(?P<digitalId>.+?)\.html\">(?P<title>.+?)<\/a>", text)

        # Mediennummer
        r2 = re.search("<span class=\"loans-details-value\">(?P<mediumId>.+?)<\/span>", text)

        print(Style.BRIGHT+Fore.WHITE+" "+r1.group("title")+" ("+r2.group("mediumId")+")"+Style.RESET_ALL)
        
        # Autor
        r3 = re.search("<p class=\"loans-author\">(?P<author>.*?)<\/p>", text)
        if (len(re.findall("<p class=\"loans-author\">.*?<\/p>", text))):
            print("   Autor: ", r3.group("author"))
        else:
            print("   Autor:")

        # Medienart
        r4 = re.search("<p class=\"loans-media-type-text\">(?P<type>.*?)<\/p>", text)
        if (len(re.findall("<p class=\"loans-media-type-text\">.*?<\/p>", text))):
            if (r4.group("type") in ["Bestseller", "Blu-Ray-Disk", "DVD"]):
                print("   Typ:",Style.BRIGHT+Fore.BLUE+r[0]+Style.RESET_ALL)
            else:
                print("   Typ:",r4.group("type"))
        else:
            print("   Typ:")

        # Ausleihdatum
        r5 = re.search("Ausgeliehen am:<\/strong><\/span> <span class=\"loans-details-value\">(?P<date>.*?)<\/span> <br> <span class=\"loans-details-label\"><strong>Standort:<\/strong><\/span> <span class=\"loans-details-value\">(?P<location>.*?)<\/span>", text)
        print("   Ausgeliehen am",r5.group("date"),"("+r5.group("location")+")")

        # Fälligkeit
        #   heute oder vorher fällig:        rot
        #   in den nächsten 3 Tagen fällig:  gelb
        #   beliebig fällig, unverlängerbar: gelb
        #   in den nächsten 7 Tagen fällig:  grün
        #   sonstig fällig:                  unfarbig

        r6 = re.search("F&auml;llig am <strong>(?P<dateDMY>(?P<dateD>\d{2})\.(?P<dateM>\d{2})\.(?P<dateY>\d{4}))<\/strong>", text)
        d1 = datetime.datetime.now()
        d2 = datetime.datetime(int(r6.group("dateY")), int(r6.group("dateM")), int(r6.group("dateD")))
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

        if(text.find("Keine Verlängerung möglich, Medium wurde vorgemerkt") != -1):
            # vorgemerkt
            print(Style.BRIGHT+c1+"   Fällig am      "+r6.group("dateDMY")+" ("+str((d2-d1).days+1)+" Tag(e) verbleibend)"+Style.RESET_ALL)
            print(Style.BRIGHT+Fore.RED+"   vorgemerkt"+Style.RESET_ALL)
        elif(text.find("Keine Verlängerung möglich, Verlängerungslimit erreicht") != -1 or text.find("Zweimal verlängert") != -1 or text.find("Dreimal verlängert") != -1 or text.find("Viermal verlängert") != -1): # "Viermal" noch nicht in freier Wildbahn gesehen
            # nicht mehr verlängerbar
            print(Style.BRIGHT+c1+"   Fällig am      "+r6.group("dateDMY")+" ("+str((d2-d1).days+1)+" Tag(e) verbleibend)"+Style.RESET_ALL)
            print(Style.BRIGHT+Fore.RED+"   nicht mehr verlängerbar"+Style.RESET_ALL)
        elif(text.find("Dieses Medium kann nicht verlängert werden") != -1 or text.find("Medium nicht verlängerbar") != -1):
            # nicht verlängerbar
            print(Style.BRIGHT+c1+"   Fällig am      "+r6.group("dateDMY")+" ("+str((d2-d1).days+1)+" Tag(e) verbleibend)"+Style.RESET_ALL)
            print(Style.BRIGHT+Fore.RED+"   nicht verlängerbar"+Style.RESET_ALL)
        elif(text.find("Heute verlängert oder ausgeliehen") != -1):
            print(Style.BRIGHT+c2+"   Fällig am      "+r6.group("dateDMY")+" ("+str((d2-d1).days+1)+" Tag(e) verbleibend)"+Style.RESET_ALL)
            print(Style.BRIGHT+Fore.GREEN+"   gerade verlängert ;)"+Style.RESET_ALL)
            self.renewableCounter += 1
        else:
            print(Style.BRIGHT+c2+"   Fällig am      "+r6.group("dateDMY")+" ("+str((d2-d1).days+1)+" Tag(e) verbleibend)"+Style.RESET_ALL)
            # Medium wurde als nicht nicht verlängerbar eingestuft, daher sollte es verlängerbar sein (andernfalls Fehler beim Parsen)
            self.renewableCounter += 1

        print("")

    """
    def requestRenewMedium(self, itemId, token, cookies):
        r1 = requests.post("https://www.buecherhallen.de/entliehene-medien.html",
                           data   ={'FORM_SUBMIT':   'tl_renewal_action',
                                    'REQUEST_TOKEN': token,
                                    'actionType': 'renewItem',
                                    'itemId': itemId},
                           cookies=cookies)
        if (r1.status_code == 200):
            print("Verlängern von Medium mit ID",itemId,"erfolgreich!")
        else:
            print("Verlängern von Medium mit ID",itemId," fehlgeschlagen!")
    """

def main():
    if (len(sys.argv) <= 1 or (len(sys.argv) == 2 and sys.argv[1] == "--help")):
        print("usage: "+sys.argv[0]+" [[Nummer der Kundenkarte] [Passwort/PIN]]\nEs können mehrere Konten mit einem Aufruf abgefragt werden, indem mehrere Zugangsdaten-Paare angegeben werden!")
    else:
        for i in range(len(sys.argv)//2):
            id = konto(sys.argv[2*i+1], sys.argv[2*i+2])
            id.listLoans()
            if (len(sys.argv)//2 != 1):
                print("\n\n")

if __name__ == "__main__":
    # execute only if run as a script
    main()
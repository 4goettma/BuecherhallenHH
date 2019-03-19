#!/usr/bin/env python3
import datetime, re, requests, sys
from colorama import Fore, Back, Style

class settings:
    useColorHighlighting = True
    renewWhenDaysLeft = 0
    # requires python module "readchar" to be installed
    useReadchar = True
    skipRenewConfirm = False

if (settings.useReadchar):
    import readchar

class konto:
    def __init__(self, ID, PIN):
        self.userid  = ID
        self.userpw  = PIN
        self.token   = ""
        self.cookies = False

        self.renewableCounter    = 0
        self.renewableCounterMax = 0

        r1 = requests.get("https://www.buecherhallen.de/login.html")
        # save first cookies (PHPSESSID)
        self.cookies = r1.cookies
        self.token   = re.search("name=\"REQUEST_TOKEN\" value=\"(?P<token>.+?)\"", r1.text).group("token")

    def abort(self):
        print(Style.BRIGHT+Fore.RED+" Fehler beim Parsen, bitte manuell überprüfen!"+Style.RESET_ALL)
        exit(1)

    def requestStatus(self):
        r1 = requests.post("https://www.buecherhallen.de/login.html",
                           data   ={'FORM_SUBMIT':   'tl_login',
                                    'REQUEST_TOKEN': self.token,
                                    'username':      self.userid,
                                    'password':      self.userpw},
                           cookies=self.cookies)
        # during authentification, some more cookies will be created (FE_USER_AUTH, PHPSESSID)
        self.cookies = r1.cookies
        return r1.status_code, r1.text

    def listLoans(self):
        text = self.requestStatus()[1]
        replacements = [("\n",""),("\r",""),("\t",""),("&auml;","ä"),("&ouml;","ö"),("&uuml;","ü"),("&#40;","("),("&#41;",")"),("&nbsp;"," ")]
        for i in replacements:
            text = text.replace(i[0],i[1])
        while (text.find("  ") != -1):
            text = text.replace("  ", " ")

        errorMessages = ["Ihr Kundenkonto wurde aus Sicherheitsgründen deaktiviert. Bitte wenden Sie sich an das Bibliothekspersonal.", "Wir bitten um Entschuldigung, leider steht Ihr Kundenkonto aus technischen Gründen im Augenblick nicht zur Verfügung. Bitte versuchen Sie es später noch einmal."]
        for i in errorMessages:
            if(text.find(i) != -1):
                print(" "+i+"\n")
                self.abort()
        
        entries = re.findall("<li class=\"loans-item\">(?P<name>.+?)<\/li>", text)
        
        # Kontonummer ausgeben
        print(Style.BRIGHT+Fore.WHITE+" "+self.userid+Style.RESET_ALL+"\n")

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

        r6 = re.search("Fällig am <strong>(?P<dateDMY>(?P<dateD>\d{2})\.(?P<dateM>\d{2})\.(?P<dateY>\d{4}))<\/strong>", text)
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

        if(text.find("Keine Verlängerung möglich, Medium wurde vorgemerkt") != -1 or text.find("Medium vorgemerkt") != -1):
            # vorgemerkt
            print(Style.BRIGHT+Fore.WHITE+" "+r1.group("title")+" ("+r2.group("mediumId")+")"+Style.RESET_ALL)
            print("   nicht anwendbar\n")
        elif(text.find("Keine Verlängerung möglich, Verlängerungslimit erreicht") != -1 or text.find("Zweimal verlängert") != -1 or text.find("Dreimal verlängert") != -1 or text.find("Viermal verlängert") != -1): # "Viermal" noch nicht in freier Wildbahn gesehen
            # nicht mehr verlängerbar
            print(Style.BRIGHT+Fore.WHITE+" "+r1.group("title")+" ("+r2.group("mediumId")+")"+Style.RESET_ALL)
            print("   nicht anwendbar\n")
        elif(text.find("Dieses Medium kann nicht verlängert werden") != -1 or text.find("Medium nicht verlängerbar") != -1):
            # nicht verlängerbar
            print(Style.BRIGHT+Fore.WHITE+" "+r1.group("title")+" ("+r2.group("mediumId")+")"+Style.RESET_ALL)
            print("   nicht anwendbar\n")
        elif(text.find("Heute verlängert oder ausgeliehen") != -1):
            # Verlängerung sinnfrei
            print(Style.BRIGHT+Fore.WHITE+" "+r1.group("title")+" ("+r2.group("mediumId")+")"+Style.RESET_ALL)
            print("   nicht anwendbar\n")
        else:
            # Medium wurde als nicht nicht verlängerbar eingestuft, daher sollte es verlängerbar sein (andernfalls Fehler beim Parsen)
            print(Style.BRIGHT+Fore.WHITE+" "+r1.group("title")+" ("+r2.group("mediumId")+")"+Style.RESET_ALL)
            print(Style.BRIGHT+c2+"   Fällig am      "+r6.group("dateDMY")+" ("+str((d2-d1).days+1)+" Tag(e) verbleibend)"+Style.RESET_ALL)
            self.renewableCounter += 1
            if((d2-d1).days <= settings.renewWhenDaysLeft):
                if (not settings.skipRenewConfirm and "--skip-confirm" not in sys.argv):
                    if (settings.useReadchar):
                        choice = ""
                        while(choice not in ["\r","Y","y","N","n","\x03"]):
                            print(Style.BRIGHT+Fore.WHITE+"   try to renew? [Y/n] "+Style.RESET_ALL, end="", flush=True)
                            choice = readchar.readchar()
                        print(choice)
                        if(choice in ["\r","Y","y"]):
                            self.requestRenewMedium(r2.group("mediumId"))
                        if(choice == "\x03"):
                            print(Style.BRIGHT+Fore.RED+"\n   Aborting..."+Style.RESET_ALL)
                            exit(0)
                    else:
                        choice = input("try to renew? [Y/n]")
                        if(choice in ["","Y","y"]):
                            self.requestRenewMedium(r2.group("mediumId"))
                else:
                    self.requestRenewMedium(r2.group("mediumId"))
            else:
                print("   Skipped according to configuration (renewWhenDaysLeft)")
                
            print("")

    def requestRenewMedium(self, itemId):
        r1 = requests.post("https://www.buecherhallen.de/entliehene-medien.html",
                           data   ={'FORM_SUBMIT':   'tl_renewal_action',
                                    'REQUEST_TOKEN': self.token,
                                    'actionType': 'renewItem',
                                    'itemId': itemId},
                           cookies=self.cookies)
        if (r1.status_code == 200):
            print(Fore.GREEN+"   Verlängerung von Medium mit ID",itemId,"wahrscheinlich erfolgreich!"+Style.RESET_ALL)
        else:
            print(Fore.RED+"   Verlängerung von Medium mit ID",itemId,"fehlgeschlagen!"+Style.RESET_ALL)
        print("   Alle Angeben ohne Gewähr!")

def main():
    if (len(sys.argv) <= 1 or "--help" in sys.argv):
        print("usage: ./"+sys.argv[0]+" [[Nummer der Kundenkarte] [Passwort/PIN]]+")
        print("Es können mehrere Konten mit einem Aufruf bearbeitet werden, indem mehrere Zugangsdaten-Paare angegeben werden!")
        print("")
        print("Optionen:")
        print("  --help           Diese Gebrauchsanweisung anzeigen.")
        print("  --skip-confirm  Verlängerung nicht vom Nutzer bestätigen lassen. Für automatisierten Einsatz per Skript gedacht.")
    else:
        arguments = sys.argv[1:]
        for i in ["--help","--skip-confirm"]:
            if(i in arguments):
                arguments.remove(i)
        for i in range(len(arguments)//2):
            id = konto(arguments[2*i], arguments[2*i+1])
            id.listLoans()
            if (len(arguments)//2 != 1):
                print("\n\n")

if __name__ == "__main__":
    # execute only if run as a script
    main()
#!/usr/bin/env python3
import datetime, re, requests, sys

class settings:
    printAccountStatus   = True
    # requires python module "readchar"
    useReadchar          = True
    useColorHighlighting = True
    showWeekday          = True
    debug                = False
    renewWhenDaysLeft    = 3

if (settings.useReadchar):
    import readchar

if (settings.useColorHighlighting):
    from colorama import Fore, Back, Style


class account:
    def __init__(self, ID, PIN):
        self.userid    = ID
        self.userpw    = PIN

        self.weekdays  = ['Mo, ','Di, ','Mi, ','Do, ','Fr, ','Sa, ','So, ']
        self.color     = {'Style.BRIGHT': '', 'Style.RESET_ALL': '', 'Fore.WHITE': '', 'Fore.BLUE': '', 'Fore.GREEN': '', 'Fore.YELLOW': '', 'Fore.RED': ''}
        if (settings.useColorHighlighting):
            self.color = {'Style.BRIGHT': Style.BRIGHT, 'Style.RESET_ALL': Style.RESET_ALL, 'Fore.WHITE': Fore.WHITE, 'Fore.BLUE': Fore.BLUE, 'Fore.GREEN': Fore.GREEN, 'Fore.YELLOW': Fore.YELLOW, 'Fore.RED': Fore.RED}

        # Session-Cookies und REQUEST_TOKEN erhalten
        req = requests.get('https://www.buecherhallen.de/login.html')
        self.cookies = req.cookies
        self.token   = re.search('name=\"REQUEST_TOKEN\" value=\"(?P<token>.+?)\"', req.text).group('token')


    def abort(self):
        print(self.color['Style.BRIGHT']+self.color['Fore.RED']+' Fehler beim Parsen!'+self.color['Style.RESET_ALL'])
        exit(1)


    def requestLoanList(self):
        # Übersicht über ausgeliehene Medien abrufen (erste Seite nach Absenden des Login-Formulars)
        req = requests.post('https://www.buecherhallen.de/login.html',
                           data   ={'FORM_SUBMIT':   'tl_login',
                                    'REQUEST_TOKEN': self.token,
                                    'username':      self.userid,
                                    'password':      self.userpw},
                           cookies=self.cookies)

        if(settings.debug):
            with open(f'debug_{self.userid}_{int(datetime.datetime.now().timestamp())}.htm', 'w') as f:
                f.write(req.text)
            global tmp
            tmp = req.text

        return {'status': req.status_code, 'src': req.text}


    def listLoans(self):
        src = self.requestLoanList()['src']

        errorMessages = ["Ihr Kundenkonto wurde aus Sicherheitsgründen deaktiviert. Bitte wenden Sie sich an das Bibliothekspersonal.", "Wir bitten um Entschuldigung, leider steht Ihr Kundenkonto aus technischen Gründen im Augenblick nicht zur Verfügung. Bitte versuchen Sie es später noch einmal."]
        for m in errorMessages:
            if(m in src):
                print(f' {m}\n')
                self.abort()

        accountData = {
            # Anzahl entliehener Medien
            'Medienanzahl': re.search('<li class=\"odd\"><a href=\"entliehene-medien\.html\" class=\"odd\"><span class=\"navbar-submenu-account-text\">Entliehene Medien</span> <span class=\"navbar-submenu-account-count\">(.+)</span></a></li>',src).group(1),
            # ggf. fällige Gebühren / Guthaben
            'Kontostand': re.search('<li class=\"even\"><a href=\"kontostand.html\" class=\"even\"><span class=\"navbar-submenu-account-text\">Kontostand</span> <span class=\"navbar-submenu-account-count\">(.+) €</span></a></li>',src).group(1),
            # Vorbestellungen / Vorbestellungen
            'Vorbestellungen': re.search('<li class=\"odd\"><a href=\"vorbestellungen.html\" class=\"odd\"><span class=\"navbar-submenu-account-text\">Vorbestellungen</span> <span class=\"navbar-submenu-account-count\">(.+)</span></a></li>',src).group(1),
            # Vorbestellguthaben
            'Vorbestellguthaben': re.search('<li class=\"even\"><a href=\"vorbestellguthaben.html\" class=\"even\"><span class=\"navbar-submenu-account-text\">Vorbestellguthaben</span> <span class=\"navbar-submenu-account-count\">(.+) €</span></a></li>',src).group(1),
        }

        r = re.search('(?P<media_renewable>\d+) der (?P<media_total>\d+) von Ihnen entliehenen Medien (kann|k(&ouml;|ö)nnen) verlängert werden\.', src)
        accountData['verlängerbar'] = r.group('media_renewable')

        # Kontonummer ausgeben
        print(self.color['Style.BRIGHT']+self.color['Fore.WHITE']+' '+self.userid+self.color['Style.RESET_ALL'])

        # größerer Abschnitt, welcher später weiter geparst werden muss
        loans = re.findall('<li class=\"search-results-item loans-search-results-item\">[\S\s]+?F(?:&auml;|ä)llig am[\S\s]+?</li>', src)

        # Wenn die Anzahl der Medien in der Liste (geparst) nicht mit der Anzahl der Medien (angegeben) übereinstimmt
        if(len(loans) != int(accountData['Medienanzahl'])):
            self.abort()
        else:
            if (settings.printAccountStatus):
                l1,l2,l3 = len(accountData['Vorbestellungen']), len(accountData['Vorbestellguthaben']), len(accountData['Kontostand'])
                print('   Vorbestellungen:      ',' '*(max(l1,l2,l3)-l1-5),accountData['Vorbestellungen'])
                print('   Vorbestellguthaben:',' '*(max(l1,l2,l3)-l2)  ,accountData['Vorbestellguthaben'],'€')
                print('   Kontostand:        ',' '*(max(l1,l2,l3)-l3)  ,accountData['Kontostand'],'€')
                print()

            print(' {} Medien ausgeliehen ({} verlängerbar):\n'.format(accountData['Medienanzahl'], accountData['verlängerbar']))
            for loan in loans:
                self.listLoan(loan)
            if('Ihr Kundenkonto ist derzeit gesperrt.' in src):
                print(self.color['Style.BRIGHT']+self.color['Fore.RED']+' Achtung:\n  Ihr Kundenkonto ist derzeit gesperrt.'+self.color['Style.RESET_ALL'])


    def listLoan(self, src):
        loan = dict()

        # Titel, URL ID
        r1 = re.search('<a href=\"suchergebnis-detail\/medium\/(?P<id_URL>.+?)\.html\">(?P<title>.+?)<\/a>', src)
        loan['title'] = r1.group('title').replace('&amp;','&')
        loan['id_URL'] = r1.group('id_URL')

        # Medien ID
        loan['id'] = re.search('<span class=\"loans-details-value\">(?P<id>.+?)<\/span>', src).group('id')

        print(self.color['Style.BRIGHT']+self.color['Fore.WHITE']+' '+loan['title']+self.color['Style.RESET_ALL']+' ['+loan['id']+']')

        # Autor
        r3 = re.search('<p class=\"loans-author\"><a .+?>(?P<author>[\w\s,]+)<\/a><\/p>', src)
        if r3:
            loan['author'] = r3.group('author')
            print('   Autor         ', loan['author'])

        # Medienart
        loan['type'] = re.search('<span class=\"search-results-media-type-text\">(?P<type>.*?)<\/span>', src).group('type')
        if (loan['type'] in ['Bestseller', 'Blu-Ray-Disk', 'DVD']):
            print('   Typ           ',self.color['Style.BRIGHT']+self.color['Fore.BLUE']+loan['type']+self.color['Style.RESET_ALL'])
        else:
            print('   Typ           ',loan['type'])

        # Ausleihdatum
        r5 = re.search('<span class=\"loans-details-value\">(?P<dateDMY>(?P<dateD>\d{2})\.(?P<dateM>\d{2})\.(?P<dateY>\d{4}))<\/span>', src)
        loan['date'] = r5.group('dateDMY')
        loan['date_D'] = r5.group('dateD')
        loan['date_M'] = r5.group('dateM')
        loan['date_Y'] = r5.group('dateY')

        loan['Standort_Ausleihe'] = re.search('Standort:<\/strong><\/span>[\S\s]*?<span class=\"loans-details-value\">(?P<location>.*?)<\/span>', src).group('location')

        weekday = ''
        if(settings.showWeekday):
            weekday = self.weekdays[datetime.datetime(int(loan['date_Y']), int(loan['date_M']), int(loan['date_D'])).weekday()]

        print('   Ausgeliehen am '+weekday+loan['date']+' ('+loan['Standort_Ausleihe']+')')

        # Fälligkeit
        #   heute oder vorher fällig:        rot
        #   in den nächsten 3 Tagen fällig:  gelb
        #   beliebig fällig, unverlängerbar: gelb
        #   in den nächsten 7 Tagen fällig:  grün
        #   sonstiges Fälligkeitsdatum:      unfarbig

        r6 = re.search('F(&auml;|ä)llig am <strong>(?P<dateDMY>(?P<dateD>\d{2})\.(?P<dateM>\d{2})\.(?P<dateY>\d{4}))<\/strong>', src)
        loan['expiration_date'] = r6.group('dateDMY')
        loan['expiration_date_D'] = r6.group('dateD')
        loan['expiration_date_M'] = r6.group('dateM')
        loan['expiration_date_Y'] = r6.group('dateY')
        d1 = datetime.datetime.now()
        d2 = datetime.datetime(int(loan['expiration_date_Y']), int(loan['expiration_date_M']), int(loan['expiration_date_D']))

        weekday = ''
        if(settings.showWeekday):
            weekday = self.weekdays[d2.weekday()]

        if (((d2-d1).days+1) <= 0):
            # heute fällig
            c1 = self.color['Fore.RED']
            c2 = self.color['Fore.RED']
        elif (((d2-d1).days+1) > 7):
            # irgendwann fällig
            c1 = self.color['Fore.YELLOW']
            c2 = self.color['Style.RESET_ALL']
        elif (((d2-d1).days+1) > 3):
            # in mehr als 3 Tagen fällig
            c1 = self.color['Fore.YELLOW']
            c2 = self.color['Fore.GREEN']
        else:
            # in 1 bis 3 Tagen fällig
            c1 = self.color['Fore.YELLOW']
            c2 = self.color['Fore.YELLOW']

        if('Keine Verlängerung möglich, Medium wurde vorgemerkt' in src or 'Medium vorgemerkt' in src):
            # vorgemerkt
            print(self.color['Style.BRIGHT']+c1+'   Fällig am      '+weekday+loan['expiration_date']+' ('+str((d2-d1).days+1)+' Tag(e) verbleibend)'+self.color['Style.RESET_ALL'])
            print(self.color['Style.BRIGHT']+self.color['Fore.RED']+'   vorgemerkt'+self.color['Style.RESET_ALL'])
        elif('Keine Verlängerung möglich, Verlängerungslimit erreicht' in src or 'Zweimal verlängert' in src or 'Dreimal verlängert' in src or 'Viermal verlängert' in src): # "Viermal verlängert" noch nicht gesehen
            # nicht mehr verlängerbar
            print(self.color['Style.BRIGHT']+c1+'   Fällig am      '+weekday+loan['expiration_date']+' ('+str((d2-d1).days+1)+' Tag(e) verbleibend)'+self.color['Style.RESET_ALL'])
            print(self.color['Style.BRIGHT']+self.color['Fore.RED']+'   nicht mehr verlängerbar'+self.color['Style.RESET_ALL'])
        elif('Dieses Medium kann nicht verlängert werden' in src or 'Medium nicht verlängerbar' in src):
            # nicht verlängerbar
            print(self.color['Style.BRIGHT']+c1+'   Fällig am      '+weekday+loan['expiration_date']+' ('+str((d2-d1).days+1)+' Tag(e) verbleibend)'+self.color['Style.RESET_ALL'])
            print(self.color['Style.BRIGHT']+self.color['Fore.RED']+'   nicht verlängerbar'+self.color['Style.RESET_ALL'])
        elif('Heute verlängert oder ausgeliehen' in src):
            # Verlängerung nicht notwendig
            print(self.color['Style.BRIGHT']+c2+'   Fällig am      '+weekday+loan['expiration_date']+' ('+str((d2-d1).days+1)+' Tag(e) verbleibend)'+self.color['Style.RESET_ALL'])
            print(self.color['Style.BRIGHT']+self.color['Fore.GREEN']+'   gerade verlängert oder ausgeliehen'+self.color['Style.RESET_ALL'])
        elif('<form action="/entliehene-medien.html" id="tl_renewal_action" method="post" class="loans-actions-form">' in src):
            # verlängerbar
            print(self.color['Style.BRIGHT']+c2+'   Fällig am      '+weekday+loan['expiration_date']+' ('+str((d2-d1).days+1)+' Tag(e) verbleibend)'+self.color['Style.RESET_ALL'])

            if((d2-d1).days < settings.renewWhenDaysLeft and '--renew' in sys.argv):
                if ('--no-confirm' not in sys.argv):
                    if (settings.useReadchar):
                        choice = ''
                        while(choice not in ['\r','Y','y','N','n','\x03']):
                            print(self.color['Style.BRIGHT']+self.color['Fore.WHITE']+'   verlängern? [Y/n] '+self.color['Style.RESET_ALL'], end='', flush=True)
                            choice = readchar.readchar()
                        print(choice)
                        if(choice in ['\r','Y','y']):
                            self.renewLoan(loan['id'])
                        if(choice == '\x03'):
                            print(self.color['Style.BRIGHT']+self.color['Fore.RED']+'\n   Abbruch...'+self.color['Style.RESET_ALL'])
                            exit(0)
                    else:
                        choice = input('verlängern? [Y/n]')
                        if(choice in ['','Y','y']):
                            self.renewLoan(loan['id'])
                else:
                    self.renewLoan(loan['id'])
            elif (settings.debug):
                print('   Restleihdauer größer als Schwellwert (settings.renewWhenDaysLeft)')

        else:
            # Fehler: kein Verlängerungsbutton vorhanden, aber kein bekannter Hinderungsgrund gefunden
            print(self.color['Style.BRIGHT']+self.color['Fore.RED']+' Achtung:\n  Es sind vermutlich (weitere) Medien nicht verlängerbar! Bitte manuell überprüfen!'+self.color['Style.RESET_ALL'])
            self.abort()
        print()


    def renewLoan(self, id):
        r = requests.post('https://www.buecherhallen.de/entliehene-medien.html',
                          data   ={'FORM_SUBMIT':   'tl_renewal_action',
                                   'REQUEST_TOKEN': self.token,
                                   'actionType':    'renewItem',
                                   'itemId':        id},
                          cookies=self.cookies)
        if (r.status_code == 200):
            print(self.color['Fore.GREEN']+'   Verlängerung von Medium mit ID',itemId,'wahrscheinlich erfolgreich!'+self.color['Style.RESET_ALL'])
        else:
            print(self.color['Fore.RED']+'   Verlängerung von Medium mit ID',itemId,'fehlgeschlagen!'+self.color['Style.RESET_ALL'])
        print('   Alle Angeben ohne Gewähr!')


def main():
    if (len(sys.argv) <= 1 or '-h' in sys.argv or '--help' in sys.argv):
        print('Verwendung: '+sys.argv[0]+' [[Nummer der Kundenkarte] [Passwort/PIN]]\nEs können mehrere Konten mit einem Aufruf abgefragt werden, indem mehrere Zugangsdaten-Paare angegeben werden!')
        print()
        print('Optionen:')
        print('  --help        Diese Gebrauchsanweisung anzeigen.')
        print('  --renew       Bei fälligen Medien nachfragen, ob diese verlängert werden sollen.')
        print('  --no-confirm  Automatische Verlängerung nicht vom Nutzer bestätigen lassen, für unbeaufsichtigten Einsatz gedacht.')
    else:
        args = [a for a in sys.argv if a not in ['--renew', '--no-confirm']]
        for i in range(len(args)//2):
            acc = account(sys.argv[2*i+1], sys.argv[2*i+2])
            acc.listLoans()
            if (len(args)//2 != 1):
                print('\n\n')


if (__name__ == '__main__'):
    main()

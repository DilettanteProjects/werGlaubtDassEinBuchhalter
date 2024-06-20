ver = 1.02 # Yippee!


#%% Init stuff(Imports, const, vars)
# Imports
###################################
import pathlib
import os
import pickle
import datetime
import csv
import copy
import cursor
import sys
###########imprts##################


# Constants
################################### 
PATH = str(pathlib.Path(__file__).parent.resolve())
##############consts###############


# Variables
###################################
settings = {'verboseLvl'    : 2, # 0=errs,dbg only, 1=important info, 2=chatty
            'debug'         : False,
            'keepSettings'  : True,
            'sheetPath'     : PATH,
            'autoSave'      : False,
            'autoLoad'      : True,
            'platform'      : 'pc',     # pc/mobile
            'maxWidthHeight': (83, 43)  # screen space on my phone
            }
recurring = {'Buergergeld'   : 1013.29,
             'Strom'         : -123.00,
             'Miete'         : -537.74,
             'Handy'         : -7.98,
             'Konto'         : -10.00,
             'HealthyGamer'  : -9.99,
            }
##############vars#################


# Helpers
###################################
months = {'01' : 'Jan',
          '02' : 'Feb',
          '03' : 'Mar',
          '04' : 'Apr',
          '05' : 'May',
          '06' : 'Jun',
          '07' : 'Jul',
          '08' : 'Aug',
          '09' : 'Sep',
          '10' : 'Oct',
          '11' : 'Nov',
          '12' : 'Dec'
          }
##############hlprs################



#%%###########init#################


#%% Functions
###################################
def increment_month(date):
    """Increments the month of a datestring, recognizes turn of year"""
    # (9) Put this in I think some TxList function? Checker?
    # Split date into integers
    intYear = int(date[:4])
    intMonth = int(date[-2:])
    # Increment,  checking for turn of year
    if intMonth == 12:
        intMonth = 1
        intYear += 1
    else:
        intMonth += 1
    # Turn back into datestring
    if intMonth < 10:
        strMonth = '0' + str(intMonth)
    else:
        strMonth = str(intMonth)
    strYear = str(intYear)
    newDate = strYear + '-' + strMonth
    return newDate

def decrement_month(date):
    """Decrements the month of a datestring, recognizes turn of year"""
    # Split date into integers
    intYear = int(date[:4])
    intMonth = int(date[-2:])
    # Increment,  checking for turn of year
    intMonth -= 1
    if intMonth == 0:
        intYear -= 1
        intMonth = 12
    # Turn back into datestring
    if intMonth < 10:
        strMonth = '0' + str(intMonth)
    else:
        strMonth = str(intMonth)
    strYear = str(intYear)
    newDate = strYear + '-' + strMonth
    return newDate


def check_Entries_vs_BankTx(listEntries, listBankTx):
    """Check the list of entries for correctness, making corrections where
    neccessary(modifies original lists)
    """
    
    def pre_checker(listEntries, listBankTx):
        """Check for already checked entries, pop corresponding Txs"""
        for entry in listEntries:
            if entry.status == 'c':
                # For each entry already 'checked', search Txlist for tx
                for tx in listBankTx:
                    if entry.associatedTx.comparer(tx):
                        if settings['verboseLvl'] >= 2:
                            print(f'Popped tx at index {listBankTx.index(tx)}')
                        elif settings['verboseLvl'] >= 1:
                            print('Popped tx')
                        listBankTx.pop(listBankTx.index(tx))
                        if settings['debug']:
                            input('continue...')
                        break
                    elif settings['verboseLvl'] >= 2:
                        print(f'Searching...({listBankTx.index(tx)}' +\
                              f'/{len(listBankTx)})')
                        
            if not listBankTx:
                if settings['verboseLvl'] >= 2:
                    print('Txlist empty')
                    break
        if settings['verboseLvl'] >= 2:
            print('Finished pre-check')
            if settings['debug']:
                input('continue...')
    
    pre_checker(listEntries, listBankTx)
    # Run once through list of BankTx
    posListBankTx = 0
    if settings['debug']:
        print(f'{posListBankTx=} {len(listBankTx)=}')
    while posListBankTx < len(listBankTx):
        # Loop through listEntries and find matches to current Tx
        # only matches amounts for now, extend this
        foundMatches = []
        for entry in listEntries:
            if entry.amount == listBankTx[posListBankTx].betrag \
                    and entry.status != 'c':
                foundMatches.append(entry)
        match len(foundMatches):
            # No match
            case 0:
                if settings['verboseLvl'] >= 2:
                    print(listBankTx[posListBankTx])
                if settings['verboseLvl'] >= 1:
                    print('No match found, skipped for now')
                posListBankTx += 1
            # Single match
            case 1:
                if settings['verboseLvl'] >= 2:
                    print('Matched:\n', listBankTx[posListBankTx],
                          '\nwith\n', 3 * ' ', foundMatches[0],
                          sep='', end=f'\n{5 * "*"}\n')
                elif settings['verboseLvl'] >= 1:
                    print('Single match found, automatically processed.')
                foundMatches[0].ingest(listBankTx[posListBankTx])
                listBankTx.pop(posListBankTx)
            # Multiple matches
            case _:
                print('Found multiple potential matches for: \n',
                      listBankTx[posListBankTx])
                for item in foundMatches:
                    print(f'({foundMatches.index(item)}){item}')
                print('\nAssociate which one(default:0)?: ', end='')
                choice = valid_choice('', *range(len(foundMatches)))
                if choice == '':
                    choice = 0                    
                foundMatches[int(choice)].ingest(listBankTx[posListBankTx])
                listBankTx.pop(posListBankTx)
        if settings['debug']:
            print(f'\n\n{posListBankTx=} {len(listBankTx)=}')
            input('continue...')
    # Finished one run of list of Tx, popped matches, 
    ## now take care of leftovers
    # Collect unchecked list entries 
    leftoverEntries = []
    for entry in listEntries:
        if entry.status != 'c':
            leftoverEntries.append(entry)
    # Go through leftover Tx, process by hand
    while len(listBankTx) > 0:
        if settings['verboseLvl'] >= 1:
            print(f'{len(listBankTx)} Leftovers \n')
        if settings['verboseLvl'] >= 2:    
            print(listBankTx[0], '\n')
        if len(leftoverEntries) > 0:
            if settings['verboseLvl'] < 2:
                print(listBankTx[0], '\n')
            for entry in leftoverEntries:
                print(f'({leftoverEntries.index(entry)}){entry}')
            print('\nAssociate number(default:0),','make (n)ew entry,',
                   'or (s)kip?: ', end='')
            choice = valid_choice('', *range(len(leftoverEntries)), 'n', 's')
            print()
        else:
            choice = 'n'
            if settings['verboseLvl'] >= 1:
                print('No unchecked entries left, creating new')
                if settings['debug']:
                    input('continue...')
        if choice == '':
            choice = 0
        if choice == 'n':
            newBetrag = listBankTx[0].betrag
            newDate = datetime.datetime.strptime(listBankTx[0].buchungstag,
                                                 '%d.%m.%Y')
            newAssociatedTx = listBankTx[0]
            if listBankTx[0].name:
                newName = listBankTx[0].name.split()[0]
            elif listBankTx[0].text == 'Entgelt/Auslagen':
                newName = listBankTx[0].text
            else:
                raise Exception('No Zahlungsbeteilugter, not Entgelt')
            activeList.entriesList.append(Entries(newBetrag, newName, newDate,
                                                  'c', newAssociatedTx))
            if settings['verboseLvl'] >= 2:
                print(f'Created new entry: \n{activeList.entriesList[-1]}')
        elif choice == 's':
            if settings['verboseLvl'] >= 2:
                print('Popping without action')
        else:    
            leftoverEntries[int(choice)].ingest(listBankTx[0])
            leftoverEntries.pop(int(choice))
        listBankTx.pop(0)
    if settings['verboseLvl'] >= 2:
        print('All transactions processed!')
    
                    
def valid_choice(*validInputs):
    """Makes sure user input is valid option
    !Unpack collections when passing!
    """
    validInputs = [str(i) for i in validInputs]
    choice = input()
    while choice not in validInputs:
        choice = input('Invalid input, try again: ')
    return choice        


def draw_frame(width=settings['maxWidthHeight'][0],
               height=settings['maxWidthHeight'][1]):
    """Draws border *around* target size,
    that means the border is at size + 1!
    """
    cursor.hme()
    for x in range(1, height + 1 + 1):
        cursor.xy(x, width + 1)
        print('#')
    cursor.xy(height + 1, 1)
    print(width * '#')
    cursor.hme()
    

def save_config(**kwargs):
    """Call this as (settings=settings, recurring=recurring, etc...)"""
    if settings['debug']:
        print('Saving the following configurations:')
        for i in kwargs.items():
            header = i[0]
            dictionary = i[1]
            print(header)
            print(dictionary)
    with open(PATH + '/' + 'cfg.ini', 'w') as file:
        for current in kwargs:
            file.write(f'[{current}]\n')
            for item in kwargs[current]:
                file.write((f' {item} : {kwargs[current][item]}\n'))


def load_config():
    if not os.path.exists(PATH + '/' + 'cfg.ini'):
        input('No config file found, creating new with defaults...')
        return save_config(settings=settings, recurring=recurring)
    # If cfg file exists
    else:
        headersDict = {}
        changed = False
        # Turn file back into dictionaries based on headers
        with open(PATH + '/' + 'cfg.ini', 'r') as file:
            for line in file:
                if line.startswith('['):
                    header = line[1:-2]
                    headersDict.setdefault(header, {})
                else:
                    partedLine = line.partition(':')
                    key = partedLine[0].strip()
                    value = partedLine[2].strip()
                    value = fix_type(value)
                    headersDict[header][key] = value
        # Match dicts from file to those in code
        for header in headersDict.keys():
            for key in headersDict[header]:
                value = headersDict[header][key]
                outsideDict = eval(header)
                if key in outsideDict:
                    if outsideDict[key] != value:
                        if settings['verboseLvl'] >= 2:
                            print(f'{header}[{key}] was ',
                                  f'{outsideDict[key]}',
                                  f'({type(outsideDict[key])}), ',
                                  f'is now {value}({type(value)})', sep='')
                        changed = True
                else:
                    changed = True
                outsideDict[key] = value
            if settings['verboseLvl'] == 1 and changed == True:
                print('Some settings have been changed from default')
    input('continue...')


def fix_type(value):
    """Check whether value should be datetime, integer, float, or boolean,
    casts accordingly. Implicitly assumes string otherwise.
    """
    if len(value) == 10 and len(value.split('-')) == 3:
        value = datetime.datetime.strptime(value, '%Y-%m-%d').date()
    elif value.isdigit():
        value = int(value)
    elif value.replace('.', '', 1).lstrip('-').isdigit():
        value = float(value)
    elif value == 'True' or value == 'False':
        if value == 'True':
            value = True
        else:
            value = False
    return value


def prep_menu():
    os.system('clear')
    if settings['platform'] == 'pc':
        draw_frame()


def menu_main(status='ok'):
    def menu_select(preChoice):
        if preChoice == '':
            prep_menu()
            for key in subMenus.keys():
                print(f'({key[0]}){key[1:]}')
            print('\nChoose(blank to return): ', end='')
            choice = valid_choice(*[item[0] for item in subMenus.keys()], '')
        else:
            choice = preChoice
        if choice != '':
            for key in subMenus.keys():
                if key[0] == choice:
                    return subMenus[key]()
                
    global activeList
    subMenus = {'save list'     : menu_save_list,
               'edit entry'     : menu_edit,
               'delete entry'   : delete_helper,
               'run check'      : menu_check,
               'config'         : menu_config,
               'manage lists'   : menu_file_master,
               }
    while True:
        prep_menu()
        print(activeList)
        activeList.print_list(printSum=True)
        print('Status:', status)
        if not activeList.riceBought:
            print(f'{30*" "}!Reis nicht vergessen!')
        else:
            print()
        choice = input()
        # Call submenus
        if choice == '' or choice in [item[0] for item in subMenus.keys()] \
                or choice in ['<', '>']:
            #(13)This should not be a special case
            if choice == '<' or choice == '>':
                menu_file_master(preChoice=choice)
            else:
                menu_select(choice)
        # Add entry to active list
        elif choice.split(maxsplit=1)[0].translate(
                str.maketrans('', '', '-.p')).isnumeric():
            activeList.add(choice)
        # Rice toggle
        elif choice == 'rice':
            activeList.riceBought = not activeList.riceBought
        # Default case
        else:
            status = 'Invalid input:' + choice
        if settings['autoSave']:
            activeList.save()
            status = f'Saved({datetime.datetime.now().strftime("%H:%M")})'
        
def delete_helper():
    #(14) This is everything but elegant, had to do this workaround because
    # putting activeList.delete_entry as dictionary value refs to activeList
    #  at assignment and doesn't dynamically update.
    activeList.delete_entry()

            
def menu_config(status='ok'):
    while True:
        prep_menu()
        print('[Settings]')
        for item in settings.items():
            print(f' {item[0]} = {item[1]}')
        print('[Recurring]')
        for item in recurring.items():
            print(f' {item[0]} = {item[1]}')
        print('Status:', status)
        # (3) This doesn't catch bad inputs
        choice = input('Enter "key=value", "sheetpath" for selector, ' 
                       + 'or blank to return:\n')
        if choice == 'sheetpath' or choice == 'sheetPath':
            BankTx.sheetPathSelector()
            if settings['verboseLvl'] >= 1:
                status = 'sheetPath set'
        elif '=' in choice:
            key, value = choice.split('=')
            key, value = key.strip(), value.strip()
            value = fix_type(value)
            # (4) This is not a nice way to match choice to option
            if key in settings.keys():
                settings[key] = value
            if key in recurring.keys():
                recurring[key] = value
            if settings['verboseLvl'] >= 2:
                status = f'{key} set to {value}'
            elif settings['verboseLvl'] >= 1:
                status = f'{key} set'
        elif choice == '':
            break
    # Save config(or not)
    if settings['keepSettings']:
        save_config(settings=settings, recurring=recurring)
        if settings['verboseLvl'] >= 2:
            input('Saved cfg to file_')


def menu_check():
    prep_menu()
    txSheetFile = BankTx.sheet_picker(settings['sheetPath'])
    txSheetList = BankTx.sheet_processor(txSheetFile, activeList)
    check_Entries_vs_BankTx(activeList.entriesList, txSheetList)
    
    
def menu_edit():
    """Menu for editing entries in activeList"""
    while True:
        prep_menu()
        activeList.print_list(printIndex=True)
        print('Edit which one?(blank to return): ', end='')
        choice = valid_choice(*range(len(activeList.entriesList)), '')
        if choice == '':
            break
        else:
            activeList.entriesList[int(choice)].edit()
        

def menu_save_list():
    prep_menu()
    if os.path.exists(activeList.filePath):
        snippedPath = f'{activeList.filePath.split("/")[-1]}'
        print(f'\"{snippedPath}\" already exists, overwrite?(y/n): ',
              end='')
        choice = valid_choice('y', 'n', '')
        if choice == 'y' or choice == '':
            activeList.save()
        else:
            input('Aborted._')
            return
    else:
        activeList.save()
    input('Save successful._')


def menu_file_master(autoLoad=False, preChoice=''):
    """Does everything relating to the list files(except save)"""
    global activeList
    
    def find_files():
        """Returns sorted list of filenames"""
        fileList = []
        # Find
        with os.scandir(PATH) as current:
            for item in current:
                if 'entriesList' in item.name:
                    fileList.append([item.name, item.name[-14:-4].\
                                    replace('.', '')])
                elif 'bilanzListe' in item.name:
                    input('Old format bilanzListen deprecated, skipping')
        # Sort
        fileList = sorted(fileList, key=lambda item: item[1])
        fileList = [item[0] for item in fileList]
        return fileList.copy()
    
    def new_list():
        suggestions = []
        now = datetime.datetime.now().strftime('%Y-%m')
        # Suggestions:
        ## this month 
        suggestions.append(now)
        ## next month
        suggestions.append(increment_month(now))
        ## month after highest in files
        if fileList:
            suggestions.append(increment_month(fileList[-1][-11:-4]))
        ## month after highest in loaded lists
        if MonthList.dictOfLists:
            suggestions.append(increment_month(max(
                MonthList.dictOfLists.keys())))
        # Get rid of dupes, sort (Sort second because sets are unsorted)
        suggestions = sorted(list(set(suggestions)))
        # Get rid of those that already have a list
        for item in fileList:
            if item[-11:-4] in suggestions:
                suggestions.remove(item[-11:-4])
        for item in MonthList.dictOfLists.keys():
            if item in suggestions:
                suggestions.remove(item)
        print(f'\n{15*"*"}\nCreating new list...')
        print('Suggested new list dates: ')
        for index, item in enumerate(suggestions):
            dummy = f'({index})'
            print(f'{dummy:2}{item}')
        # (10) Does not check validity, does not check for duplicates!
        choice = input('\nPick from suggested, enter datestring(YYYY-MM) or '+\
                       'blank to return: ')
        if choice == '':
            pass
        elif choice.isnumeric() and int(choice) in range(len(suggestions)):
            choice = suggestions[int(choice)]
        return MonthList(listDate=choice)
    
    def autoLoader():
        # Figure out what month is most pertinent
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        if int(today[-2:]) >= 30:
            turnOfMonth = True
        else:
            turnOfMonth = False
        if turnOfMonth:
            currentMonth = increment_month(today[:-3])
        else:
            currentMonth = today[:-3]
        for file in fileList:
            if currentMonth in file:
                return MonthList(filePath=PATH + '/' + file)
        # No matching file found
        else:
            return MonthList(listDate=currentMonth)
    
    fileList = find_files()
    # Autoload list for current month
    if autoLoad:
        activeList = autoLoader()
        
    # Actual menu part
    else:
        while True:
            # Pop already loaded lists
            fileList = [item for item in fileList if item[-11:-4] not in
                        MonthList.dictOfLists.keys()]
            prep_menu()
            # Print files
            print('Not yet loaded list files:')
            if fileList:
                for index, file in enumerate(fileList):
                    dummy = f'({index})'
                    print(f'{dummy:>4}{file}')
            else:
                print(' None!')
            print()
            # Print loaded lists
            print('Loaded lists:')
            # (11) Prints unsorted!
            if MonthList.dictOfLists:
                for index, entry in enumerate(MonthList.dictOfLists.values()):
                    dummy = f'({index})'
                    if entry == activeList:
                        print(f'{dummy:>4}{entry} <-active')
                    else:
                        print(f'{dummy:>4}{entry}')
            else:
                print(' None!')
            print()
            if not activeList:
                print('No active list selected!')
            print()
            # User input(or not)
            if preChoice == '':
                choice = input(
                        'Enter\n(number) to load list from files,\n'+\
                        '(a) for all,\n'+\
                        '(>number) to select active list from loaded,\n'+\
                        '(n) to create new list,\n'+\
                        '(</>) for quickswitch next/previous month, or'+\
                        '\n(blank) to continue: ')
            else:
                choice = preChoice
                preChoice = ''
            #(12) Would this look more concise as a match-case?
            # Load all
            if choice == 'a':
                for item in fileList:
                    MonthList(filePath=PATH + '/' + item)
            # Quickswitch
            elif choice == '<' or choice == '>':
                if choice == '<':
                    targetMonth = decrement_month(activeList.listDate)
                else:
                    targetMonth = increment_month(activeList.listDate)
                # Check in loaded lists
                if targetMonth in MonthList.dictOfLists:
                    activeList = MonthList.dictOfLists[targetMonth]
                # Else check list files
                elif f'entriesList{targetMonth}.pkl' in fileList:
                    activeList = MonthList(filePath=PATH + '/' + 
                                           f'entriesList{targetMonth}.pkl')
                # Doesn't exist? Make new
                else:
                    activeList = MonthList(listDate=targetMonth)
                break
            # Choose active
            elif choice.startswith('>') and int(choice[1:]) in\
                    range(len(MonthList.dictOfLists.values())):
                choice = int(choice[1:])
                activeList = list(MonthList.dictOfLists.values())[choice]
            # Load selection
            elif choice.isnumeric() and int(choice) in range(len(fileList)):
                MonthList(filePath=PATH + '/' + fileList[int(choice)])
            # Make new list
            elif choice == 'n':
                activeList = new_list()
            # Continue
            elif choice == '':
                if activeList == None:
                    input('Must select an active list!...')
                else:
                    break
            # Default case
            else:
                input(f'Invalid input: "{choice}"...')
    

#%%###########fncts################


#%% Classes
###################################
class MonthList():
    """Lists of Entries, separate lists per month, separate files per list"""
    dictOfLists = {}
    
    def __init__(self, listDate=None, filePath=None):
        """listDate only needed for new lists, filePath for ones being loaded
        """
        self.listDate = listDate    # Format: 1970-01
        self.filePath = filePath
        self.entriesList = []
        self.riceBought = False
        if listDate is None and filePath is None:
            raise Exception('must supply either listDate or filePath')
        elif listDate is not None and filePath is not None:
            raise Exception('supply *either* listDate *or* filePath')
        # Create new list
        elif listDate is not None and filePath is None:
            self.entriesList = self.prep_new_list(listDate)
            self.filePath = PATH + '/' + 'entriesList' + listDate + '.pkl'
            if settings['verboseLvl'] >= 2:
                print('New list created.')
        # Load saved list
        elif listDate is None and filePath is not None:
            self.load()
            self.listDate = self.filePath[-11:-4]
        # Add this list to class dictionary
        check = MonthList.dictOfLists.setdefault(self.listDate, self)
        if check != self:
            # (2) Probably should handle this case in some way
            print(f'There is already a list for {self.listDate}!', 
                  f'Did not overwrite.')
        elif settings['verboseLvl'] >= 1:
            print(f'Successfully initialized list for {self.listDate}')
        if settings['debug']:
            input('continue...')
        
    def __str__(self):
        month = months[self.listDate[-2:]]
        return f'List for {self.listDate} ({month}), {len(self.entriesList)}' +\
                f' Entries'
    
    def print_list(self, printIndex=False, printSum=False):
        sumOfAmounts = 0
        widthTitle = 20
        lastInRecurring = list(recurring.keys())[-1]
        # Old way of output, includes associatedTx
        if settings['debug']:
            for entry in self.entriesList:
                print(entry)
                sumOfAmounts += entry.amount
            if printSum:
                print(f'  {sumOfAmounts}')
        # New way of output
        else:
            for index, entry in enumerate(self.entriesList):
                if entry.amount < 0:
                    sign = 'minus'
                else:
                    sign = 'plus'
                sumOfAmounts += entry.amount
                strippedAmount = entry.amount
                if strippedAmount < 0:
                    strippedAmount *= -1
                # Start constructing the line
                ## Takes tuple: value, width, alignment
                line = []
                if printIndex:
                    line.append((f'({index})', 4, '>'))
                line.append((sign, 5, '<'))
                line.append((f'{strippedAmount:.2f}', 7, '>'))
                line.append((entry.title, widthTitle, '<'))
                if printSum:
                    line.append(('=' + f'{sumOfAmounts:>8.2f}', 8, '>'))
                line.append((entry.status, 1, '^'))
                line.append((entry.date.strftime("%d.%m."), 6, '>'))
                # Print line
                for item in line:
                    print(f'{item[0]:{item[2]}{item[1]}}{3 * " "}', end='')
                print()
                # split
                if entry.title == 'Buergergeld':
                    print()
                else:
                    try:
                        if entry.title in recurring.keys() and\
                                self.entriesList[index + 1].title not in\
                                recurring.keys():
                            print()
                    except:
                        print()
                    
                
    @staticmethod
    def prep_new_list(month):
        """Creates new list, adds all recurring ins and outs,
        month as 'yyyy-mm'
        """
        newList = []
        placeholderDate = datetime.datetime.strptime(month, '%Y-%m').date()
        for item in recurring.items():
            newList.append(Entries(amount=item[1], title=item[0],
                                   date=placeholderDate))
        return copy.deepcopy(newList)
    
    @classmethod
    def Entry_to_Entries_migrator(cls, oldList):
        """!Deprecated!! Would need to figure out month of old list to pass to
        prep_new_list to get this working
        For legacy list migration
        """
        input('!!Importing of old "entry" lists deprecated!!')
        # newList = cls.prep_new_list()
        # for oldEntry in oldList:
        #     newList.append(Entries(oldEntry.amount, date=oldEntry.date))
        # return copy.deepcopy(newList)
    
    def load(self):
        
        def legacy_load():
            """To fix old filename schema or use of old classes"""
            # Correct from old format
            if type(self.entriesList[0]) == Entry:
                self.entriesList = self.Entry_to_Entries_migrator(
                    self.entriesList)
                if settings['verboseLvl'] >= 1:
                    print('Old list format detected, migrated to new.')
                self.save()
                
            if self.filePath.endswith('bilanzListe.pkl'):
                # Figure out month
                for item in self.entriesList:
                    if item.title == 'Buergergeld':
                        year, month = str(item.date)[:7].split('-')
                        break
                # Increment month since Buergergeld arrives the month before
                if month == '12':
                    month = '01'
                    year = int(year) + 1
                else:
                    month = int(month) + 1
                    if month < 10:
                        month = '0' + str(month)
                date = str(year) + '-' + str(month)
                # Show head and tail of list
                print(f'{self.entriesList[0]}\n{self.entriesList[1]}\n.\n.',
                      f'\n{self.entriesList[-2]}\n{self.entriesList[-1]}',
                      f'\nseems to pertain to {date}.')
                print('Press enter to confirm, enter new date(YYYY-MM)',
                      ', or d to display entire list: ', sep= '', end='')
                choice = input()
                if choice == 'd':
                    for i in self.entriesList:
                        print(i)
                    choice = input('Press enter to confirm' +\
                                   ' or enter new date(YYYY-MM): ')
                #(1) Not bothering to write a check for date formatting rn
                if choice != '':
                    date = choice
                updatedFilePath = PATH + '/entriesList' + date + '.pkl'
                os.rename(self.filePath, updatedFilePath)
                self.filePath = updatedFilePath
                if settings['verboseLvl'] >= 1:
                    print(f'New file path: {self.filePath}')
            
        with open(self.filePath, "rb") as file:
            self.entriesList = pickle.load(file)
        if self.filePath.endswith('bilanzListe.pkl') or type(
                self.entriesList[0]) == Entry:
            legacy_load()
        if settings['verboseLvl'] >= 1:
            print('loaded.')
        if settings['debug']:
            input('continue...')
            
    def save(self):
        with open(self.filePath, 'wb') as file:
            pickle.dump(self.entriesList, file)
            if settings['verboseLvl'] >= 2:
                if settings['debug']:
                    print(f'Saved at {self.filePath}')
                else:
                    snippedPath = f'/{self.filePath.split("/")[-2]}/'+\
                        f'{self.filePath.split("/")[-1]}'
                    print(f'Saved at {snippedPath}')
            elif settings['verboseLvl'] >= 1:
                print('Saved.')
            if settings['debug']:
                input('continue...')
                
    def delete_entry(self, preChoice=None):
        if preChoice is None:
            while True:
                prep_menu()
                self.print_list(printIndex=True)
                # for item in self.entriesList:
                #     print(f'({self.entriesList.index(item)}){item}')
                # (5) Doesn't catch bad inputs
                choice = input('\nDelete which one?(blank to return): ')
                if choice != '':
                    self.entriesList.pop(int(choice))
                else:
                    break
        else:
            self.entriesList.pop(int(preChoice))
        if settings['autoSave']:
            self.save()
    
    def add(self, newEntry):
        newEntry = newEntry.split(maxsplit=1)
        # Has custom title
        if len(newEntry) > 1:
            newTitle = newEntry[1]
        else:
            newTitle = False
        # Has placeholder tag
        if 'p' in newEntry[0]:
            newStatus = 'p'
        else:
            newStatus = False
        newAmount =  float(newEntry[0].replace('p', ''))
        self.entriesList.append(Entries(newAmount))
        if newTitle:
            self.entriesList[-1].title = newTitle
        if newStatus:
            self.entriesList[-1].status = newStatus


class Entries():
    """Entries made by user"""
    defaultTitle = '---'
    
    def __init__(self, amount, title=defaultTitle, date=datetime.date.today(),
                 status='u', associatedTx=None):
        self.amount = amount
        self.title = title
        self.date = date
        self.status = status    # (u)nconfirmed / (c)hecked / (p)laceholder
        self.associatedTx = associatedTx   
        
    def __str__(self):
        spacing = 20
        info =  f'{self.date.strftime("%d.%m.") :<{spacing}}' +\
                f'{self.title :<{spacing}}' +\
                f'{self.amount :<{spacing}.2f}' +\
                f'{self.status :<{spacing}}'
        if settings['debug']:
            info += f'{str(self.associatedTx) :<{spacing}}'
        return info
    
    def ingest(self, tx):
        self.amount = tx.betrag
        self.date = datetime.datetime.strptime(tx.buchungstag, '%d.%m.%Y')
        self.status = 'c'   
        self.associatedTx = copy.deepcopy(tx)
        if self.title == Entries.defaultTitle:
            if tx.name:
                self.title = tx.name.split()[0]
            else:
                self.title = tx.text
        if settings['verboseLvl'] >= 2:
            print(f'Successfully ingested: \n{3 * " "}{self}')
            
    def edit(self):
        # (7) Incredibly sloppily done
        """Edit an Entry's attributes"""
        attributes = vars(self)
        prep_menu()
        while True:
            for item in attributes.items():
                print(f'{item[0]} : {item[1]}({type(item[1])})')
            choice = input('Enter edit as statement(key = value, ' +\
                           'no quotes around strings), blank to return:\n')
            if choice == '':
                break
            else:
                choice = choice.split('=')
                choice[0], choice[1] = choice[0].strip(), choice[1].strip()
                choice[1] = fix_type(choice[1])
                attributes[choice[0]] = choice[1]
                print()


class Entry():
    """ !! Extremely deprecated, only used for conversion"""
    
    def __init__(self, amount, date=datetime.date.today(), status='u'):
        self.amount = amount
        self.date = date
        self.status = status    # (u)nconfirmed / (c)hecked / (p)laceholder
        self.associatedBuchung = None
        
        
class BankTx():
    """Actual bank transactions imported from real life"""
    listOf = []
    
    def __init__(self, buchungstag, valutadatum, name_zahlungsbeteiligter,
                 buchungstext, verwendungszweck, betrag):
       self.buchungstag = buchungstag
       self.valuta = valutadatum
       self.name = name_zahlungsbeteiligter
       self.text = buchungstext
       self.verwendungszweck = verwendungszweck
       self.betrag = betrag
       
    def __str__(self):
        divider = 30 * '-'
        info =  f'{divider} \n' +\
                f'Buchungsdatum: {self.buchungstag} // ' +\
                f'Valutadatum: {self.valuta} \n' +\
                f'Zahlungsbeteiligter: {self.name} \n' +\
                f'Buchungstext: {self.text} \n' +\
                f'Verwendungszweck: {self.verwendungszweck} \n' +\
                '\n' +\
                f'Betrag: {self.betrag:.2f} \n' +\
                f'{divider}'
        return info
    
    @staticmethod
    def sheetPathSelector():
        path = PATH
        while True:
            prep_menu()
            dirs = []
            sheets = []
            with os.scandir(path) as current:
                for item in current:
                    if item.is_dir():
                        dirs.append(item)
                    if item.name.startswith('Umsaetze'):
                        sheets.append(item)
            print(f'\nCurrent path: {path}\n')
            print('(..)')
            for item in dirs:
                print(f'({dirs.index(item)}){item.path}')
            print()
            for item in sheets:
                print(f'>{item.name}')
            print('Path(blank to choose this dir): ', end='')
            choice = valid_choice('..', '', *range(len(dirs)))
            if choice == '':
                break
            elif choice == '..':
                snip = path.rfind('/')
                path = path[:snip]
            else:
                path = dirs[int(choice)].path
        settings['sheetPath'] = path
        print(f'Selected: {path}')
        
    
    @staticmethod
    def sheet_picker(PATH):
        """Returns name of correct csv file, gets rid of others"""
        # Finds relevant files
        direc = os.scandir(PATH)
        found = []
        for item in direc:
            if item.name.startswith('Umsaetze'):
                # Full name, date via part of name
                found.append([item.name, item.name[-14:-4].replace('.', '')])
        # Sort and turn one-dimensional(by dropping dates)
        found = sorted(found, key=lambda item: item[1])
        found = [item[0] for item in found]
        # Picks the correct file
        if len(found) > 1:
            print('Found multiple files:')
            for item in found:
                print(f'({found.index(item)}){item}')
            choice = input(f'\nUse which one?(Deletes others, ' +\
                           f'default: last in list): ')
            if choice != '':
                sheet = found[int(choice)]
            else:
                sheet = found[-1]
            for item in found:
                if item != sheet:
                    os.remove(PATH + '/' + item)    
        else:
            sheet = found[0]
        if settings['verboseLvl'] >= 2:
            print(f'Selected "{sheet}"')
        return sheet
    
    @staticmethod
    def sheet_processor(sheet, activeList):
        """Turn csv file with transactions into list of BankTx objects
        !Expects the csv to be from most recent to oldest, returns reversed!
        Need Entries.listOf to be loaded in order to know the month to grab
        """
        
        def make_BankTx_object(txDict):
            """Turns a row from the sheet(in dictionary form) into
            a BankTx object
            """
            txObj = BankTx(txDict['Buchungstag'], txDict['Valutadatum'],
                           txDict['Name Zahlungsbeteiligter'],
                           txDict['Buchungstext'], txDict['Verwendungszweck'],
                           float(txDict['Betrag'].replace(',', '.')))
            return txObj
            
        with open(settings['sheetPath'] + '/' + sheet) as file:
            reader = csv.DictReader(file, delimiter=';')
            txList = []
            listMonth = activeList.listDate.replace('-', '')
            if settings['debug']:
                input(f'I believe the month of the list is {listMonth}_')
            for item in reader:
                thisTx = make_BankTx_object(item)
                thisTxMonth = f'{thisTx.valuta[-4:]}{thisTx.valuta[-7:-5]}'
                if settings['debug']:
                    print(thisTx)
                if thisTxMonth > listMonth:
                    if settings['verboseLvl'] >= 2:
                        print('Tx month higher than list, skipped.')
                elif thisTxMonth == listMonth:
                    txList.append(thisTx)
                    if settings['verboseLvl'] >= 2:
                        print(f'Valuta:{item["Valutadatum"][3:5]}, Monat:' +\
                              f'{listMonth} -- Match appended.')
                        if settings['debug']:
                            input('continue...')
                # If TxMonth < listMonth
                else:
                    # Continue until Buergergeld for current month 
                    ## (which arrived last month), to demarcate turn of month
                    txList.append(thisTx)
                    if settings['verboseLvl'] >= 2:
                        print('Appended while looking for Buergergeld.')
                        if settings['debug']:
                            input('continue...')
                    if item['Name Zahlungsbeteiligter'].\
                            startswith('Bundesagentur fuer Arbeit'):
                        if settings['verboseLvl'] >= 2:
                            print('Buergergeld found, breaking.')
                            if settings['debug']:
                                input('continue...')
                        break
        if settings['verboseLvl'] >= 1:
                print(len(txList), 'transactions loaded.')
        txList.reverse()
        return txList.copy()
                    
    def comparer(self, other):
        if self.buchungstag == other.buchungstag and \
                self.valuta == other.valuta and \
                self.name == other.name and \
                self.text == other.text and \
                self.verwendungszweck == other.verwendungszweck and \
                self.betrag == other.betrag:
            return True
        else:
            return False
        
        
    
#%%###########classes##############


#%% Objects
###################################

#%%###########objcts###############




#%% Main Program
###################################

load_config()
for instruction in sys.argv[1:]:
    exec(instruction)
activeList = None
menu_file_master(autoLoad=settings['autoLoad'])
menu_main()




#%%##########main##################



















































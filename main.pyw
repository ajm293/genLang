import random as ran
from copy import deepcopy
from tkinter import *
from tkinter import scrolledtext
from tkinter import filedialog
import csv
import pickle
import os
import ctypes

class Generators(object): # Holds the fundamental language generation functions
    def __init__(self):
        self.consonants = ['m','p','f','b','t','d','n','s',
                           'r','k','x','g','θ','l','ɲ','ʃ',
                           'h','j','w','ʒ']
        self.vowels = ['i','u','e','o','a','ə','æ']
        self.fluids = ['r','l','n','m','w']
        self.orthConsonants = {
            'm' : 'm',
            'p' : 'p',
            'f' : 'f',
            'b' : 'b',
            't' : 't',
            'd' : 'd',
            'n' : 'n',
            's' : 's',
            'r' : 'r',
            'k' : 'k',
            'x' : 'x',
            'g' : 'g',
            'θ' : 'th',
            'l' : 'l',
            'ɲ' : 'ng',
            'ʃ' : 'sh',
            'h' : 'h',
            'j' : 'y',
            'w' : 'w',
            'ʒ' : 'zh'}
        self.orthVowels = {
            'i' : 'i',
            'u' : 'ü',
            'e' : 'e',
            'o' : 'o',
            'a' : 'a',
            'ə' : 'u',
            'æ' : 'ä'}


    def phonology(self, cOffset=0, vOffset=0):
        ran.shuffle(self.consonants) # Ensure lists are random
        ran.shuffle(self.vowels)
        # Slice into lists, to make the random selection
        selectionConsonants = self.consonants[:ran.randint(6,len(self.consonants)-cOffset)]
        selectionVowels = self.vowels[:ran.randint(3,len(self.vowels)-vOffset)]
        selectionFluids = []
        for fluid in self.fluids:
            if fluid in selectionConsonants:
                selectionConsonants.remove(fluid) # Remove fluids
                selectionFluids.append(fluid) # Move fluids to present fluids list
        return [selectionConsonants,selectionVowels,selectionFluids] # Return selection as a list of three lists

    
    def orthography(self, arrayPhonology):
        arrayOrthography = deepcopy(arrayPhonology) # Makes the two arrays the same size
        for index,consonant in enumerate(arrayPhonology[0]): # Process consonants
            arrayOrthography[0][index] = self.orthConsonants[consonant] # Replace IPA with orthographical char
        for index,vowel in enumerate(arrayPhonology[1]): # Process vowels
            arrayOrthography[1][index] = self.orthVowels[vowel] # Replace IPA with orthographical char
        if arrayPhonology[2] != []:
            for index,fluid in enumerate(arrayPhonology[2]): # Process fluids
                arrayOrthography[2][index] = self.orthConsonants[fluid] # Replace IPA with orthographical char
        return arrayOrthography


    def sentenceOrder(self):
        systems = ['SOV','SVO','VSO','VOS','OVS','OSV','NONE'] # define systems
        distribution = [410,354,69,18,8,3,138] # 1-to-1 weighted distribution
        return ran.choices(systems,weights=distribution)[0] # choose and return direct


    def syllableStructure(self, arrayPhonology, dropoff=100):
        # Dropoff is used to guide how large a phonology is. Higher dropoff equals more structures
        print(dropoff)
        enoughGenerated = False
        forms = [] # Holds syllable structures generated
        while enoughGenerated == False:
            if arrayPhonology[2] != []:
                form = self.syllableFluidsPresent()
            else:
                form = self.syllableNoFluids()
            if (form in forms) or (form in ['VVV','VV']) or ('VV' in form) or ('CR' in form):
                pass # Exclude generations already in list, and problematic forms
            else:
                forms.append(form) # Add checked form to list
            if (len(forms) > 1) and (ran.randint(0,dropoff) == 0):
                enoughGenerated = True # Leave generation at random after 3 forms are verified
                break
        return forms


    def syllableFluidsPresent(self): # Create a structure for a phonology with fluids
        form = ''
        palette = ['C','V','R']
        weighting = [0.3,0.4,0.3]
        for i in range(ran.randint(2,3)): # Produces forms of length 2 or 3
            form += ran.choices(palette,weights=weighting)[0]
            if form[i] == 'C':
                weighting = [0.0,0.6,0.4] # Ensure consonants cannot group
            elif form[i] == 'V':
                weighting = [0.5,0.2,0.3] # Vowels are permissive, consonants are prioritised
            elif form[i] == 'R':
                weighting = [0.0,1.0,0.0] # Fluids followed by vowels
        return form
            

    def syllableNoFluids(self): # Create a structure for a phonology without fluids
        form = ''
        weighting = [0.5,0.5]
        for i in range(ran.randint(2,3)): # Produces forms of length 2 or 3
            form += ran.choices(['C','V'],weights=weighting)[0]
            if form[i] == 'C':
                weighting = [0.0,1.0] # Avoid consonant grouping
            elif form[i] == 'V':
                weighting = [0.8,0.2] # Prioritise consonants
        return form


class Features(object): # Holds the language feature consolidation
    def __init__(self, phonology, wordOrder, syllableForms):
        self.phonology = phonology
        self.wordOrder = wordOrder
        self.syllableForms = syllableForms
        self.verbSystem = []
        self.declensionSystem = []
        self.pluralSystem = []
        self.articleSystem = []
        self.morphRules = []
        

    def verbs(self):
        vb = Verb(self.phonology, self.syllableForms)
        self.verbSystems = [vb.particle, # Establish available systems
                       vb.agglutinative,
                       vb.auxiliary]
        self.verbSystem = ran.choice(self.verbSystems)()
        return self.verbSystem
        

    def nouns(self):
        noun = Noun(self.phonology, self.syllableForms, self.wordOrder) # Initialise
        self.pluralSystem = noun.plurals() # Get plural
        self.articleSystem = noun.articles() # Get article
        self.declensionSystem = noun.declension() # Get declension
        return [self.pluralSystem, self.articleSystem, self.declensionSystem]


    def morphology(self):
        morph = Morphology(self.phonology, self.syllableForms)
        self.morphRules = morph.createRules()
        return self.morphRules


class Morphology(object):
    def __init__(self, phonology, syllableForms):
        self.phonology = phonology
        self.syllableForms = syllableForms
        self.rules = ['Adjective > Adverb',
                      'Diminutive',
                      'Augmentative',
                      'Agent noun (Doer)',
                      'Possessive']


    def stringGenerator(self, length, forms): # Used to generate the affixes
        output = ''
        for x in range(length):
            for letter in ran.choice(forms):
                if letter == 'C':
                    output += ran.choice(self.phonology[0])
                elif letter == 'V':
                    output += ran.choice(self.phonology[1])
                elif letter == 'R':
                    output += ran.choice(self.phonology[2])
        return output


    def createRules(self):
        affixes = [] # Declare empty affix list
        for rule in self.rules:
            affix = '-' + self.stringGenerator(1,self.syllableForms) # Generate affix
            while (affix in affixes) or ('ʔ' in affix): # If duplicate regenerate
                affix = '-' + self.stringGenerator(1,self.syllableForms)
            affixes.append(affix)
        return [self.rules, affixes]


class Noun(object): # Holds the noun methods
    def __init__(self, phonology, syllableForms, wordOrder):
        self.phonology = phonology
        self.syllableForms = syllableForms
        self.wordOrder = wordOrder
        self.cases = ['Nominative','Accusative','Dative','Genitive','Locative']


    def stringGenerator(self, length, forms): # Used to generate the affixes
        output = ''
        for x in range(length):
            for letter in ran.choice(forms):
                if letter == 'C':
                    output += ran.choice(self.phonology[0])
                elif letter == 'V':
                    output += ran.choice(self.phonology[1])
                elif letter == 'R':
                    output += ran.choice(self.phonology[2])
        return output
    

    def declension(self): # Chooses declension and generates
        weights = [0.2,0.8] # Weights for declension choice
        choose = [True,False]
        if self.wordOrder == 'NONE':
            weights = [0.8,0.2] # Adjust for NONE order languages
        isDeclension = ran.choices(choose, weights)[0] # Choose
        if isDeclension: # Generate declensions
            caseExtensions = []
            for case in self.cases:
                inflect = self.stringGenerator(1,self.syllableForms)
                caseExtensions.append('-'+inflect)
            return [isDeclension, [self.cases, caseExtensions]] # Return declensions
        else:
            return [isDeclension] # Return false choice
        

    def plurals(self): # Chooses plural system and generates
        pluralType = ran.choice(['prefix','suffix']) # Choose type
        if pluralType == 'prefix': # Generate prefix
            pluralAffix = self.stringGenerator(1, self.syllableForms) + '-'
        else: # Generate suffix
            pluralAffix = '-' + self.stringGenerator(1, self.syllableForms)
        return [pluralType, pluralAffix]


    def articles(self): # Chooses article and generates
        weights = [0.8,0.2]
        choose = [True,False]
        isArticles = ran.choices(choose, weights)[0] # Decide article
        if isArticles: # Generate the articles if true
            definiteArticle = self.stringGenerator(ran.randint(1,2),self.syllableForms)
            indefiniteArticle = self.stringGenerator(ran.randint(1,2),self.syllableForms)
            return [isArticles, [definiteArticle,indefiniteArticle]] # Return articles
        else:
            return [isArticles] # Return false choice



class Verb(object): # Holds the various verb system methods
    def __init__(self, phonology, syllableForms):
        self.phonology = phonology
        self.syllableForms = syllableForms
        self.baseTenses = ['Present','Past', # Establish base tenses
                       'Future','Remote Future',
                       'Remote Past','Cond. Future']
        self.aspects = ['Simple','Perfect','Progressive','Perf. Progressive'] # Establish available aspects

        self.inventory = [] # Establish tense-aspect inventory array
        self.inventory.append('Present Simple') # Ensure every language has a complete tense set
        self.inventory.append('Past Simple')
        self.inventory.append('Future Simple')
        


    def stringGenerator(self, length, forms): # Used to generate the additions
        output = ''
        for x in range(length):
            for letter in ran.choice(forms):
                if letter == 'C':
                    output += ran.choice(self.phonology[0])
                elif letter == 'V':
                    output += ran.choice(self.phonology[1])
                elif letter == 'R':
                    output += ran.choice(self.phonology[2])
        return output

        
    def particle(self):
        tenses = []
        aspects = []

        tenses.append('Present')
        tenses.append('Past')
        tenses.append('Future')
        aspects.append('Simple')
        
        enough = False # Loop for tenses
        while enough == False: # Loop until satisfactory
            tense = ran.choice(self.baseTenses) # Pick tense for inspection
            if tense not in tenses: # Ensure duplicate tenses are not created
                tenses.append(tense)
            else:
                pass # Skip if already present
            if len(tenses) > 1 and ran.randint(0,2) == 2: # Ensure tenses is of somewhat random length
                enough = True # The breaker
                break

        enough = False
        while enough == False:
            aspect = ran.choice(self.aspects)
            if aspect not in aspects:
                aspects.append(aspect)
            else:
                pass
            if len(aspects) > 0 and ran.randint(0,2) ==2:
                enough = True
                break
            
        tenseTable = []
        for tense in tenses: # Appending loop for tenses
            auxWord = self.stringGenerator(1, self.syllableForms)
            tenseTable.append([tense,auxWord])
        aspectTable = []
        for aspect in aspects: # Appending loop for aspects
            auxWord = self.stringGenerator(1, self.syllableForms)
            aspectTable.append([aspect,auxWord])
        return ['PARTICLE',tenseTable,aspectTable]

    
    def agglutinative(self):
        tenses = []
        aspects = []

        tenses.append('Present')
        tenses.append('Past')
        tenses.append('Future')
        aspects.append('Simple')
        
        enough = False # Loop for tenses
        while enough == False: # Loop until satisfactory
            tense = ran.choice(self.baseTenses) # Pick tense for inspection
            if tense not in tenses: # Ensure duplicate tenses are not created
                tenses.append(tense)
            else:
                pass # Skip if already present
            if len(tenses) > 1 and ran.randint(0,2) == 2: # Ensure tenses is of somewhat random length
                enough = True # The breaker
                break

        enough = False
        while enough == False:
            aspect = ran.choice(self.aspects)
            if aspect not in aspects:
                aspects.append(aspect)
            else:
                pass
            if len(aspects) > 0 and ran.randint(0,2) ==2:
                enough = True
                break
            
        tenseTable = []
        for tense in tenses: # Appending loop for tenses
            auxWord = self.stringGenerator(1, self.syllableForms)
            tenseTable.append([tense,auxWord])
        aspectTable = []
        for aspect in aspects: # Appending loop for aspects
            auxWord = self.stringGenerator(1, self.syllableForms)
            aspectTable.append([aspect,auxWord])
        return ['AGGLUTINATIVE',tenseTable,aspectTable] # Return agglutinative-particle standard

  
    def auxiliary(self):
        enough = False
        while enough == False: # Loop until satisfactory
            addition = ran.choice(self.baseTenses)+' '+ran.choice(self.aspects) # Generate tense-aspect for inspection
            if addition not in self.inventory: # Ensure duplicate tense-aspects are not created
                self.inventory.append(addition)
            else:
                pass # Skip if already present
            if len(self.inventory) > 3 and ran.randint(0,2) == 2: # Ensure inventory is of somewhat random length
                enough = True # The breaker
                break
        assignmentTable = []
        for tenseAspect in self.inventory:
            auxWord = self.stringGenerator(ran.randint(1,2), self.syllableForms)
            assignmentTable.append([tenseAspect,auxWord])
        return ['AUXILIARY',assignmentTable] # Return auxiliary standard


# Experimental paragraph generator
def paragraphGen(arrayOrthography, syllableForms):
    paragraph = ''
    for i in range(50):
        for x in range(ran.randint(1,3)):
            structure = ran.choice(syllableForms)
            output = ''
            for letter in structure:
                if letter == 'C':
                    output += ran.choice(arrayOrthography[0])
                elif letter == 'V':
                    output += ran.choice(arrayOrthography[1])
                elif letter == 'R':
                    output += ran.choice(arrayOrthography[2])
            paragraph += output
        paragraph += ' '
    return paragraph


def lexiconGen(syllableForms, phonology, orthography): # Create lexicon
    try:
        verb = open('verbs.txt','r').read().splitlines() # Read all prerequisites
        noun = open('nouns.txt','r').read().splitlines()
        adjective = open('adjectives.txt', 'r').read().splitlines()
        other = open('other.txt', 'r').read().splitlines()
    except FileNotFoundError: # Handle missing files
        return False

    verbTableOrth = [] # Define orthographical intermediate arrays
    nounTableOrth = []
    adjTableOrth = []
    otherTableOrth = []

    verbTablePhono = assignWords(verb, syllableForms, phonology, orthography, 2, 3) # Generate words
    nounTablePhono = assignWords(noun, syllableForms, phonology, orthography, 2, 3)
    adjTablePhono = assignWords(adjective, syllableForms, phonology, orthography, 2, 3)
    otherTablePhono = assignWords(other, syllableForms, phonology, orthography, 1, 2)

    for word in verbTablePhono: # Populate orth array with iterated conversion from phono
        verbTableOrth.append(convertPhono(word, phonology, orthography))
    for word in nounTablePhono:
        nounTableOrth.append(convertPhono(word, phonology, orthography))
    for word in adjTablePhono:
        adjTableOrth.append(convertPhono(word, phonology, orthography))
    for word in otherTablePhono:
        otherTableOrth.append(convertPhono(word, phonology, orthography))

    verbTable = [verb, verbTablePhono, verbTableOrth] # Assemble individual tables
    nounTable = [noun, nounTablePhono, nounTableOrth]
    adjTable = [adjective, adjTablePhono, adjTableOrth]
    otherTable = [other, otherTablePhono, otherTableOrth]

    return [verbTable, nounTable, adjTable, otherTable] # Return combined standard

def assignWords(inputArray, syllableForms, phonology, orthography, hi, lo): # Generate words for an array
    outputArray = []
    for word in inputArray:
        genWord = stringGenerator(ran.randint(hi, lo), syllableForms, phonology) # Gen partner word
        while genWord in outputArray: # Check for duplicates
            genWord = stringGenerator(ran.randint(hi, lo), syllableForms, phonology)
        outputArray.append(genWord) # Add when checked
    return outputArray


def stringGenerator(length, forms, phonology): # Common generator for any length string given forms and phono
        output = ''
        for x in range(length):
            for letter in ran.choice(forms): # Use CVR form to generate word
                if letter == 'C':
                    output += ran.choice(phonology[0])
                elif letter == 'V':
                    output += ran.choice(phonology[1])
                elif letter == 'R':
                    output += ran.choice(phonology[2])
        return output


def convertPhono(word, phonology, orthography): # Convert given IPA word to orthographical equivalent
        g = Generators()
        outWord = ''
        for i,y in enumerate(word):
            if y in g.vowels:
                outWord += g.orthVowels.get(y, y)
            else:
                outWord += g.orthConsonants.get(y, y)
        return outWord


def printLexiconTable(lexicon, table): # Present a given table in the lexicon
    for i,x in enumerate(lexicon[table][0]):
        print('{0:13}{1:13}{2:13}'.format(x, lexicon[table][1][i], lexicon[table][2][i]))


def savePickleFile(data, fileName): # Dump lexicon to a pickle file
    with open(fileName, 'wb') as f:
        pickle.dump(data, f)


def loadPickleFile(fileName): # Returns a pickle stream given a filename
    with open(fileName, 'rb') as f:
        return pickle.load(f)


# UI Functions

def Mbox(title, text, style): # Message box creator
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)

def showAboutWindow():
    about = Tk()
    about.title("About genLang")
    about.resizable(width=False, height=False)
    Label(about, text="Language and lexicon generator").grid(row=1, padx=10, sticky=W)
    im = PhotoImage(master=about, file="genlogo.gif")
    image = Label(about, image=im)
    image.grid(row=0, padx=10, pady=10)
    image.image = im

def showLexWindow(lexicon, dropoff, cOffset, vOffset): # Load and display the lex window
    global lexOut, lexWindow # Ensure global for co-op with searchLexicon
    
    lexWindow = Toplevel(master) # Establish window
    lexWindow.resizable(False, False)
    lexWindow.focus_force()

    menubar = Menu(lexWindow) # Establish menu and menu options
    filemenu = Menu(menubar, tearoff=0)
    filemenu.add_command(label="Exit", command=exit)
    filemenu.add_command(label="Regenerate", command=lambda:generateInstance(dropoff, cOffset, vOffset))
    filemenu.add_command(label="Regenerate lexicon", command=lambda:regenerateLexicon(dropoff, cOffset, vOffset))
    filemenu.add_command(label="Save language", command=lambda:saveInstance(menubar))
    filemenu.add_command(label="Load language", command=lambda:loadInstance(menubar))
    menubar.add_cascade(label="File", menu=filemenu)
    lexWindow.config(menu = menubar)
    
    lexOut = scrolledtext.ScrolledText(lexWindow, wrap=WORD, width=50, height=20) # Create lexicon output box
    lexOut.grid(row=4, column=0, padx=10, pady=10)

    infoFrame = Frame(lexWindow) # Create a frame for the language overview information
    infoFrame.grid(row=0, column=0, sticky=W+E)
    
    # Establish labels for language overview
    Label(infoFrame, text='Language Name: '+ searchLexicon(lexicon, word='language')).grid(row=0, column=0, padx=5, sticky=W)
    Label(infoFrame, text='Verb System Type: '+ verbSystem[0]).grid(row=1, column=0, padx=5, sticky=W)
    Label(infoFrame, text='Word Order: '+ wordOrder).grid(row=2, column=0, padx=5, sticky=W)
    Label(infoFrame, text='Articles? : '+ str(articleSystem[0])).grid(row=0, column=1, padx=5, sticky=E)
    if articleSystem[0]: # If there are articles in the language, render the appropriate labels
        Label(infoFrame, text='Definite: '+ articleSystem[1][0]+'/'+convertPhono(articleSystem[1][0],
                                                                                 phonology,
                                                                                 orthography)).grid(row=1, column=1, padx=5, sticky=E)
        Label(infoFrame, text='Indefinite: '+ articleSystem[1][1]+'/'+convertPhono(articleSystem[1][1],
                                                                                   phonology,
                                                                                   orthography)).grid(row=2, column=1, padx=5, sticky=E)
    Label(infoFrame, text='Plurality : '+ str(pluralSystem[1])+'/'+convertPhono(str(pluralSystem[1]),
                                                                                phonology,
                                                                                orthography)).grid(row=3, column=0, padx=5, sticky=W)

    Label(infoFrame, text='Declension? : '+str(declensionSystem[0])).grid(row=3, column=1, padx=5, sticky=E)
    if declensionSystem[0]: # If the language uses noun declension, render the declension button
        btnDec = Button(infoFrame, text='Declension', command=showDeclensionWindow)
        btnDec.grid(row=3, column=2, padx=5, sticky=W)
    
    entryFrame = Frame(lexWindow) # Create a frame for search entries
    entryFrame.grid(row=1,column=0,sticky=W+E)
    
    englishSearch = Entry(entryFrame, width=50) # Create an Entry element for english word searching
    Label(entryFrame, text="English:").grid(row=0,column=0, padx=10, pady=10)
    englishSearch.grid(row=0,column=1, padx=10, pady=10)
    # Create a button for starting the search
    btnSearch = Button(entryFrame, text='Search for word', command=lambda:searchLexicon(lexicon, word=englishSearch.get().lower()))
    btnSearch.grid(row=1, column=1, padx=5, pady=5, sticky=E)

    buttonFrame = Frame(lexWindow) # Create a frame to store the word type buttons
    buttonFrame.grid(row=2, column=0, padx=10, pady=10)

    Label(buttonFrame, text="Show:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
    
    btnVerb = Button(buttonFrame, text='Verbs', command=lambda:searchLexicon(lexicon, wordtype=0))
    btnVerb.grid(row=0, column=1, padx=5, pady=5) # Button for verb word type
    
    btnNoun = Button(buttonFrame, text='Nouns', command=lambda:searchLexicon(lexicon, wordtype=1))
    btnNoun.grid(row=0, column=2, padx=5, pady=5) # Button for noun word type
    
    btnAdj = Button(buttonFrame, text='Adjectives', command=lambda:searchLexicon(lexicon, wordtype=2))
    btnAdj.grid(row=0, column=3, padx=5, pady=5) # Button for adjective word type
    
    btnOther = Button(buttonFrame, text='Others', command=lambda:searchLexicon(lexicon, wordtype=3))
    btnOther.grid(row=0, column=4, padx=5, pady=5) # Button for other word type
    
    btnAll = Button(buttonFrame, text='All', command=lambda:searchLexicon(lexicon, wordtype=4))
    btnAll.grid(row=0, column=5, padx=5, pady=5) # Button for all words to be displayed

    Label(lexWindow, text='Results:').grid(row=3, column=0, sticky=W, padx=10)

    featureFrame = Frame(lexWindow) # Create frame for feature buttons
    featureFrame.grid(row=5, column=0, padx=5, pady=5, sticky=W+E)

    btnWordOrder = Button(featureFrame, text='Word Order', command=lambda:showOrderWindow())
    btnWordOrder.grid(row=0, column=0, padx=5, pady=5) # Button for word order window

    btnVerbSystem = Button(featureFrame, text='Verb System', command=lambda:showVerbWindow())
    btnVerbSystem.grid(row=0, column=1, padx=5, pady=5) # Button for verb system window

    btnMorphology = Button(featureFrame, text='Morphology', command=lambda:showMorphWindow())
    btnMorphology.grid(row=0, column=2, padx=5, pady=5) # Button for morphology window

    btnWordGen = Button(featureFrame, text='Word Generator', command=lambda:showWordGenWindow())
    btnWordGen.grid(row=0, column=3, padx=5, pady=5) # Button for word generator window


def showWordGenWindow():
    wordGenWindow = Toplevel(lexWindow) # Establish window
    wordGenWindow.resizable(False, False)
    wordGenWindow.focus_force()

    genFrame = Frame(wordGenWindow) # Create frame for output of generator
    genFrame.grid(row=0, column=0, padx=5, pady=5)

    genOut = scrolledtext.ScrolledText(genFrame, wrap=WORD, width=40, height=10)
    genOut.grid(row=0, column=0, padx=5, pady=5) # Create generator output box
    genOut.configure(state='disabled')

    controlFrame = Frame(wordGenWindow) # Create frame for generator controls
    controlFrame.grid(row=1, column=0, padx=5, pady=5, sticky=W+E)

    Label(controlFrame, text='Length:').grid(row=1, column=0, padx=5, pady=5, sticky=E)

    scaleLength = Scale(controlFrame, from_=1, to=5, orient=HORIZONTAL)
    scaleLength.grid(row=1, column=1, padx=5, pady=5, sticky=W) # Create slider for length of output

    btnGenWord = Button(controlFrame, text='Generate Word', command=lambda:genWord(genOut, scaleLength.get()))
    btnGenWord.grid(row=0, column=0, padx=5, pady=5) # Create generate button

def genWord(genOut, length): # Used alongside showWordGenWindow
    addition = stringGenerator(length, syllableForms, phonology) # Get word from stringGenerator
    addition = addition +'/'+convertPhono(addition, phonology, orthography)+'\n'
    genOut.configure(state='normal')
    genOut.insert(END, addition) # Add generated word to output box
    genOut.see(END) # Scroll to bottom
    genOut.configure(state='disabled')


def showMorphWindow():
    morphWindow = Toplevel(lexWindow)
    morphWindow.resizable(False,False)
    morphWindow.focus_force()

    morphOut = scrolledtext.ScrolledText(morphWindow, wrap=WORD, width=40, height=6)
    morphOut.grid(row=0, column=0, padx=10, pady=10)
    for i,morph in enumerate(morphSystem[0]):
        addition = '{:20}{:7}{}\n'.format(morph, morphSystem[1][i], convertPhono(morphSystem[1][i], phonology, orthography))
        morphOut.insert(END, addition)
    morphOut.configure(state='disabled')


def showDeclensionWindow():

    decWindow = Toplevel(lexWindow)
    decWindow.resizable(False, False)
    decWindow.focus_force()

    decOut = scrolledtext.ScrolledText(decWindow, wrap=WORD, width=30, height=5)
    decOut.grid(row=0, column=0, padx=10, pady=10)
    
    for i, case in enumerate(declensionSystem[1][0]):
        addition = '{:12}{:7}{}\n'.format(case, declensionSystem[1][1][i], convertPhono(declensionSystem[1][1][i], phonology, orthography))
        decOut.insert(END,addition)
    decOut.configure(state="disabled")


def showOrderWindow():

    orderWindow = Toplevel(lexWindow)
    orderWindow.resizable(False, False)
    orderWindow.focus_force()

    Label(orderWindow, text='This language uses the '+wordOrder+' word order.').grid(row=0, column=0, padx=10, pady=10)

    if wordOrder == 'SOV':
        Label(orderWindow, text='The sentence \'I kicked the ball\' would\nhave the order \'I the ball kicked\'').grid(row=1, column=0, padx=10, pady=10)
    elif wordOrder == 'SVO':
        Label(orderWindow, text='The sentence \'I kicked the ball\' would\nhave the order \'I kicked the ball\'').grid(row=1, column=0, padx=10, pady=10)
    elif wordOrder == 'VSO':
        Label(orderWindow, text='The sentence \'I kicked the ball\' would\nhave the order \'Kicked I the ball\'').grid(row=1, column=0, padx=10, pady=10)
    elif wordOrder == 'OVS':
        Label(orderWindow, text='The sentence \'I kicked the ball\' would\nhave the order \'The ball kicked I\'').grid(row=1, column=0, padx=10, pady=10)
    elif wordOrder == 'OSV':
        Label(orderWindow, text='The sentence \'I kicked the ball\' would\nhave the order \'The ball I kicked\'').grid(row=1, column=0, padx=10, pady=10)
    elif wordOrder == 'VOS':
        Label(orderWindow, text='The sentence \'I kicked the ball\' would\nhave the order \'Kicked the ball I\'').grid(row=1, column=0, padx=10, pady=10)
    elif wordOrder == 'NONE':
        Label(orderWindow, text='The sentence \'I kicked the ball\' would\nhave any order possible').grid(row=1, column=0, padx=10, pady=10)


def showVerbWindow():

    verbWindow = Toplevel(lexWindow) # Establish verb window
    verbWindow.resizable(False, False)
    verbWindow.focus_force()

    verbOut = scrolledtext.ScrolledText(verbWindow, wrap=WORD, width=100, height=15)
    verbOut.grid(row=4, column=0, padx=10, pady=10) # Create verb table output box
    
    if verbSystem[0] in ['PARTICLE','AGGLUTINATIVE']: # Needs a 2D table
        aspects = ['']
        tenses = ['']
        for aspect in verbSystem[2]: # Ensures the first row is formatted correctly
            aspects.append(aspect[0])
        addition = ''.join(['{:20}' for n in range(len(aspects))])
        verbOut.insert(END,addition.format(*aspects)+'\n')
        for tense in verbSystem[1]:
            suffixes = []
            for aspect in verbSystem[2]:
                if verbSystem[0] == 'AGGLUTINATIVE': # Do not add spaces for agglutinative systems
                    suffixes.append('-'+tense[1]+aspect[1]+'/'+convertPhono(tense[1]+aspect[1], phonology, orthography))
                else: # Add spaces for particle systems
                    suffixes.append(tense[1]+' '+aspect[1]+'/'+convertPhono(tense[1],phonology,
                                                                            orthography)+' '+convertPhono(aspect[1],
                                                                                                          phonology, orthography))
            verbOut.insert(END,addition.format(tense[0], *suffixes)+'\n')
    else: # For auxiliary systems, needs only 1D table
        for tenseaspect in verbSystem[1]:
            verbOut.insert(END, '{:30}{:10}'.format(*tenseaspect)+'\n')
    verbOut.configure(state='disabled') # Finish off
        

def searchLexicon(lexicon, word=None, wordtype=None): # Find a word, or words of a wordtype. Works with lexOut.
    if word != None:
        word = word.lower() # Lowercase forced
        for i,table in enumerate(lexicon):
            for j,x in enumerate(table[0]):
                if x.lower() == word: # If the word is found
                    lexOut.configure(state='normal')
                    lexOut.delete(1.0,END) # Clear box
                    addition = ('{0:<16}{1:<16}{2:<16}\n'.format(x,lexicon[i][1][j],lexicon[i][2][j])) # Format addition
                    lexOut.insert(END, '{0:<16}{1:<16}{2:<16}\n'.format('ENGLISH','PRONUNCIATION','ORTHOGRAPHIC'))
                    lexOut.insert(END, addition) # Add addition
                    lexOut.configure(state='disabled') # Disable editing
                    return lexicon[i][2][j] # Exit function
    elif (wordtype != None) and (wordtype != 4): # Condition for wordtypes not ALL
        lexOut.configure(state='normal')
        lexOut.delete(1.0,END) # Clear box
        lexOut.insert(END, '{0:<16}{1:<16}{2:<16}\n'.format('ENGLISH','PRONUNCIATION','ORTHOGRAPHIC'))
        for i,x in enumerate(lexicon[wordtype][0]):
            addition = ('{0:<16}{1:<16}{2:<16}\n'.format(x,lexicon[wordtype][1][i],lexicon[wordtype][2][i]))
            lexOut.insert(END, addition) # Add found words
        lexOut.configure(state='disabled')
    elif wordtype == 4: # Condition for ALL
        lexOut.configure(state='normal')
        lexOut.delete(1.0,END)
        lexOut.insert(END, '{0:<16}{1:<16}{2:<16}\n'.format('ENGLISH','PRONUNCIATION','ORTHOGRAPHIC'))
        for i,table in enumerate(lexicon):
            for j,x in enumerate(table[0]):
                addition = ('{0:<16}{1:<16}{2:<16}\n'.format(x,lexicon[i][1][j],lexicon[i][2][j]))
                lexOut.insert(END, addition) # Add found word
        lexOut.configure(state='disabled')

def regenerateLexicon(dropoff, cOffset, vOffset):
    try: # Destroy lexWindow
        lexWindow.state()
        lexWindow.destroy()
    except:
        pass
    finally:
        global syllableForms, lexicon # Regenerate syllableForms and lexicon
        syllableForms = generate.syllableStructure(phonology, dropoff=dropoff)
        lexicon = lexiconGen(syllableForms, phonology, orthography)
        showLexWindow(lexicon, dropoff, cOffset, vOffset) # Open lexWindow, passing through options

def generateInstance(dropoff, cOffset, vOffset):
    try:
        lexWindow.state()
        lexWindow.destroy()
    except:
        pass
    finally:
        global phonology, orthography, wordOrder, syllableForms, verbSystem, nounSystem, pluralSystem, articleSystem, declensionSystem, morphSystem, lexicon
        # Generate core language
        phonology = generate.phonology(cOffset, vOffset)
        orthography = generate.orthography(phonology)
        wordOrder = generate.sentenceOrder()
        syllableForms = generate.syllableStructure(phonology, dropoff=dropoff)
        # Initialise and generate features
        feature = Features(phonology, wordOrder, syllableForms)
        verbSystem = feature.verbs()
        nounSystem = feature.nouns()
        pluralSystem = nounSystem[0]
        articleSystem = nounSystem[1]
        declensionSystem = nounSystem[2]
        morphSystem = feature.morphology()
        # Generate lexicon
        lexicon = lexiconGen(syllableForms, phonology, orthography)
        showLexWindow(lexicon, dropoff, cOffset, vOffset) # Open the lexicon language overview window, passing through options

def saveInstance(menubar):
    menubar.entryconfig('File',state='disabled')
    # Pack together variables to make saving easier to manage
    corePack = [phonology, orthography, wordOrder, syllableForms]
    featurePack = [verbSystem, nounSystem, morphSystem]
    lexPack = lexicon
    
    # Pack together packs into one array
    totalDump = [corePack, featurePack, lexPack]

    # Initialise file prompt
    files = [("genLang Language Files","*.glang")]
    filename = filedialog.asksaveasfilename(filetypes = files, defaultextension=files)
    if filename != '': # If not exited before save
        savePickleFile(totalDump, filename)
    menubar.entryconfig('File',state='normal')

def loadInstance(menubar):
    menubar.entryconfig('File',state='disabled')
    # Initialise file load prompt
    files = [("genLang Language Files","*.glang")]
    filename = filedialog.askopenfilename(filetype = files, defaultextension=files)
    menubar.entryconfig('File',state='normal')
    if filename != '': # If not exited before load
        global phonology, orthography, wordOrder, syllableForms, verbSystem, nounSystem, pluralSystem, articleSystem, declensionSystem, morphSystem, lexicon
        lexWindow.destroy() # Close lex window
        # Load and separate packs
        data = loadPickleFile(filename)
        corePack = data[0]
        featurePack = data[1]
        
        # Redefine global variables according to pack
        phonology = corePack[0]
        orthography = corePack[1]
        wordOrder = corePack[2]
        syllableForms = corePack[3]

        verbSystem = featurePack[0]
        nounSystem = featurePack[1]
        pluralSystem = nounSystem[0]
        articleSystem = nounSystem[1]
        declensionSystem = nounSystem[2]
        morphSystem = featurePack[2]
        
        lexicon = data[2]
        
        showLexWindow(lexicon, 100, 0, 0) # Open lex window

                                          
generate = Generators() # Init generator object


master = Tk() # Establish the master window
master.title("genLang")
master.resizable(width=False, height=False)

optionFrame = Frame(master) # Create a frame for options
optionFrame.grid(row=2, column=0, sticky=W+E)

Label(optionFrame, text='Dropoff level:').grid(row=0, column=0, sticky=W, padx=5, pady=5) # Create labels for sliders
Label(optionFrame, text='Consonant offset:').grid(row=1, column=0, sticky=W, padx=5, pady=5)
Label(optionFrame, text='Vowel offset:').grid(row=2, column=0, sticky=W, padx=5, pady=5)

dropoffScale = Scale(optionFrame, from_=10, to=1000, orient=HORIZONTAL) # Create slider for dropoff
dropoffScale.set(100)
dropoffScale.grid(row=0, column=1, padx=5, pady=5, sticky=W)

consonantOffset = Scale(optionFrame, from_=0, to=len(generate.consonants)-6, orient=HORIZONTAL) # Create slider for consonant offset
consonantOffset.grid(row=1, column=1, padx=5, pady=5, sticky=W)

vowelOffset = Scale(optionFrame, from_=0, to=len(generate.vowels)-3, orient=HORIZONTAL) # Create slider for vowel offset
vowelOffset.grid(row=2, column=1, padx=5, pady=5, sticky=W)

dropExp = 'This controls the approximate amount of syllable structures generated. Higher dropoff values mean more structures.'
offExp = 'This controls how small the sound inventory of the language approximately is. Larger values mean smaller inventories.'

dropoffInfo = Button(optionFrame, text='?', command=lambda:Mbox('Dropoff',dropExp, 0x40))
dropoffInfo.grid(row=0, column=2, sticky=W, padx=5, pady=5) # Create help message for dropoff slider
offsetInfo = Button(optionFrame, text='?', command=lambda:Mbox('Offset',offExp, 0x40))
offsetInfo.grid(row=1, column=2, sticky=W, padx=5, pady=5) # Create help message for offset slider


Label(master, text='Welcome to genLang 0.0').grid(row=0, sticky=N+S+E+W, padx=50, pady=5)
Button(master, text='Generate', command=lambda:generateInstance(dropoffScale.get(),
                                                                consonantOffset.get(),
                                                                vowelOffset.get())).grid(row=1,
                                                                                         column=0,
                                                                                         padx=15,
                                                                                         pady=15,
                                                                                         sticky=E+W) # Create generate button

menubar = Menu(master) # Create menu bar
helpmenu = Menu(menubar, tearoff=0)
helpmenu.add_command(label="About genLang", command=showAboutWindow) # Add about window
filemenu = Menu(menubar, tearoff=0)
filemenu.add_command(label="Exit", command=exit) # Add other
menubar.add_cascade(label="File", menu=filemenu)
menubar.add_cascade(label="Help", menu=helpmenu)
master.config(menu = menubar)

mainloop( ) # Start tkinter

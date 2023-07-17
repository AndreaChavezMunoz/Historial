# Funciones generales 

import json 
import string
from unidecode import unidecode
import pandas as pd
from io import BytesIO

def load_data(file):
    """
    Loads json data
    ** file: str. File path
    """

    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return (data)


def clean_text(textInput, lowerCase = False, unidecodeStandard = False, skipStopWords = False):
    """
    Opens and cleans text
    
    ** textInput: str. Text to clean
    ** lowercase: Boolean. Default False. Converts all text to lowercase
    ** unidecodeStandard: Boolean. Default False. Gets rid of special caracters. 
                        Needs to be developed more
    ** split: Boolean. Default False. Splits sentences into a list of words
    """
    # Open
    if textInput == None:
        return None
    if lowerCase: 
        textInput = textInput.lower()
   
    # Define element to delete
    punc = string.punctuation + "”°»º–•“"

    # Get rids of special accents and transforms unidecode
    if unidecodeStandard:
        textInput = unidecode(textInput)
        textInput = textInput.replace("\n", "")

    # Delete special caracters
    for ele in textInput:
        if ele in punc:
            textInput = textInput.replace(ele," ")


    # Deletes stop words
    if skipStopWords:
        stopwords = load_data("./data/stop_words.json")
        textInput = ' '.join([word for word in textInput.split() if word not in stopwords])

    # Gets rid of white trailing
    textInput=textInput.strip()

    return textInput


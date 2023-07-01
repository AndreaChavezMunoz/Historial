# Import data
from __future__ import print_function
import os.path
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from _general import clean_text
import spacy
import subprocess
import sys
from gensim.models.word2vec import Word2Vec
from gensim.models.keyedvectors import KeyedVectors
import multiprocessing
import numpy as np
from tqdm import tqdm
from annoy import AnnoyIndex
import json

# CONECTARSE A BASE DE DATOS 
# Could be cached
def connect_sheet(credentials):
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    # Connect to database
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

# CONSEGUIR DATOS DE BASE DE DATOS
def get_data(creds):

    # The ID and range of a sample spreadsheet.
    SAMPLE_SPREADSHEET_ID = '1Ge_nrrNF9VoVMysRiGm-Is53jSMh2OL_8cxTIimfpxE'
    bd_cotizaciones = 'BD_Cotizaciones_de_proveedores!A1:Q'
    planilla = 'Planilla!A1:G'

    # Call the Sheets API
    service = build('sheets', 'v4', credentials=creds) 
    sheet = service.spreadsheets()

    # Get data from database
    bd_cotizaciones_data = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=bd_cotizaciones).execute()
    bd_cotizaciones_data_values = bd_cotizaciones_data.get("values",[])

    planilla_data = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=planilla).execute()
    planilla_data_values = planilla_data.get("values",[])

    # Save as pandas dataframe
    df_bd = pd.DataFrame.from_records(bd_cotizaciones_data_values[1:],columns=bd_cotizaciones_data_values[0])
    df_planilla = pd.DataFrame.from_records(planilla_data_values[1:],columns=planilla_data_values[0])
    df_bd.to_csv("./data/productos_cotizados.csv", index=False)

    return df_bd, df_planilla

# NORMALIZAR NOMBRES
def normalize(df,columna_producto):
    new_column ="Norm_" + columna_producto 
    df[new_column] = [clean_text(producto,True,True,True) for producto in df[columna_producto]]

    return df

# COMBINAR NOMBRES DFs
def combinar_bd(df1,df2,column1,column2):
    """
    Combines two pandas DFs

    ** df1 = pandas DF al que añadir valores
    ** df2 = pandas DF del que se sacaran valores
    ** column1,2 = Str. Nombre de la columna con el idx de connecion

    Lista a conseguir
    # Producto solicitado
    # Producto ofrecido
    # Categorias
    # Producto solicitado con categorias
    # Producto ofrecido con categorias
    # Producto solicitado con categoria y todos los prod ofrecidos
    """
    # Combinar dfs
    df = pd.merge(df1, df2,
                       how='left', left_on=column1, right_on=column2)
    
    # Make TRAIN_DATA
    TRAIN_DATA = []
    # Producto solicitado
    TRAIN_DATA = TRAIN_DATA + df["Norm_Producto Solicitado"].values.tolist() 
    # Producto ofrecido
    TRAIN_DATA = TRAIN_DATA + df["Norm_Producto Ofrecido"].values.tolist() 
    # Categorias
    TRAIN_DATA = TRAIN_DATA + df["Norm_Categoria"].values.tolist() 
    # Producto solicitado con categorias
    df["sol_categoria"] = df["Norm_Producto Solicitado"]+ " "+ df["Norm_Categoria"]
    TRAIN_DATA = TRAIN_DATA + df["sol_categoria"].values.tolist() 
    # Producto ofrecido con categorias
    df["ofr_categoria"] = df["Norm_Producto Ofrecido"]+ " "+ df["Norm_Categoria"]
    TRAIN_DATA = TRAIN_DATA + df["ofr_categoria"].values.tolist() 
    # Producto solicitado con categoria y todos los prod ofrecidos
    df["todo"] = df["Norm_Producto Solicitado"]+ " " + df["Norm_Categoria"] + " " +df["Norm_Producto Ofrecido"]
    TRAIN_DATA = TRAIN_DATA + df["todo"].values.tolist()  

    # Remove duplicates
    TRAIN_DATA = list(set(TRAIN_DATA))
    
    return TRAIN_DATA

# CREAR VECTORES
def create_vectors(data):
    """
    Crea gensim vectors
    ** data: list of words normalized and without stop words
    """

    # Split data
    texts = []
    for producto in data:
        if isinstance(producto,str) and len(producto)>0: 
            producto_split = producto.split(" ")
            palabras = []
            for word in producto_split:
                word = word.strip()
                
                if len(word) > 0:
                    palabras.append(word)
            texts.append(palabras)

    # Create wordVector
    cores = multiprocessing.cpu_count()
    w2v_model = Word2Vec(min_count=3,
                            window=2,
                            vector_size=500,
                            sample=6e-5,
                            alpha=0.03,
                            min_alpha=0.0007,
                            negative=20,
                            workers=cores-1)
    w2v_model.build_vocab(texts)
    w2v_model.train(texts, total_examples=w2v_model.corpus_count,epochs=30)

    # Save data
    w2v_model.wv.save_word2vec_format("data/vectores.txt")

# COPIAR VECTORS EN MODELO DE SPACY
def load_word_vectors():

    model_name = "./model"

    nlp = spacy.blank("es-419")
    nlp.to_disk(model_name)


    subprocess.run([sys.executable,"-m","spacy",
                    "init", "vectors","es","data/vectores.txt",model_name])
    
# USAR LISTA DE PRODUCTOS OFRECIDOS PARA CREAR INDICE
def create_index(df_productos):

    # Load model
    nlp = spacy.load("./model")

    # Get data from df
    train_list = df_productos[["Norm_Producto Ofrecido","TRAZA"]].values.tolist() 
    train_list = dict(zip(df_productos["TRAZA"], df_productos["Norm_Producto Ofrecido"]))

    # Create annoy object
    annoy_index = AnnoyIndex(500,'euclidean')

    # Make a dictionary for reference data
    reference = {}

    # For every produtct
    for ix,(traza,text) in tqdm(enumerate(train_list.items())):
        if text != None:

            # Convert to vector
            doc = nlp(text) 

            # Add to annoy index
            annoy_index.add_item(ix, doc.vector)

            # Add data to reference dictionary
            reference[ix] = (traza,text)
    annoy_index.build(10)

    # Save data
    annoy_index.save('./data/product_index.ann')

    with open("./data/reference_map.json", "w",encoding="utf-8") as f:
        json.dump(reference, f, indent = 4)
   
    return 

def run(cred):

    # Connectarse con google
    credential = connect_sheet(cred)

    # Conseguir datos
    df_productos, df_planilla = get_data(credential)

    # Normalizar nombres
    df_productos = normalize(df_productos,"Producto Ofrecido")
    df_planilla = normalize(df_planilla,"Categoria")
    df_planilla = normalize(df_planilla,"Producto Solicitado")

    # Combinar nombres
    TRAIN_DATA = combinar_bd(df_productos,df_planilla,"Producto Solicitado","TRAZA")

    # Crear vectores
    create_vectors(TRAIN_DATA)

    # Copiar vectores en spacy
    load_word_vectors()

    # Crear indice
    create_index(df_productos)
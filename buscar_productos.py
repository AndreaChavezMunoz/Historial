# Import data
import spacy
from _general import clean_text
import pandas as pd
from annoy import AnnoyIndex
import json
from cryptography.fernet import Fernet

def serach_product(word):
    """ 
    Takes: str
    Returns: list of tuples (TRAZA, nombre de producto)
    """
    # Load model
    nlp = spacy.load("./model")

    # Load index
    annoy_index = AnnoyIndex(500, 'euclidean')
    annoy_index.load('./data/product_index.ann')
    
    # Find vector of word based in spacy model
    word = clean_text(word,lowerCase=True,unidecodeStandard=True,skipStopWords=True)
    search_doc = nlp(word)
    search_vector = search_doc.vector

    # Search in index the 10 closest points to the vector found
    res = annoy_index.get_nns_by_vector(search_vector, 10)

    # Get the word that is represented by each of the vectors found
    # Get values from reference map (TRAZA, nombre de producto)
    with open("./data/reference_map.json", "r", encoding="utf-8") as f:
        reference = json.load(f)

    productos = []
    for ix in res:
        p = reference[str(ix)]
        productos.append(p)



    return productos
        

# Load past data
def open_productos_cotizados():
    # Load encrypted data
    with open('./data/filekey.key', 'rb') as filekey:
        encrypt_key = filekey.read()

    # Create decoder
    f = Fernet(encrypt_key)

    token = pd.read_csv('./data/productos.csv') 
    token = token.applymap(lambda x: bytes(x[2:-1],'utf-8'))
    token  = token.applymap(lambda x: f.decrypt(x))
    token = token.applymap(lambda x: x.decode('utf-8'))

    columns = list(token.columns.values)
    columns = map(lambda x: bytes(x[2:-1],'utf-8'),columns)
    columns = map(lambda x: f.decrypt(x), columns)
    columns = map(lambda x: x.decode('utf-8'), columns)


    token.columns = columns
    productos_cotizados = token
    productos_cotizados.set_index('TRAZA',inplace=True)

    return productos_cotizados
    


# BUSCAR PRODUCTOS IMPORTADOS CON PLANILLA 
def to_str(x):
    x = str(x)
    if x == 'nan':
        return ""
    else:
        return x
    
def search_file(path, productos_cotizados):

    # Leer datos subidos por usuario
    planilla = pd.read_excel(path, index_col= None)
    productos_solicitados  = planilla[["Producto Solicitado",
                                       "Nombre de producto Solicitado",
                                       "U. Medida solicitada", 
                                       "Cantidad Solicitada"]].values.tolist() 

    # Create new dataframe to save n products found for each product requested
    todos_productos_similares = pd.DataFrame()

    # Search every product input by the user
    for TRAZA_sol, prod, medida, cant in productos_solicitados:
        productos_similares = serach_product(prod) # [[producto_TRAZA, producto_normalized_name],...[]]
        
        # Get all trazas
        trazas = []
        for (traza, _) in productos_similares:
            
            trazas.append(str(traza))
        
        # Find products from FIGsac database
        productos_similares = productos_cotizados.loc[trazas]
    
        # Añadir info de producto_solicitado a productos_similares
        productos_similares["Producto Solicitado"] =  TRAZA_sol
        productos_similares["Nombre de producto Solicitado"] =  prod
        productos_similares["U. Medida solicitada"] =  medida
        productos_similares["Cantidad Solicitada"] =  cant

        # Add all productos_similares to todos_productos_similares
        productos_similares.reset_index(inplace=True)
        todos_productos_similares =  pd.concat([todos_productos_similares, productos_similares], ignore_index = True)
    
    # Add comentaries about the origin of data
    todos_productos_similares["Observaciones"] = "Datos copiados de producto " + todos_productos_similares["TRAZA"].map(str)  + todos_productos_similares["Observaciones"].map(to_str) 

    # Copy only necessary data to return
    resultado = pd.DataFrame()
    resultado["Cotizacion"] = todos_productos_similares["Cotizacion"]
    resultado["Producto Solicitado"] = todos_productos_similares["Producto Solicitado"]
    resultado["Nombre de producto Solicitado"] = todos_productos_similares["Nombre de producto Solicitado"]
    resultado["U. Medida solicitada"] = todos_productos_similares["U. Medida solicitada"]
    resultado["Cantidad Solicitada"] = todos_productos_similares["Cantidad Solicitada"]
    resultado["Producto Ofrecido"] = todos_productos_similares["Producto Ofrecido"]
    resultado["U. Medida"] = todos_productos_similares["U. Medida"]
    resultado["Cantidad"] = todos_productos_similares["Cantidad"]
    resultado["Costo x Unidad"] = todos_productos_similares["Costo x Unidad"]
    resultado["Precio Venta x Unidad"] = todos_productos_similares["Precio Venta x Unidad"]
    resultado["Cotizacion"] = todos_productos_similares["Cotizacion"]
    resultado["Observaciones"] = todos_productos_similares["Observaciones"]  

    return resultado     
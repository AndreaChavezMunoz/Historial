# Import data
import spacy
from _general import clean_text
import pandas as pd
from annoy import AnnoyIndex
import json

# BUSCAR N NUMERO DE PRODUCTOS MAS PARECIDOS

def serach_product(word):
    # Load model
    nlp = spacy.load("./model")

    # Load index
    annoy_index = AnnoyIndex(500, 'euclidean')
    annoy_index.load('./data/product_index.ann')
    
    # Make search into vector
    word = clean_text(word,lowerCase=True,unidecodeStandard=True,skipStopWords=True)
    search_doc = nlp(word)
    search_vector = search_doc.vector

    # Search in index
    res = annoy_index.get_nns_by_vector(search_vector, 10)

    # Get values from reference map
    with open("./data/reference_map.json", "r", encoding="utf-8") as f:
        reference = json.load(f)

    productos = []
    for ix in res:
        productos.append(reference[str(ix)])

    return productos

# BUSCAR PRODUCTOS IMPORTADOS CON PLANILLA 
def to_str(x):
    x = str(x)
    if x == 'nan':
        return ""
    else:
        return x
    
def search_file(path):

    # Cargar base de datos de productos
    productos_cotizados = pd.read_csv("./data/productos_cotizados.csv", index_col=15)

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
        for traza, _ in productos_similares:
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
    resultado["Nombre de producto Solicitado"] = todos_productos_similares["Nombre de producto Solicitado"]
    resultado["Producto Ofrecido"] = todos_productos_similares["Producto Ofrecido"]
    resultado["Cotizacion"] = todos_productos_similares["Cotizacion"]
    resultado["Producto Solicitado"] = todos_productos_similares["Producto Solicitado"]
    resultado["U. Medida solicitada"] = todos_productos_similares["U. Medida solicitada"]
    resultado["Cantidad Solicitada"] = todos_productos_similares["Cantidad Solicitada"]
    resultado["U. Medida"] = todos_productos_similares["U. Medida"]
    resultado["Cantidad"] = todos_productos_similares["Cantidad"]
    resultado["Costo x Unidad"] = todos_productos_similares["Costo x Unidad"]
    resultado["Precio Venta x Unidad"] = todos_productos_similares["Precio Venta x Unidad"]
    resultado["Cotizacion"] = todos_productos_similares["Cotizacion"]
    resultado["Observaciones"] = todos_productos_similares["Observaciones"]  

    return resultado
            

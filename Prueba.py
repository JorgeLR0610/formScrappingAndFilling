import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import unicodedata

# --- CONFIGURACIÓN INICIAL ---
path_json = "data/preguntas.json"
excel_path = "data/acosoPrueba.xlsx"
form_url = "https://docs.google.com/forms/d/e/1FAIpQLScliBrZ2EED5oVLlZB5LDWVUhzotH-oXkbTFRRpU2c6PjBU2g/viewform?usp=sharing&ouid=111425962232891575232" #Emilio copia
progreso = "data/progreso.txt"
cantidad_por_tanda = 4 #Aquí se define cuántos registros se van a llenar 310

# --- CARGAR ESTRUCTURA DEL FORMULARIO ---
with open(path_json, "r", encoding="utf-8") as f:
    estructura_formulario = json.load(f)

# --- CARGAR RESPUESTAS DEL EXCEL ---
df = pd.read_excel(excel_path) #De forma predeterminada, ignora la primer fila al tomarlos como encabezados y empieza a tomar como datos a partir de la segunda. Cargar registros del rango actual

# --- INICIAR CHROME ---
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 0.5)
waitBtnSiguiente = WebDriverWait(driver, 5)
# Leer progreso desde archivo
def leer_indice_inicio():
    with open(progreso, "r") as f:
        return int(f.read().strip())
    
# Guardar nuevo índice al final
def guardar_indice_inicio(nuevo_indice):
    with open(progreso, "w") as f:
        f.write(str(nuevo_indice))

inicio = leer_indice_inicio()
fin = inicio + cantidad_por_tanda
dftanda = df.iloc[inicio:fin]

# Verificar si hay suficientes datos
if dftanda.empty:
    print("Ya no hay más registros por enviar.")
    driver.quit()
    exit()
    
#Función para que haga clic en el botón siguiente para avanzar de página o en enviar si está en la última página
def clicSiguiente(wait):
    botonXpath = '//div[@role="button"]//span[text()="Siguiente" or text()="Enviar"]/ancestor::div[@role="button"]'
    wait.until(EC.visibility_of_element_located((By.XPATH, botonXpath)))
    boton = wait.until(EC.element_to_be_clickable((By.XPATH, botonXpath)))
    
    #Obtiene el texto que aparezca en el botón
    span = boton.find_element(By.XPATH, './/span')
    texto = span.text.strip()
    
    boton.click()
    return texto == "Enviar"

def limpiarEspacios(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return unicodedata.normalize("NFKC", texto.replace('\xa0', ' ')).strip()

def llenar_formulario(fila):
    fila = {limpiarEspacios(k): limpiarEspacios(v) for k, v in fila.items()}
    
    driver.get(form_url)
    try:
        WebDriverWait(driver, 0.2).until(EC.presence_of_element_located((By.XPATH, '//div[@role="listitem"]')))
        wait.until(EC.visibility_of_element_located((By.XPATH, '//span[@class="M7eMe"]')))
    except:
        clicSiguiente(waitBtnSiguiente)
    
    while True:
        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, '//span[@class="M7eMe"]')))
            bloques_preguntas = driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
            
            for bloque in bloques_preguntas:
                try:
                    textoCrudo = bloque.find_element(By.CSS_SELECTOR, "span.M7eMe").text
                    texto_pregunta = limpiarEspacios(textoCrudo)
                except:
                    continue  #No es una pregunta válida

                pregunta = next((p for p in estructura_formulario if p['pregunta'].strip() == texto_pregunta), None)
                if not pregunta:
                    print(f"Pregunta no encontrada en estructura: {texto_pregunta}")
                    continue

                tipo = pregunta['tipo']
                id_ = pregunta['id']
                valor = str(fila.get(texto_pregunta, "")).strip()

                try:
                    if tipo == "radio":
                        opciones = bloque.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                        labels = [op.get_attribute("aria-label") or "" for op in opciones]
                        
                        # quitar espacios, &nbsp;
                        valor_limpio = valor.replace('\xa0', ' ').strip()
                        labels_limpios = [lbl.replace('\xa0', ' ').strip() for lbl in labels]

                        if valor_limpio in labels_limpios:
                            for opcion in opciones:
                                if (opcion.get_attribute("aria-label") or "").replace('\xa0', ' ').strip() == valor_limpio:
                                    opcion.click()
                                    break
                        else:
                            # Seleccionar la opción "Otro", "Otro:", o vacía ([SIN TEXTO])
                            for opcion in opciones:
                                label = (opcion.get_attribute("aria-label") or "").replace('\xa0', ' ').strip()
                                if label in ["Otro", "Otro:", "[SIN TEXTO]", ""]:
                                    opcion.click()
                                    try:
                                        input_otro = bloque.find_element(By.CSS_SELECTOR, "input[type='text']")
                                        input_otro.clear()
                                        input_otro.send_keys(valor_limpio)
                                    except Exception as e:
                                        print(f"No se pudo escribir en el campo 'Otro' para '{texto_pregunta}':", e)
                                    break

                    elif tipo == "texto":
                        campo = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"input[aria-labelledby='{id_}']")))                    
                        campo.clear()
                        campo.send_keys(valor)
                    # Aquí hubiera añadido los checkboxes si hubieran jalado
                    
                    elif tipo == "textarea": #Para textarea, esto es lo que podría fallar ahorita, porque sí hace el scraping correctamente en el otro archivo
                        campo = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"textarea[aria-labelledby='{id_}']")))                    
                        campo.clear()
                        campo.send_keys(valor)
                        
                    elif tipo == "checkbox":
                        seleccionadas = [op.strip() for op in valor.split(";") if op.strip()] #El carácter que marca el split es ;, recordarlo
                        opciones = bloque.find_elements(By.CSS_SELECTOR, "div[role='checkbox']")
                        for opcion in opciones:
                            etiqueta = opcion.get_attribute("aria-label")
                            if etiqueta in seleccionadas:
                                opcion.click()

                except Exception as e:
                    print(f"Error al responder '{texto_pregunta}':", e)
            #Botón clic siguiente y/o enviar
            try:
                clicSiguiente(waitBtnSiguiente)
            except:
                break  
        except:
            try:
                esFinal = clicSiguiente(waitBtnSiguiente)
                if esFinal:
                    print(f"Formulario {i+1} enviado")
                    break
            except:
                break             

# --- BUCLE PRINCIPAL---
for i, fila in dftanda.iterrows():
    print(f"\n--- Enviando formulario {i+1} ---")
    llenar_formulario(fila)
    time.sleep(0.3)

guardar_indice_inicio(fin)
driver.quit()
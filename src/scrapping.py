# type: ignore
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import unicodedata

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 0.5) #El segundo parámetro define cuánto tiempo va a esperar como máximo antes de que arroje una excepción

# Form URL
driver.get("")

def clicSiguiente(wait):
    botonXpath = '//div[@role="button"]//span[text()="Siguiente"]'
    wait.until(EC.visibility_of_element_located((By.XPATH, botonXpath)))
    boton = wait.until(EC.element_to_be_clickable((By.XPATH, botonXpath)))
    boton.click()

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='listitem']")))

# Esperar a que se cargue al menos un bloque de pregunta; eso de div[role='listitem'] es cómo google forms marca cada pregunta
try:
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='listitem']")))
except:
    clicSiguiente(wait)
    
def limpiarEspacios(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return unicodedata.normalize("NFKC", texto.replace('\xa0', ' ')).strip()

def seleccionarRespuestas(wait):
    preguntas = []
    #Este while va a servir para que vaya avanzando de página hasta que llegue a la última
    while True:
        #Cada elemento de esta lista representa un bloque de pregunta en el formulario. Así, las preguntas suelen estar contenidas en un div de role listitem
        bloques_preguntas = driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")

        #Este bucle for itera sobre la lista de elementos WebElement (probablemente divs) y se podría entender como: Para cada bloque () dentro de la lista bloques_preguntas, haz lo siguiente
        #bloque es una variable temporal que en cada vuelta del bucle, toma el valor de un elemento de la lista
        #in bloques_preguntas significa que se está iterando (recorriendo) todos los elementos en la lista bloques_preguntas
        for bloque in bloques_preguntas:
            try:
                #Ese span M7eMe parece ser constante para todos los formularios, es decir, las preguntas siempre están contenidas en un span con ese id, pero aun así es lo más volátil porque podría ser que cambie, intentar sustituirlo por otra cosa más segura
                textoPregunta = bloque.find_element(By.CSS_SELECTOR, "span.M7eMe").text
                #Esto era para ver que estuviera guardando bien las respuestas print(textoPregunta)
            except:
                pass
            
            try: #Para radiobuttons
                # Esta línea busca todas las opciones de respuesta de tipo radiobutton que están dentro del bloque actual (es decir, dentro de la pregunta actual).
                opciones_radio = bloque.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                if opciones_radio:
                    opciones_radio[0].click() #Selecciona la primera opción
                    #print(f"[RADIO] {textoPregunta}")
                    radiogroupID = bloque.find_element(By.CSS_SELECTOR, "div[role='radiogroup']")
                    #print(radiogroupID.get_attribute("aria-labelledby"))
                    
                    #Esto es para obtener el texto de las respuestas
                    opciones = []
                    for opcion in opciones_radio:
                        try:
                            texto = opcion.get_attribute("aria-label")
                            if texto:
                                opciones.append(texto.strip())
                            else:
                                opciones.append("[SIN TEXTO]")
                        except Exception as e:
                            print("Excepción atrapada:", e)
                            opciones.append("[ERROR]")
                    #Aquí se guardan los datos de cada pregunta
                    pregunta_info = {
                        "pregunta": limpiarEspacios(textoPregunta),
                        "tipo": "radio",
                        "id": radiogroupID.get_attribute("aria-labelledby"),
                        "opciones": opciones
                    }
                    preguntas.append(pregunta_info)
                    continue
            except:
                pass
            
            try: #Para campos de texto
                campo_texto = bloque.find_element(By.CSS_SELECTOR, "input[type='text']")
                if campo_texto:
                    campo_texto.send_keys("21")
                    #print(f"[TEXTO] {textoPregunta}") #Coloco 21 porque generalmente ese campo será la edad y ahora solo relleno con datos cualquiera para poder avanzar de páginas e ir haciendo el scraping
                    inputID = campo_texto.get_attribute("aria-labelledby")
                   #print(inputID) #Esto nomás era para probar, creo que ya podría quitarlo
                    pregunta_info = {
                    "pregunta": limpiarEspacios(textoPregunta),
                    "tipo": "texto",
                    "id": inputID,
                    "valor_enviado": "21"
                    }
                    preguntas.append(pregunta_info)
                    continue
            except:
                pass
                
            try:# Para checkboxes 
                opciones_checkbox = bloque.find_elements(By.CSS_SELECTOR, "div[role='checkbox']")
                if opciones_checkbox:
                    checkboxID = bloque.find_element(By.CSS_SELECTOR, "div[role='list']")
                    opciones = []
                    
                    for opcion in opciones_checkbox:
                        try:
                            texto = opcion.get_attribute("aria-label")
                            if texto:
                                opciones.append(texto.strip())
                            else:
                                opciones.append("[SIN TEXTO]")
                        except Exception as e:
                            print("Excepción atrapada:", e)
                            opciones.append("[ERROR]")
                            
                    opciones_checkbox[0].click()
                    #print(f"[CHECKBOX] {textoPregunta}")
                    #print(checkboxID.get_attribute("aria-labelledby"))
                    #Aquí se guardan los datos de cada pregunta
                    pregunta_info = {
                        "pregunta": limpiarEspacios(textoPregunta),
                        "tipo": "checkbox",
                        "id": checkboxID.get_attribute("aria-labelledby"),
                        "opciones": opciones
                    }
                    preguntas.append(pregunta_info)
                    continue
            except:
                pass
                
            try: #Para párrafo (campos de texto largo)
                textArea = bloque.find_element(By.CSS_SELECTOR, "textarea")
                if textArea:
                    textArea.send_keys("21")
                    #print(f"[TEXTAREA] {textoPregunta}") #Coloco 21 porque generalmente ese campo será la edad y ahora solo relleno con datos cualquiera para poder avanzar de páginas e ir haciendo el scraping
                    inputID = textArea.get_attribute("aria-labelledby")
                    #print(inputID)
                    pregunta_info = {
                    "pregunta": limpiarEspacios(textoPregunta),
                    "tipo": "textarea",
                    "id": inputID,
                    "valor_enviado": "TextoPrueba"
                    }
                    preguntas.append(pregunta_info)
                    continue
            except:
                pass
                
                
        try:
            clicSiguiente(wait)
        except:
            print("No hay más páginas, cerrando el navegador.")
            break
    driver.quit()
    with open("data/preguntas.json", "w", encoding="utf-8") as f:
        json.dump(preguntas, f, ensure_ascii=False, indent=2)
    
seleccionarRespuestas(wait)
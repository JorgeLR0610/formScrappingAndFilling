import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()

#Ruta al txt de progreso
progreso = "data/progreso.txt"

cantidad_por_tanda = 84 #Aquí se define cuántos registros se van a llenar

# Leer progreso desde archivo
def leer_indice_inicio():
    with open(progreso, "r") as f:
        return int(f.read().strip())
    
# Guardar nuevo índice al final
def guardar_indice_inicio(nuevo_indice):
    with open(progreso, "w") as f:
        f.write(str(nuevo_indice))
        
# Ruta al excel
excel_path = "data/simulacion.xlsx"
# Cargar registros del rango actual
df = pd.read_excel(excel_path) #De forma predeterminada, ignora la primer fila al tomarlos como encabezados y empieza a tomar como datos a partir de la segunda

inicio = leer_indice_inicio()
fin = inicio + cantidad_por_tanda
dftanda = df.iloc[inicio:fin]

# Verificar si hay suficientes datos
if dftanda.empty:
    print("Ya no hay más registros por enviar.")
    driver.quit()
    exit()

# URL del formulario
# ******ORIGINAL******
form_url = "https://docs.google.com/forms/d/e/1FAIpQLSeXds1eHGCo68SDeodAKkG05EOQ9VdtagziXYIE_Wyq9jHu4A/viewform"

#Función para que haga clic en el botón siguiente para avanzar de página o en enviar si está en la última página
def clicSiguiente(wait):
    botonXpath = '//div[@role="button"]//span[text()="Siguiente" or text()="Enviar"]/ancestor::div[@role="button"]'
    wait.until(EC.visibility_of_element_located((By.XPATH, botonXpath)))
    boton = wait.until(EC.element_to_be_clickable((By.XPATH, botonXpath)))
    
    #Obtiene el texto que aparezca en el botón
    span = boton.find_element(By.XPATH, './/span')
    texto = span.text.strip()
    
    if texto == "Siguiente":
        boton.click()
    elif texto == "Enviar":
        boton.click()
    else:
        print(f"Texto inesperado en el botón: {texto}")
    
# Función para llenar la primera página
def fill_page_1_acuerdo(driver, row):
    driver.get(form_url)
    wait = WebDriverWait(driver, 15)
    
    #Medida de seguridad para saber que la página se cargó por completo
    wait.until(EC.visibility_of_element_located((By.XPATH, '//span[text()="¿Estoy de acuerdo?"]')))
    
    # Pregunta 1: ¿Estoy de acuerdo?
    opcion = row['¿Estoy de acuerdo?']
    xpath_opcion = f'//div[@data-value="{opcion}"]'
    
    wait.until(EC.visibility_of_element_located((By.XPATH, xpath_opcion)))
    wait.until(EC.element_to_be_clickable((By.XPATH, xpath_opcion))).click()

    # Clic en "Siguiente"
    clicSiguiente(wait)


def fill_page_2_demografia(driver, row):
    wait = WebDriverWait(driver, 10)

    # Esperar campo de edad
    campo_edad = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@jsname="YPqjbf"]')))
    wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@jsname="YPqjbf"]'))).click()
    campo_edad.send_keys(str(row['Edad']))

    campos = ['Género', 'Escolaridad', 'Ocupación principal', 'Nivel de ingresos', 'Religión']
    for campo in campos:
        valor = row[campo]
        if valor == 'Otro' and campo == 'Religión':
            xpath_opcion = f'(//div[@role="listitem"])[7]//div[@data-value="Otro"]'
        else:
            xpath_opcion = f'//div[@data-value="{valor}"]'
        wait.until(EC.visibility_of_element_located((By.XPATH, xpath_opcion)))
        wait.until(EC.element_to_be_clickable((By.XPATH, xpath_opcion))).click()

    # Clic en "Siguiente"
    clicSiguiente(wait)
    
def fill_page_3_apariencia(driver, row):
    wait = WebDriverWait(driver, 10)

    campos = ['Tono de piel', 'Color de pelo', 'Color de ojos']
    for campo in campos:
        valor = row[campo]
        xpath_opcion = f'//div[@data-value="{valor}"]'
        wait.until(EC.visibility_of_element_located((By.XPATH, xpath_opcion))).click()

    # Clic en "Siguiente"
    clicSiguiente(wait)
    
def fill_page_4_factorA(driver, row):
    wait = WebDriverWait(driver, 10)
    # Preguntas de la 1 a la 9, usando como identificador el aria_labelledby
    preguntas = {
        1: {'aria_labelledby': 'i1 i4', 'columna_excel': '1. Me han dejado de lado en actividades grupales sin razón aparente.'},
        2: {'aria_labelledby': 'i6 i9', 'columna_excel': '2. Siento que las personas me evitan activamente en entornos sociales.'},
        3: {'aria_labelledby': 'i11 i14', 'columna_excel': '3. En actividades en grupo, percibo que se me deja de lado.'},
        4: {'aria_labelledby': 'i16 i19', 'columna_excel': '4. Me siento aislado/a por mis compañeros.'},
        5: {'aria_labelledby': 'i21 i24', 'columna_excel': '5. He sido excluido/a de reuniones informales en el trabajo/escuela.'},
        6: {'aria_labelledby': 'i26 i29', 'columna_excel': '6. Me siento rechazado/a cuando intento unirme a ciertos grupos.'},
        7: {'aria_labelledby': 'i31 i34', 'columna_excel': '7. Me doy cuenta de que no soy bienvenido/a en ciertos espacios.'},
        8: {'aria_labelledby': 'i36 i39', 'columna_excel': '8. Mi opinión no es considerada en decisiones importantes en mi entorno.'},
        9: {'aria_labelledby': 'i41 i44', 'columna_excel': '9. En mi comunidad, siento que no pertenezco.'}
    }
    for datos_pregunta in preguntas.values():
        valor = str(row[datos_pregunta['columna_excel']])  # Asegura que sea string
        aria_labelledby = datos_pregunta['aria_labelledby']
        opcion_xpath = f'//div[@role="radiogroup"][@aria-labelledby="{aria_labelledby}"]//div[@data-value="{valor}"]'
        opcion = wait.until(EC.visibility_of_element_located((By.XPATH, opcion_xpath)))
        opcion.click()
            
    # Clic en "Siguiente"
    clicSiguiente(wait)
    
def fill_page_5_factorB(driver, row):
    wait = WebDriverWait(driver, 10)
    preguntas = {
        10: {'aria_labelledby': 'i1 i4', 'columna_excel': '10. Recibo comentarios negativos basados en mi apariencia.'},
        11: {'aria_labelledby': 'i6 i9', 'columna_excel': '11. Me han hecho sentir inferior por mi apariencia.'},
        12: {'aria_labelledby': 'i11 i14', 'columna_excel': '12. He sido víctima de apodos ofensivos.'},
        13: {'aria_labelledby': 'i16 i19', 'columna_excel': '13. Me han tratado de forma condescendiente por mi identidad.'},
        14: {'aria_labelledby': 'i21 i24', 'columna_excel': '14. Me han dicho que no encajo en ciertos espacios.'}
    }
    for datos_pregunta in preguntas.values():
        valor = str(row[datos_pregunta['columna_excel']])
        aria_labelledby = datos_pregunta['aria_labelledby']
        opcion_xpath = f'//div[@role="radiogroup"][@aria-labelledby="{aria_labelledby}"]//div[@data-value="{valor}"]'
        opcion = wait.until(EC.visibility_of_element_located((By.XPATH, opcion_xpath)))
        opcion.click()
        
    # Clic en "Siguiente"
    clicSiguiente(wait)
    

def fill_page_6_factorC(driver, row):
    wait = WebDriverWait(driver, 10)
    preguntas = {
        15: {'aria_labelledby': 'i1 i4', 'columna_excel': '15. He sido excluido/a de capacitaciones relevantes.'},
        16: {'aria_labelledby': 'i6 i9', 'columna_excel': '16. He sido descalificado/a de procesos sin motivos objetivos.'},
        17: {'aria_labelledby': 'i11 i14', 'columna_excel': '17. Las decisiones de mi entorno parecen sesgadas en mi contra.'},
        18: {'aria_labelledby': 'i16 i19', 'columna_excel': '18. Me han rechazado de oportunidades por mi apariencia.'},
        19: {'aria_labelledby': 'i21 i24', 'columna_excel': '19. Me han tratado como menos competente sin motivos objetivos.'},
        20: {'aria_labelledby': 'i26 i29', 'columna_excel': '20. Se me ha negado participar en ciertos eventos por prejuicios.'}
    }
    for datos_pregunta in preguntas.values():
        valor = str(row[datos_pregunta['columna_excel']])
        aria_labelledby = datos_pregunta['aria_labelledby']
        opcion_xpath = f'//div[@role="radiogroup"][@aria-labelledby="{aria_labelledby}"]//div[@data-value="{valor}"]'
        opcion = wait.until(EC.visibility_of_element_located((By.XPATH, opcion_xpath)))
        opcion.click()
        
    # Clic en "Siguiente"
    clicSiguiente(wait)
    

def fill_page_7_factorD(driver, row):
    wait = WebDriverWait(driver, 10)
    preguntas = {
        21: {'aria_labelledby': 'i1 i4', 'columna_excel': '21. Me han tratado con hostilidad solo por pertenecer a cierto grupo social.'},
        22: {'aria_labelledby': 'i6 i9', 'columna_excel': '22. Me han ridiculizado públicamente debido a aspectos personales o de identidad.'},
        23: {'aria_labelledby': 'i11 i14', 'columna_excel': '23. He recibido amenazas de daño físico por parte de otras personas.'},
        24: {'aria_labelledby': 'i16 i19', 'columna_excel': '24. Siento que debo cambiar mi comportamiento o apariencia para evitar acoso.'},
        25: {'aria_labelledby': 'i21 i24', 'columna_excel': '25. He notado que ciertas personas intentan intimidarme para que no participe en actividades.'},
        26: {'aria_labelledby': 'i26 i29', 'columna_excel': '26. El acoso que he experimentado ha afectado mi desempeño académico o laboral.'},
        27: {'aria_labelledby': 'i31 i34', 'columna_excel': '27. He sido objeto de acoso persistente en redes sociales o plataformas digitales.'}
    }
    for datos_pregunta in preguntas.values():
        valor = str(row[datos_pregunta['columna_excel']])
        aria_labelledby = datos_pregunta['aria_labelledby']
        opcion_xpath = f'//div[@role="radiogroup"][@aria-labelledby="{aria_labelledby}"]//div[@data-value="{valor}"]'
        opcion = wait.until(EC.visibility_of_element_located((By.XPATH, opcion_xpath)))
        opcion.click()
        
    # Clic en "Siguiente"
    clicSiguiente(wait)

def fill_page_8_factorE(driver, row):
    wait = WebDriverWait(driver, 10)
    preguntas = {
        28: {'aria_labelledby': 'i1 i4', 'columna_excel': '28. Me han tratado con desconfianza sin motivo aparente.'},
        29: {'aria_labelledby': 'i6 i9', 'columna_excel': '29. Siento que debo esforzarme más que otros para demostrar mi valía.'},
        30: {'aria_labelledby': 'i11 i14', 'columna_excel': '30. Considero que los prejuicios tienen un impacto negativo en mis oportunidades de crecimiento.'},
        31: {'aria_labelledby': 'i16 i19', 'columna_excel': '31. Me han hecho sentir que no pertenezco a ciertos espacios debido a mi identidad.'},
        32: {'aria_labelledby': 'i21 i24', 'columna_excel': '32. Es probable que siga enfrentando prejuicios en el futuro.'},
        33: {'aria_labelledby': 'i26 i29', 'columna_excel': '33. He sido tratado/a de manera diferente a pesar de tener las mismas habilidades que otros.'},
        34: {'aria_labelledby': 'i31 i34', 'columna_excel': '34. He experimentado miradas o actitudes de sorpresa cuando demuestro competencia en ciertas áreas.'},
        35: {'aria_labelledby': 'i36 i39', 'columna_excel': '35. El trato desigual que recibo debido a prejuicios ha afectado mi bienestar emocional.'},
        36: {'aria_labelledby': 'i41 i44', 'columna_excel': '36. He evitado ciertos espacios porque sé que enfrentaré prejuicios.'}
    }
    for datos_pregunta in preguntas.values():
        valor = str(row[datos_pregunta['columna_excel']])
        aria_labelledby = datos_pregunta['aria_labelledby']
        opcion_xpath = f'//div[@role="radiogroup"][@aria-labelledby="{aria_labelledby}"]//div[@data-value="{valor}"]'
        opcion = wait.until(EC.visibility_of_element_located((By.XPATH, opcion_xpath)))
        opcion.click()
    
    # Última página: Click en "Enviar"
    clicSiguiente(wait)
    
#Bucle principal
for i, row in dftanda.iterrows():
    fill_page_1_acuerdo(driver, row)
    fill_page_2_demografia(driver, row)
    fill_page_3_apariencia(driver, row)
    fill_page_4_factorA(driver, row)
    fill_page_5_factorB(driver, row)
    fill_page_6_factorC(driver, row)
    fill_page_7_factorD(driver, row)
    fill_page_8_factorE(driver, row)
    print(f"Formulario {i+1} completado.")
    time.sleep(0.3)

guardar_indice_inicio(fin)
driver.quit()
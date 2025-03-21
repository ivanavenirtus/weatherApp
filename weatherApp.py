import os
from flask import Flask, request, Response
import requests
from wand.image import Image
from wand.drawing import Drawing
from wand.color import Color
from dotenv import load_dotenv

load_dotenv()

class Clima:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    def consulta_ciudad(self, ciudad):
        params = {
            'q': ciudad,
            'appid': self.api_key,
            'units': 'metric'
        }
        response = requests.get(self.base_url, params=params)
        return response.json()

    def extrae_relevantes(self, ciudad):
        weather_data = self.consulta_ciudad(ciudad)
        
        if 'name' not in weather_data:
            return None
        
        icono = weather_data['weather'][0]['icon']  
        es_dia = icono.endswith("d")  

        return {
            'ciudad': weather_data['name'],
            'temperatura': weather_data['main']['temp'],
            'es_dia': es_dia,
            'icono': f"https://openweathermap.org/img/wn/{icono}.png"
        }

weather03 = Flask(__name__)
c = Clima()

@weather03.route('/clima', methods=['GET'])
def generar_imagen_clima():
    ciudad = request.args.get('ciudad', 'Ciudad Desconocida')
    
    datos = c.extrae_relevantes(ciudad)
    if datos is None:
        return {"error": "Ciudad no encontrada"}, 404

    color_fondo = "#B3E5FC" if datos["es_dia"] else "#1a1630"
    color_texto = "#1a1630" if datos["es_dia"] else "#B3E5FC"
    color_tint = "#0066CC" if datos["es_dia"] else "#FFD700"  

    width, height = 1000, 600  
    
    ruta_fuente = os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'a4.TTF')  # Relativa al directorio actual
    
    if not os.path.exists(ruta_fuente):
        return {"error": f"Fuente no encontrada en {ruta_fuente}"}, 500

    with Image(width=width, height=height, background=Color(color_fondo)) as img:
        with Drawing() as draw:
            draw.font = ruta_fuente  
            draw.font_size = 50
            draw.fill_color = Color(color_texto)

            draw.text_alignment = 'center'
            draw.text(width // 2, height // 2, datos['ciudad'])

            draw.text_alignment = 'right'
            draw.text(width - 50, 80, f"{datos['temperatura']}°C")  

            draw(img) 

        # DESCARGA ICONO
        icono_respuesta = requests.get(datos["icono"], stream=True)
        if icono_respuesta.status_code == 200:
            with Image(file=icono_respuesta.raw) as icono:
                icono.resize(100, 100)
                icono.tint(Color(color_tint), Color("white"))  
                img.composite(icono, left=20, top=20) 
        
        img_bytes = img.make_blob('png')

    return Response(img_bytes, mimetype='image/png')

# Muestra el mapeo de rutas
print(weather03.url_map)

if __name__ == '__main__':
    weather03.run(debug=True, host='0.0.0.0', port=5000)  



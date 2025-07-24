from flask import Flask, render_template
from pytrends.request import TrendReq

# Iniciar Flask
app = Flask(__name__)

# Iniciar pytrends
pytrends = TrendReq(hl='en-US', tz=360)

@app.route('/')
def index():
    # Obtener las 10 búsquedas más populares globalmente
    trends = pytrends.trending_searches(pn='global')  # Usa 'global' para obtener tendencias globales
    
    # Convertir las tendencias a una lista
    trending_list = trends.head(10).values.tolist()  # Limitar a las 10 primeras

    return render_template('index.html', trends=trending_list)

if __name__ == '__main__':
    app.run(debug=True)

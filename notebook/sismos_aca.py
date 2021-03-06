# -*- coding: utf-8 -*-
"""Sismos - ACA.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1_VWD9yoQ2bL-JlUiwMJs5D0bgnMe38mo

# Predicción de sismos - ACA

## Librerias necesarias
Existe una serie de herramientas externas que seran incluidas en el proyecto con el fin de simplificar el proceso de analisis del modelo
"""

!apt-get install libgeos
!apt-get install libgeos-dev
!pip install https://github.com/matplotlib/basemap/archive/master.zip
print('done')

!pip install pyproj==1.9.6

# Commented out IPython magic to ensure Python compatibility.
# Importando librerrias necesarias para la creación de datasets
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

#Se usa de un archivo de Excel que se encuentra en nuestro drive
from google.colab import drive
drive.mount('/content/drive')

# %matplotlib inline

"""## 1. Lectura de registros
Actualmente el equipo genero el csv. Este se baso en extraer información del SIG de sismos de MARM, realizando una consulta HTTP especificando la extraccción de datos registrados desde 2010 al presente día.

El [SIG](http://mapas.snet.gob.sv/geologia/sismicidad.phtml) útilizado proporciona información publica por lo que ha sido anexado para futura referencia
"""

#Este notebook depende del archivo csv para realizar todos los procesos
df = pd.read_csv("drive/My Drive/Sismos-el-salvador.csv")
df.head()

#Este bloque de codigo es opcional y se encarga de filtrar el dataset de valores atipicos que se encuentran muy alejados de El Salvador
for idx, row in df.iterrows():
  latitud = row['Latitud N(°)']
  longitud = row['Longitud W(°)']
  if (latitud < 12 or latitud > 14.5) or (longitud < -91 or longitud > -87.5):
    df.drop(idx, inplace=True)

"""## 2. Cambiar formato de fecha a texto y luego a número"""

# Las fechas ingresadas son transformadas a una representación numerica con el objetivo de ser estudiadas de manera cuantitativa
import datetime
import time as tlib
months = [None, "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov" , "Dic"]
timestamp = []

def twoDigit(field):
  return field if(int(field) > 9 and len(field) > 1) else '0'+str(field)


for date, time in zip(df["Fecha"], df['Hora local']):
    # Date format check
    dateSp = date.split()
    month = months.index(dateSp[0])
    monthStrFormat = twoDigit(str(month))
    day = str(dateSp[1]).replace(',','')
    year = dateSp[2]
    formatDate = year+'-'+monthStrFormat+'-'+day

    # Time format check
    timeSp = time.split(":")
    hour = twoDigit(timeSp[0])
    timeFormat = hour +':'+ timeSp[1] +':'+ timeSp[2]
    ts = datetime.datetime.strptime(formatDate+' '+timeFormat, '%Y-%m-%d %I:%M:%S %p')
    timestamp.append(tlib.mktime(ts.timetuple()))
    
   
print(timestamp)

"""## 3. Limpiar la tabla de dataset"""

#Agrega las columnas especiales adicionales
timeStamp = pd.Series(timestamp)
df['Timestamp'] = timeStamp.values
df.head()

#Elimina columnas innecesarias para los modelos
final_data = df.drop(['Fecha', 'Hora local'], axis=1)
final_data = final_data[final_data.Timestamp != 'ValueError']


final_data.head()

final_data = final_data.drop(['Localizacion', 'Intensidad'], axis=1)
final_data.head()

"""## 4. Mapa de actividad sísmica
Usando los datos extraídos del mapa se han marcado con puntos azules los terremotos registrados en El Salvador. Observando el mapa es posible notar visualmente que existen zonas con gran frecuencia sísmica. Con esta información visual se conjetura que existe un patrón, casi todos los terremotos registrados se forman atravesando el país y las costas.
"""

#Prepara los datos para el mapa
m = Basemap(projection='mill',llcrnrlat=10, llcrnrlon=-97,urcrnrlon=-83, urcrnrlat=17, resolution='l' )
longitudes = final_data["Longitud W(°)"].tolist()
latitudes = final_data["Latitud N(°)"].tolist()

x,y = m(longitudes,latitudes)

#Crea un mapa digital del pais y le inserta datos
fig = plt.figure(figsize=(12,10))
plt.title("Terremotos en El Salvador")
m.plot(x, y, "o", markersize = 1, color = 'blue')
m.drawcoastlines()
m.fillcontinents(color='white',lake_color='aqua')
m.drawmapboundary()
m.drawcountries()
plt.show()

"""## 5.1. Modelo de predicción de latitud y longuitud
Utilizando los registros proporcionados por MARN nos enfocamos en analizar un análisis para un modelo. El objetivo es determinar si a través de una fecha, magnitud y profundidad es posible encontrar un patrón o relación con las coordenadas del terremoto.
"""

from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

x = final_data[['Timestamp','Magnitud','Profundidad (km)']]
y = final_data[['Latitud N(°)', 'Longitud W(°)']]


# Sacar las variables dividiendolos datos
x_train, x_test, y_train, y_test = train_test_split(x, y, train_size=0.80, test_size=0.20, random_state=20)
max_depth = 100

print(x_train.shape, x_test.shape, y_train.shape, y_test.shape)

"""### RandomForestRegressor"""

#Se crear una regresión usando el algoritmo de random forest regressor
from sklearn.ensemble import RandomForestRegressor

regr_rf = RandomForestRegressor(n_estimators=70, max_depth=max_depth,random_state=1, min_samples_split = 2, min_samples_leaf = 1)

regr_rf.fit(x_train, y_train)
y_ranfo = regr_rf.predict(x_test)

r2_score(y_test, y_ranfo)

from sklearn.model_selection import GridSearchCV

n_estimators = [40, 80, 120, 140, 160]
max_depth = [5, 8, 15, 25, 30]
min_samples_split = [2, 5, 10, 15, 100]
min_samples_leaf = [1, 2, 5, 10] 

hyperF = dict(n_estimators = n_estimators, max_depth = max_depth,  
              min_samples_split = min_samples_split, 
             min_samples_leaf = min_samples_leaf)

gridF = GridSearchCV(regr_rf, hyperF, cv = 3, verbose = 1, 
                      n_jobs = -1)
bestF = gridF.fit(x_train, y_train)

y_grid = bestF.predict(x_test)
print(r2_score(y_test, y_grid, multioutput='variance_weighted'))

"""### MultiOutputRegressor"""

from sklearn.multioutput import MultiOutputRegressor

regr_multirf = MultiOutputRegressor(regr_rf)
regr_multirf.fit(x_train, y_train)
y_multirf = regr_multirf.predict(x_test)

r2_score(y_test, y_multirf, multioutput='variance_weighted')

"""### KNeighborsRegressor"""

from sklearn.neighbors import KNeighborsRegressor

k_neighbor = KNeighborsRegressor(n_neighbors=70, weights='distance',leaf_size=50 )
k_neighbor.fit(x_train, y_train)
y_pred = k_neighbor.predict(x_test)

r2_score(y_test, y_pred, multioutput='variance_weighted')

"""### Guardar modelo"""

import joblib

filename = 'LatitudLonguitudF.sav'
best_fit = gridF

joblib.dump(best_fit, filename)

loaded_model = joblib.load(filename)
y_loadp = loaded_model.predict(x_test)
print(y_loadp)

loaded_model.predict([[12321,70,121]])

"""## 5.2. Modelo de predicción de magnitud y profundidad

Así como el primer modelo se hace uso de los registros de MARN, pero con un enfoque distinto. El objetivo de este modelo es determinar si a través de una fecha y coordenadas es posible encontrar un comportamiento de dependencia para la profundidad y magnitud de un terremoto.
"""

from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

x = final_data[['Timestamp','Latitud N(°)','Longitud W(°)']]
y = final_data[['Magnitud', 'Profundidad (km)']]


# Sacar las variables dividiendolos datos
x_train, x_test, y_train, y_test = train_test_split(x, y, train_size=0.80, test_size=0.20, random_state=0)
max_depth = 30

print(x_train.shape, x_test.shape, y_train.shape, y_test.shape)

"""### RandomForestRegressor"""

from sklearn.ensemble import RandomForestRegressor

regr_rf = RandomForestRegressor(random_state=8, max_depth=max_depth)
regr_rf.fit(x_train, y_train)

from sklearn.model_selection import GridSearchCV

parameters = {'n_estimators':[10, 20, 50, 70, 120]}

grid_obj = GridSearchCV(regr_rf, parameters)
grid_fit = grid_obj.fit(x_train, y_train)
best_fit = grid_fit.best_estimator_
y_ranfo = best_fit.predict(x_test)

r2_score(y_test, y_ranfo, multioutput='variance_weighted')

"""### MultiOutputRegressor"""

from sklearn.multioutput import MultiOutputRegressor

regr_multirf = MultiOutputRegressor(RandomForestRegressor(n_estimators=70,max_depth=max_depth,random_state=0))
regr_multirf.fit(x_train, y_train)
y_multirf = regr_multirf.predict(x_test)

r2_score(y_test, y_multirf, multioutput='variance_weighted')

"""### KNeighborsRegressor"""

from sklearn.neighbors import KNeighborsRegressor
from sklearn.datasets import make_regression

x, y = make_regression(n_samples=70, n_features=10, n_informative=5, n_targets=2, random_state=1)
k_neighbor = KNeighborsRegressor()
k_neighbor.fit(x_train, y_train)
y_pred = k_neighbor.predict(x_test)

r2_score(y_test, y_pred, multioutput='variance_weighted')

"""### Guardar modelo"""

import joblib
from sklearn.metrics import r2_score

def best_model(M1, M2, M3):
  score_1 = r2_score(y_test, y_ranfo, multioutput='variance_weighted')
  score_2 = r2_score(y_test, y_multirf, multioutput='variance_weighted')
  score_3 = r2_score(y_test, y_pred, multioutput='variance_weighted')
  if (score_1 >= score_2) and (score_1 >= score_3): 
      return M1
  
  elif (score_2 >= score_1) and (score_2 >= score_3): 
      return M2
  else: 
      return M3

filename = 'LatitudLonguitud.sav'
best_fit = best_model(regr_rf, regr_multirf, k_neighbor)

joblib.dump(best_fit, filename)

loaded_model = joblib.load(filename)
y_loadp = loaded_model.predict(x_test)
print(y_loadp)

loaded_model.predict([[12321,70,121]])

from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

x = final_data[['Magnitud','Profundidad (km)','Latitud N(°)', 'Longitud W(°)']]
y = final_data[['Timestamp']]

# Sacar las variables dividiendolos datos
x_train, x_test, y_train, y_test = train_test_split(x, y.values.ravel(), train_size=0.80, test_size=0.20, random_state=4)

print(x_train.shape, x_test.shape, y_train.shape, x_test.shape)

import statsmodels.api as sm 
model = sm.OLS(y_train, x_train).fit() 
y_pred = model.predict(x_test)


print("Mean absolute error: %.2f" % np.mean(np.absolute(y_pred - y_test)))
print("Residual sum of squares (MSE): %.2f" % np.mean((y_pred - y_test) ** 2))
print("R2-score: %.2f" % r2_score(y_pred , y_test) )
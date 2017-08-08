import pandas as pd
from Tkinter import Tk		# Ventana para seleccionar archivo
from tkFileDialog import askopenfilename

def main():
    Tk().withdraw()		# No queremos GUI completa
    path = askopenfilename()

    headers = ['COD_EMP', 'AAAAMMDDHHMM', 'TIPO_COMUNICACION', 'TIPO_EQUIPO','TIPO_TECNOLOGIA','TIPO_PLAN','NUMERO','MARCA','MODELO','IMEI','SIMCARD','FECHA_DENUNCIA','IDO/IDD']

    # Importa archivos con TAC y a procesar
    dframe = pd.read_csv(path, sep = ';', names = headers, dtype = str, skiprows = 2)
    lista_terminales = pd.read_csv('lista.txt', sep = ';', header = 0, dtype = str)

    # Inserta fecha reporte como segunda columna
    indice_fecha = path.find('TM_205')
    dframe['AAAAMMDD'] = path[(indice_fecha + 7):(indice_fecha + 15)]
    dframe = dframe[['COD_EMP','AAAAMMDD', 'AAAAMMDDHHMM', 'TIPO_COMUNICACION', 'TIPO_EQUIPO','TIPO_TECNOLOGIA','TIPO_PLAN','NUMERO','MARCA','MODELO','IMEI','SIMCARD','FECHA_DENUNCIA','IDO/IDD']]
    print "Importados: {}".format(dframe['IMEI'].count())

    # Elimina robos masivos
    print "Masivos: {}".format(dframe[dframe.TIPO_COMUNICACION == 'T']['IMEI'].count())
    dframe = dframe[dframe.TIPO_COMUNICACION != 'T']

    # Saca los segundos de columna AAAAMMDDHHMM y agrega 0's al Numero, IMEI y SIMCARD para cunmplir con los formatos.
    dframe.NUMERO = dframe.NUMERO.astype(str)
    dframe.IMEI = dframe.IMEI.astype(str)
    dframe.SIMCARD = dframe.SIMCARD.astype(str)
    row_iterator = dframe.iterrows()
    last = row_iterator
    for i, row in row_iterator:
        row.AAAAMMDDHHMM = row.AAAAMMDDHHMM[:12]
        if row.NUMERO == '0' or row.NUMERO == 0:
            row.NUMERO = '56910000000'
        if row.NUMERO == 'nan':
            row.NUMERO = str('56910000000')
        if row.IMEI == '0' or row.IMEI == 0:
            row.IMEI = row.IMEI.zfill(15)
        if row.IMEI == 'nan':
            row.IMEI = '0'.zfill(15)
        if row.SIMCARD == '0' or row.SIMCARD == 0:
            row.SIMCARD = row.SIMCARD.zfill(15)
        if row.SIMCARD == 'nan':
            row.SIMCARD = '0'.zfill(15)
        last = row

    # Elimina los NUMERO fjos (que parten con algo distinto a 569)
    print "Fijos: {}".format(dframe[dframe.NUMERO.str[:3] == '562']['IMEI'].count())
    dframe = dframe[dframe.NUMERO.str[:3] != '562']

    # Elimina IMEI duplicados con tipo de comunicacion y fecha de denuncia
    print "Condicion: {}".format(dframe[dframe.duplicated(['IMEI', 'TIPO_COMUNICACION', 'FECHA_DENUNCIA'], keep = 'first')]['IMEI'].count())
    dframe = dframe[-dframe.duplicated(['IMEI', 'TIPO_COMUNICACION', 'FECHA_DENUNCIA'], keep = 'first')]
    print "Exportados: {}".format(dframe['IMEI'].count())

    # Sumar un segundo si hay dos comunicaciones para un mismo IMEI en la misma AAAAMMDDHHMM
    #dframe.sort_values('TIPO_COMUNICACION')
    dframe['bool'] = dframe.duplicated(['IMEI', 'AAAAMMDDHHMM'], keep = 'first')
    row_iterador = dframe.iterrows()
    last = row_iterador
    cnt = 0
    for i, row in row_iterador:
        cnt +=1
        if dframe.loc[i, 'bool'] == True:
            if int(dframe.loc[i, 'AAAAMMDDHHMM'][10:]) < 59:
                print dframe.loc[i, 'AAAAMMDDHHMM']
                if int(dframe.loc[i, 'AAAAMMDDHHMM'][10:]) < 10:
                    dframe.loc[i, 'AAAAMMDDHHMM'] = dframe.loc[i, 'AAAAMMDDHHMM'][:10] + '0' + str(int(dframe.loc[i, 'AAAAMMDDHHMM'][10:]) + 1)
                else:
                    dframe.loc[i, 'AAAAMMDDHHMM'] = dframe.loc[i, 'AAAAMMDDHHMM'][:10] + str(int(dframe.loc[i, 'AAAAMMDDHHMM'][10:]) + 1)
                print dframe.loc[i, 'AAAAMMDDHHMM']
            elif int(dframe.loc[i, 'AAAAMMDDHHMM'][10:]) == 59:
                if int(dframe.loc[i, 'AAAAMMDDHHMM'][8:10]) < 59:
                    dframe.loc[i, 'AAAAMMDDHHMM'] = str(int(dframe.loc[i, 'AAAAMMDDHHMM'][8:10]) + 1) + '00'
        last = row

    del dframe['bool']

    # Actualiza marca y modelo de los equipos terminales y agrega OTRO FABRICANTE cuando no se tiene la informacion
    dframe['TAC'] = dframe['IMEI'].str[:8]
    agregar =  pd.concat([dframe['TAC'], dframe['MARCA'], dframe['MODELO']], axis = 1, keys = ['TAC', 'MARCA', 'MODELO'])
    lista_terminales = lista_terminales.append(agregar).drop_duplicates('TAC', keep = 'first')
    lista_terminales = lista_terminales[lista_terminales['MARCA'] != 'OTRO FABRICANTE']
    del dframe['MARCA']
    del dframe['MODELO']
    dframe = pd.merge(dframe, lista_terminales, left_on = 'TAC', right_on ='TAC', how = 'left')
    dframe['MARCA'].fillna('OTRO FABRICANTE', inplace = True)
    dframe['MODELO'].fillna('OTRO FABRICANTE', inplace = True)
    dframe = dframe[['COD_EMP','AAAAMMDD', 'AAAAMMDDHHMM', 'TIPO_COMUNICACION', 'TIPO_EQUIPO','TIPO_TECNOLOGIA','TIPO_PLAN','NUMERO','MARCA','MODELO','IMEI','SIMCARD','FECHA_DENUNCIA','IDO/IDD']]

    # Exporta el archivos
    salida = "TM_205_{}_ROBOS_ALTAS.txt".format(path[(indice_fecha + 7):(indice_fecha + 15)])

    # Exporta los archivos a la misma carpeta
    salida = "TM_205_{}_ROBOS_ALTAS.txt".format(path[(indice_fecha + 7):(indice_fecha + 15)])
    dframe.to_csv(salida, sep = ';', header = False, index = False)
    lista_terminales.to_csv('lista.txt', sep = ';', header = True, index = False)

if __name__ == "__main__":
    main()
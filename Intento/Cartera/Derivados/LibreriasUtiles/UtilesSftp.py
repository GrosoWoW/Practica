import pysftp



def get_file_names(hostname, username, password, input_directory):
    """
    Función para obtener nombres de archivos y subdirectorios en SFTP
    :param hostname: string con nombre de host
    :param username: string con el nombre de usuario
    :param password: string con la contraseña de conexión
    :param input_directory: string con el direcotorio que se desea acceder
    :return: list con nombres de archivos o sub-directorios
    """
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    with pysftp.Connection(host=hostname, username=username, password=password, cnopts=cnopts) as sftp:
        # Switch to a remote directory
        sftp.cwd(input_directory)

        directory_structure = sftp.listdir_attr()
        remoteFileNames = []
        #Obtenemos el archivo

        if len(directory_structure) == 0:
            return remoteFileNames

        for attr in directory_structure:
            remoteFileNames.append(attr.filename)

    return remoteFileNames


def get_files(hostname, username, password, input_directory):
    """
    Función para obtener nombres de archivos y subdirectorios en SFTP
    Deja una copia de los archivos de forma local
    :param hostname: string con nombre de host
    :param username: string con el nombre de usuario
    :param password: string con la contraseña de conexión
    :param input_directory: string con el direcotorio que se desea acceder
    :return: list con nombres de archivos o sub-directorios
    """
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    with pysftp.Connection(host=hostname, username=username, password=password, cnopts=cnopts) as sftp:
        # Switch to a remote directory
        sftp.cwd(input_directory)

        directory_structure = sftp.listdir_attr()
        remoteFileNames = []
        #Obtenemos el archivo

        if len(directory_structure) == 0:
            return remoteFileNames

        for attr in directory_structure:
            remoteFileNames.append(attr.filename)
            localFilePath = './'+attr.filename
            sftp.get(attr.filename, localFilePath)

    return remoteFileNames


def move_file(hostname, username, password, from_directory, to_directory, filename, new_filename=None):
    """
    Función para mover un archivo de un lugar a otro en el sftp
    :param hostname: string con nombre de host
    :param username: string con el nombre de usuario
    :param password: string con la contraseña de conexión
    :param from_directory: string con nombre del directorio actual del archivo
    :param to_directory: string con nombre del directorio destino del archivo
    :param filename: string con el nombre del archivo que se desea mover
    :param new_filename: nombre nuevo del archivo. Si viene vacío se utiliza el nombre original.
    :return: None
    """

    if new_filename is None:
        new_filename = filename

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    with pysftp.Connection(host=hostname, username=username, password=password, cnopts=cnopts) as sftp:
        sftp.cwd(from_directory)
        #Se mueve el archivo

        if not sftp.isdir(to_directory):
            sftp.mkdir(to_directory)

        newFilePath = to_directory + new_filename

        if sftp.isfile(newFilePath):
            sftp.remove(newFilePath)

        sftp.rename(filename,newFilePath)




def put_file(hostname, username, password, from_directory, to_directory, from_filename, to_filename=None):
    """
    Función para subir un archivo de local al sftp
    Si hay un archivo ya existente con el nombre lo ELIMINA
    :param hostname: string con nombre de host
    :param username: string con el nombre de usuario
    :param password: string con la contraseña de conexión
    :param from_directory: string con nombre del directorio actual del archivo
    :param to_directory: string con nombre del directorio destino del archivo
    :param from_filename: string con el nombre del archivo que se desea subir
    :param to_filename: string con el nombre final de archivo. Si es vacio se mantiene el nombre
    :return: None
    """

    if to_filename is None:
        to_filename = from_filename

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    with pysftp.Connection(host=hostname, username=username, password=password, cnopts=cnopts) as sftp:
        
        if not sftp.isdir(to_directory):
            sftp.mkdir(to_directory)

        if sftp.isfile(to_directory + to_filename):
            sftp.remove(to_directory + to_filename)

        sftp.cwd(to_directory)
        sftp.put(from_directory + from_filename, to_filename)


def put_file_lva(filename, fecha):
    myHostname = "ftp.lvaindices.com" 
    myUsername = "lva-derivados"
    myPassword = "1JC8cP"
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    with pysftp.Connection(host=myHostname, username=myUsername, password=myPassword, cnopts=cnopts) as sftp:
        

        sftp.cwd('/En_proceso/')
        if sftp.isdir('/Historico/'+fecha) == False:
            sftp.mkdir('/Historico/'+fecha)
        #Lo movemos de lugar, ya que fue procesado
        newFilePath = '/Historico/'+fecha+'/'+filename
        sftp.rename(filename,newFilePath)
        
        # Switch to a remote directory
        sftp.cwd('/Output/')
        if sftp.isdir(fecha) == False:
            sftp.mkdir(fecha)
        sftp.cwd(fecha)

        remoteFilePath_log = 'Log_valorizacion_'+filename
        localFilePath_log = './Log_valorizacion_'+filename
        sftp.put(localFilePath_log,remoteFilePath_log)

        remoteFilePath_Valorizado = 'Derivados_Valorizados_'+filename
        localFilePath__Valorizado = './Derivados_Valorizados_'+filename
        sftp.put(localFilePath__Valorizado,remoteFilePath_Valorizado)
        print("Carga completa")


def put_error_lva(filename, fecha):
    myHostname = "ftp.lvaindices.com" 
    myUsername = "lva-derivados"
    myPassword = "1JC8cP"
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    with pysftp.Connection(host=myHostname, username=myUsername, password=myPassword, cnopts=cnopts) as sftp:
        
        #Lo movemos de lugar, ya que fue procesado
        if sftp.isdir('/ERROR/' + fecha) == False:
            sftp.mkdir('/ERROR/' + fecha)
        newFilePath = '/ERROR/' + fecha + '/' + filename
        sftp.put(filename,newFilePath)
        print("Archivos dejados en directorio de error")


def error_file_lva(filename, fecha):
    myHostname = "ftp.lvaindices.com" 
    myUsername = "lva-derivados"
    myPassword = "1JC8cP"
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    with pysftp.Connection(host=myHostname, username=myUsername, password=myPassword, cnopts=cnopts) as sftp:
        

        sftp.cwd('/En_proceso/')
        #Lo movemos de lugar, ya que fue procesado
        if sftp.isdir('/ERROR/' + fecha) == False:
            sftp.mkdir('/ERROR/' + fecha)
        newFilePath = '/ERROR/' + fecha + '/' + filename
        sftp.rename(filename,newFilePath)
        print("Archivos dejados en directorio de error")
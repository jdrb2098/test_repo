import paramiko
from io import StringIO
def sftp_test_conection():
    # Datos de conexión
    host = '201.131.100.101'
    port = 22  # Puerto SFTP por defecto
    username = 'sftperyuju'
    password = '$3cuR.2oL7mbe'
    private_key = '''
    -----BEGIN RSA PRIVATE KEY-----
    Proc-Type: 4,ENCRYPTED
    DEK-Info: DES-EDE3-CBC,4815E62213F3C47D

uW91MuiV5TgDJ8TUI3J404AopFrTcEKrjF3b1zr9FXVq7+GRm32pXZqnBMAp8e3U
Kn5w5R0J8CLzht2ewVGEVTYRP5fCeTuSK/F3O9Xe7QhiscisVATuqXoz8xr89c6d
4fTI+3YmJ0JIueAn5rfOp0fTWh5mXH8ia4Tri8hS5mIx5xyOac2eT2thETIF9dx0
VeFKK18qx77Forfu+R0CFmnEq+nWk9xcSB7ARwDAshcgpkaaOLwlmeDWSKQmqqCh
9PbaFRBrnnOAMAWTVFxgmOCZraYlEWg8bKu3+bWD9DgG59ddsvyC+o4NV2h44N0W
hkVWMaq0y7nQ0LKPZ+U46gy5n1pynwwpkhp3ibnZ6nN4/NXcwEKCCsUWTnBo2yoP
9HmrS97thUFV6XBNmEKea/Z9zWwkIQcuK+cqOKlGu5gIuT0rtKoNsllq0wUuVbTI
8aDaFv+aXtx5mDHzy1nuD3li4KXr67jz4bguVV6GsU9lthDfDdHc/emtp2Wl4/uh
ybwss4lJM69xwjOk2zmhlJukfuHg6dkWp6QS1nVlrNawLc5qFHlqq2gNgsBu3oag
t1afr1sY1nz5BKPEHeYxFc9eZkHPvhynVbXysw4KBqx5HPdcDwxh7byYEfoTSSGU
mwMNtFU8RUQUqxyMqutnLcZ4nw53PJMae54Ec263EHZwA1ms7UKH0haCRhC75E7X
CjU3kNek0KHI3L1WjMZjmaTvKrB1yUr93hrlGhiyx2kGpsvDyrdCHTXvh+LygE3C
s+b944YTam1+rEvYhLuu0L6uulSAp6eU/QrqABrW3mqBkqbwMNtOww==
-----END RSA PRIVATE KEY----- 
    '''
    passphrase = '$L4ve.Valu3Mb'

    # Crear una instancia de cliente SFTP
    client = paramiko.Transport((host, port))
    # Autenticar utilizando la clave privada protegida por frase de paso
    key = paramiko.RSAKey(file_obj=StringIO(private_key), password=passphrase)
    client.auth_publickey(username, key)

    # Abrir un canal SFTP
    sftp = client.open_sftp()

    # Ahora puedes usar 'sftp' para realizar operaciones SFTP, por ejemplo:
    # sftp.put('archivo_local.txt', 'archivo_remoto.txt')
    # sftp.get('archivo_remoto.txt', 'archivo_local.txt')

    # Cierra la conexión SFTP
    sftp.close()

    # Cierra la conexión SSH
    client.close()

if __name__ == '__main__':
    sftp_test_conection()
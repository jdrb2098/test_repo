import json
import os
import re
from datetime import datetime
from random import randrange

from boto3 import client, resource
from botocore.exceptions import ClientError
from mabe.services.config import *
from mabe.services.logs import getLogger
from mabe.services.obtenerFactura import obtener_factura, obtener_factura_multiples, sftp_connection
from mabe.services.tabla import Orden, Tabla
from requests import get

SQS = client("sqs")
connection = None
LOG = getLogger()


def webhooks(event, context):

    parameters = {
        1086590: token_pe,
        1086588: token_co,
    }

    # Get feed from Yuju webhook
    feed: str = event['headers'].get("location", None)
    if not feed:
        feed: str = event['headers'].get("Location", None)

    # Get event from Yuju webhook
    action_type: str = event['headers'].get("X-Madkting-event", None)
    if not action_type:
        action_type: str = event['headers'].get("x-madkting-event", None)

    if feed and "order" in action_type:

        shop_pk = int(re.findall(r'\d+', feed)[0])

        response_order = get(
            url=feed,
            headers={
                "Authorization": f"Token {parameters[shop_pk]}"
            }
        )
        order_json = response_order.json()

        delay = randrange(60) * 2
        try:
            response = SQS.send_message(
                QueueUrl=os.getenv("SQS_MAIN_URL"),
                MessageBody=json.dumps(order_json),
                DelaySeconds=delay,
            )
        except ClientError as error:
            LOG.exception("Send message failed: %s",
                          json.dumps(order_json["pk"]))
            raise error

        return respond(
            data={"message": "Message accepted!"},
            status=response["ResponseMetadata"]["HTTPStatusCode"],
        )


def get_invoice(event, context):
    global connection
    if not connection:
        connection = connect()

    for record in event["Records"]:
        orden = json.loads(record["body"])
        receipt_handle = record["receiptHandle"]
        reference = orden.get("reference")
        tabla_factura = Tabla(connection)
        result = tabla_factura.buscar_factura(reference)
        if not result:
            obtener_factura(orden, connection, SQS, receipt_handle)
        else:
            try:
                SQS.delete_message(
                    QueueUrl=os.getenv("SQS_MAIN_URL"), ReceiptHandle=receipt_handle
                )
                LOG.info("message copy deleted")
            except ClientError as error:
                LOG.exception("Couldn't delete message: %s", receipt_handle)
                raise error


def get_invoice_missing(event, context):

    global connection
    if not connection:
        connection = connect()

    tabla_ordenes = Orden(connection)
    lista_ordens = tabla_ordenes.ordenes()
    lista_ordens_validas = []

    for order in lista_ordens:
        tiempo_de_creada = datetime.now() - datetime.strptime(order["created_at"], '%Y-%m-%dT%H:%M:%S')
        if tiempo_de_creada.days > 3 :
            tabla_ordenes.eliminar_orden(str(order["reference"]))
        else:
            reference = order.get("reference")
            tabla_factura = Tabla(connection)
            result = tabla_factura.buscar_factura(reference)
            if not result:
                lista_ordens_validas.append(order)

    obtener_factura_multiples(lista_ordens_validas, event["shop_pk"], connection, SQS, None)


def test(event, context):

    parameters = {
        1086590: (
            username_pe,
            password_pe,
            private_key_pe,
            "96E5ED2C3D405028", #TODO Delete
            "Peru",
            token_pe,
        ),
        1086588: (
            username_co,
            password_co,
            private_key_co,
            "3853D5A65ECD6028",
            "Colombia",
            token_co,
        ),
    }

    sftp = sftp_connection(1086588)

    if sftp:
        folder = parameters[1086588][4]
        sftp.chdir(f"/Sudamerica/{folder}/Integra/ML/Docu")
        files = sftp.listdir_attr()
        files = tuple(
            filter(
                lambda file: (file.filename.split(".")[1] == "xml"),
                files,
            )
        )

    return [ file.filename.split(".")[0] for file in files]



def connect():
    return resource("dynamodb")


def respond(data, status):
    return {"statusCode": status, "body": json.dumps(data)}


if __name__ == '__main__':

    test(None, None)
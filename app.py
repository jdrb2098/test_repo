from qar.services.product import get_products, process_action
from qar.services.feeds import get_feed
from qar.utils import connect
from qar.services.table import ProductTable, OrderTable
import json
from qar.variables import (
    sqs_get_product,
    SQS,
    LOG,
    cloudwatch_events,
    marketplaces,
    sqs_get_order,
    productTable,
    orderTable,
)
from qar.services.orders import get_order, process_order
from boto3 import client
import os

connection = None
invoke_lambda = client("lambda")


def webhooks(event, context):
    evento = event["headers"].get("X-Madkting-event")
    location = event["headers"].get("location")

    if not location or not evento:
        return {"statusCode": 400}

    data = {"location": location}
    evento = evento.split(":")[1]

    if evento == "order":
        marketplace_pk = location.split("marketplace/")[1].split("/")[0]
        if int(marketplace_pk) not in marketplaces:
            return {"statusCode": 200}

        response = SQS.send_message(
            QueueUrl=sqs_get_order, MessageBody=json.dumps(data)
        )
    else:
        response = invoke_lambda.invoke(
            FunctionName=os.getenv("FEEDS"),
            InvocationType="Event",
            Payload=json.dumps(data),
        )
    return {"statusCode": response["ResponseMetadata"]["HTTPStatusCode"]}


def feeds(event, _):
    global connection
    if not connection:
        connection = connect()

    location = event.get("location")
    get_feed(location, connection)


def orders(event, _):
    global connection
    if not connection:
        connection = connect()

    order_table = OrderTable(connection, orderTable)
    for record in event["Records"]:
        message = json.loads(record["body"])
        location = message.get("location")
        get_order(location, order_table)


def send_order(event, _):
    global connection
    if not connection:
        connection = connect()

    for record in event["Records"]:
        order = json.loads(record["body"])
        process_order(order, connection)


def products(event, _):
    global connection
    if not connection:
        connection = connect()

    action = event.get("event")
    get_products(action, connection)


def process_product(event, _):
    global connection
    if not connection:
        connection = connect()

    resp = SQS.receive_message(
        QueueUrl=sqs_get_product,
        AttributeNames=["All"],
        MaxNumberOfMessages=1,
    )

    msg = resp.get("Messages")
    if msg:
        for msg in resp["Messages"]:
            receipt_handle = msg["ReceiptHandle"]
            body = json.loads(msg["Body"])
            SQS.delete_message(QueueUrl=sqs_get_product, ReceiptHandle=receipt_handle)
            LOG.info("Message deleted")
            process_action(body, connection)

    else:
        LOG.info("Timer desactivated")
        cloudwatch_events.disable_rule(Name="SqsSendProduct")


def retry(event, _):
    token = event["headers"].get("token")
    if token != os.environ["RETRY_TOKEN"]:
        return respond(data={"message": "Invalid token."}, status=401)

    body = json.loads(event["body"])
    shop_pk = body.get("id_shop")
    marketplace_pk = body.get("id_channel")
    order_pk = body.get("id_order")
    if not shop_pk or not marketplace_pk or not order_pk:
        return respond(data={"message": "Bad request."}, status=400)

    location = "https://api.software.madkting.com/shops/{}/marketplace/{}/orders/{}"
    location = location.format(shop_pk, marketplace_pk, order_pk)
    global connection
    if not connection:
        connection = connect()
    order_table = OrderTable(connection, orderTable)
    get_order(location, order_table, True)

    return respond(data={"message": "Processed successfully."}, status=201)


def respond(data, status):
    return {"statusCode": status, "body": json.dumps(data)}


def query(event, _):
    global connection
    if not connection:
        connection = connect()

    option = event["option"]
    if option == "product_by_shop":
        shop = event["shop"]
        product_table = ProductTable(connection, productTable)
        response = product_table.query_shop(shop)
        LOG.info(response)

    elif option == "find_product":
        sku = event["sku"]
        product_table = ProductTable(connection, productTable)
        response = product_table.find_data(sku)
        LOG.info(response)

    elif option == "get_product_from_yuju":
        vtex_product = event["product_list"]
        skuId_list = event["skuId_list"]
        from requests import get
        from requests.exceptions import HTTPError
        from qar.configs import yuju_headers, SHOP_PK
        from qar.variables import product_url
        from datetime import datetime

        connection = connect()
        product_table = ProductTable(connection, productTable)
        total = 0
        page_size = 100
        page = 1
        count_vtex = 0
        count_erp = 0
        while page:
            payload = [("page", page), ("page_size", page_size)]
            try:
                response = get(
                    product_url.format(SHOP_PK),
                    headers=yuju_headers,
                    params=payload,
                )
                response.raise_for_status()
            except HTTPError as e:
                LOG.exception(e.response.text)
            else:
                LOG.info("[{}] {}".format(page, response.status_code))
                products = response.json()
                for product in products:
                    item = {
                        "id": product["sku"],
                        "pk": product["pk"],
                        "price": str(product["price"]),
                        "stock": product["stock"],
                        "created_at": datetime.utcnow().isoformat(),
                        "status": "success",
                    }
                    try:
                        pos = vtex_product.index(product["sku"])
                        item["skuId"] = skuId_list[pos]
                        item["shop"] = "vtex"
                        count_vtex += 1
                    except ValueError:
                        item["shop"] = "erp"
                        count_erp += 1
                    product_table.insert_data(item)
                size = len(products)
                total += size
                if size < page_size:
                    LOG.info(size)
                    break

            page += 1

        LOG.info(total)
        LOG.info(f"total erp: {count_erp}")
        LOG.info(f"total vtex: {count_vtex}")




if __name__ == '__main__':
    event = {"Records": [{
        "body": """{
               "location": "https://api.software.madkting.com/shops/1087841/marketplace/13/orders/6777870536462/"
           }""",
        "receiptHandle": """"""
    }]}
    orders(event, None)

# if __name__ == '__main__':
#    products({"event": "create_product_erp"}, None)

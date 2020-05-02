import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('bill_of_rights')

# good reference:
# https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GettingStarted.Python.03.html


class DecimalEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if abs(o) % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


def lambda_handler(event, context):
    ct = 1

    f = open("sections.txt", "r")
    f_lines = f.readlines()

    for f in f_lines:
        response = table.put_item(
            Item={
                'section': str(ct),
                'text': f
            }
        )
        ct = ct + 1

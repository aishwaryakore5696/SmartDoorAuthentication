import json
from datetime import datetime,timedelta
#from __future__ import print_function # Python 2/3 compatibility
import boto3
import decimal
import math, random
def generateOTP() :  
    digits = "0123456789"
    OTP = ""
    for i in range(6) : 
        OTP += digits[math.floor(random.random() * 10)] 
    return int(OTP) 
def send_sns_message(message,VISITOR_PHONE_NUMBER):
    
    try:
        client = boto3.client('sns', 'us-east-1')
        response = client.publish(
            Message=message,
            MessageStructure='string',
            PhoneNumber=str(VISITOR_PHONE_NUMBER)
        )
        print(response)
        return True
    except Exception as e:
        print('The function failed while sending SNS message to the owner '
              'with the error ' , str(e))
def lambda_handler(event, context):
    try:
        print("******************")
        print("hi")
        name = event['name']
        phno=event['phno']
        phno=int(phno)
        faceid=event['faceid']
        faceid=str(faceid)
        VISITOR_PHONE_NUMBER = "+1"+str(phno)
        print("visitors ph no"+VISITOR_PHONE_NUMBER)
        photo=[{"objectKey": "my-photo.jpg","bucket": "my-photo-bucket","createdTimestamp": "2018-11-05T12:40:02"}]#event['photo']
        dateTimeObj = datetime.now()+ timedelta(minutes=5)
        otp=generateOTP()
        print(otp)
        WEBPAGE_URL="https://smartdoorauthenticationsystem2.s3.amazonaws.com/WP2.html?faceid="+faceid
        print("current datetime is:",dateTimeObj)
        expirytimestamp=1586667900
        print("name = ", name)
        print("phno =",phno)
        print("faceid =",faceid)

        dynamodb = boto3.resource('dynamodb')#, region_name='us-east-2', endpoint_url="http://localhost:8000")
        table1=dynamodb.Table('DB1')
        table = dynamodb.Table('DB2')
        #expirytimestamp = dateTimeObj.strftime('%s')
        expirytimestamp =int((dateTimeObj-datetime(1970,1,1)).total_seconds())
        #expirytimestamp = int(dateTimeObj.timestamp())
        print(type(expirytimestamp))
        print("TTL expirytimetimestamp:", expirytimestamp)
        print("phno after:",type(phno))
        response = table.put_item(
         Item={
            'faceid': faceid,
            'name': name,
            'phno':phno,
            'photo':photo

            }
        )
       
        #  Code To Update an item in dynamodb
#         response = table.update_item(
#     Key={
#         'year': year,
#         'title': title
#     },
#     UpdateExpression="set info.rating = :r, info.plot=:p, info.actors=:a",
#     ExpressionAttributeValues={
#         ':r': decimal.Decimal(5.5),
#         ':p': "Everything happens all at once.",
#         ':a': ["Larry", "Moe", "Curly"]
#     },
#     ReturnValues="UPDATED_NEW"
# )

        print("PutItem succeeded in DB2:",response)
        print("phno after:",type(phno))
        response1 = table1.put_item(
            Item={
                'phno':phno,
                'otp':otp,
                'expirytimestamp':expirytimestamp
            }
        )
        print("PutItem succeeded in DB1:",response1)
        print("next module")       
        message = "You are permited by the owner.Please enter your phno and otp in the link below "+WEBPAGE_URL+"  OTP:"+str(otp)
        print("sending sms now"+message)
        sns_result = send_sns_message(message,VISITOR_PHONE_NUMBER)
        if sns_result:
            print('A message has been sent to the visitor for verification')
            return {
                'statusCode': 200,
                'body': phno,
                'name':name
            }
        else:
            print("sms not send")
        return {
         'statusCode': 200,
         'body': phno,
         'name':name
        }
        
    except Exception as e:
        print(" The execution of the function failed due to error" , str(e))
        return {
            'statusCode': 400,
            'body': json.dumps(str(e))
        }


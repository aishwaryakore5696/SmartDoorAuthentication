import json
import boto3

def lambda_handler(event, context):
    try:
        print("******************")
        print("hi")
        phno = event['phno']
        otp=event['otp']
        faceid=event['faceid']
        print(type(otp))
        print("phno = ", phno)
        print("otp =",otp)
        print(faceid)
        client = boto3.client('dynamodb')

        #pno = "123456789"
        response = client.get_item(TableName='DB1', Key={'phno':{'N':phno}})
        print("Response",response)
        l=response['Item']["otp"]["N"]
        phno=response['Item']["phno"]["N"]
        print(phno)
        print(type(l),type(otp))
        print(l)
        print(otp)
        print(type(phno))
        print(l==otp)
        if (l==otp):
            faceid=str(faceid)
            #phno=str(phno)
            response = client.get_item(TableName='DB2', Key={'faceid':{'S':faceid}})
            #response = client.get_item(TableName='DB2', Key={'phno':{'N':phno}})
            print("Response",response)
            name=response['Item']["name"]["S"]
            print(name)
            return {
             'statusCode': 200,
             'body': "success",
             'name':name
            }
        else:
            return {
             'statusCode': 200,
             'body': "failed"
            }
    except Exception as e:
        print(" The execution of the function failed due to error" , str(e))
        return {
            'statusCode': 400,
            'body': json.dumps(str(e))
        }

import base64
import boto3
import os
import sys
import cv2
import math
import random
import json
from datetime import datetime,timedelta


BUCKET_NAME = 'smartdoorauthenticationsystem2'
TEMP_COLLECTION_NAME = "temp"
TABLE_NAME = 'DB2'
OWNER_WEBPAGE_URL = "https://smartdoorauthenticationsystem2.s3.amazonaws.com/WP1.html"
OWNER_PHONE_NUMBER = "+13477751608"
VISITOR_WEBPAGE_URL = "https://smartdoorauthenticationsystem2.s3.amazonaws.com/WP2.html"
ARN = "arn:aws:sns:us-east-1:775506362118:chatbotassignment_sns"


def generate_otp() :
    digits = "0123456789"
    otp = ""
    for i in range(6) :
        otp += digits[math.floor(random.random() * 10)]
    return int(otp)


def insert_entry_in_dynamo_db(table_name, insert_json):
    try:
        dynamodb = boto3.resource('dynamodb',aws_access_key_id='AKIAXA2AJIH64LD6JL5V',
                                 aws_secret_access_key='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')
        table = dynamodb.Table(table_name)
        response = table.put_item(
            Item={
                'faceid': insert_json['faceid'],
                'name': insert_json['name'],
                'phno': insert_json['phno'],
                'photo': insert_json['photo'],
                # "status": insert_json['status']
            }
        )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print("Insert in Dynamo DB table "+ table_name +" was successful")
            return True
    except Exception as e:
        print(" The execution of the function failed due to error", str(e))
        return True



def detect_new_image(local_file_path, path_output_dir,fragment_name):
   try:
        # Create client and put images to S3
        kvs_archive_client = boto3.client('kinesis-video-archived-media',
                                          'us-east-1',
                                          aws_access_key_id='AKIAXA2AJIH64LD6JL5V',
                                          aws_secret_access_key='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',
                                          endpoint_url='https://b-604520a7.kinesisvideo.us-east-1.amazonaws.com')

        response = kvs_archive_client.get_media_for_fragment_list(StreamName='KVS1',
                                                                  Fragments=[
                                                                      fragment_name])
        frame = response['Payload'].read()
        print('frame is'  , frame)
         # = 'C:/Users/tejas/Desktop/cloud-ouptput/stream.mkv'
        # for lambda = /tmp/stream.mkv
        with open(local_file_path, 'wb') as f:
            f.write(frame)
            vidcap = cv2.VideoCapture(local_file_path)
        print('Cap', type(vidcap))
        print(sys.getsizeof(vidcap))

         # = 'C:/Users/tejas/Desktop/cloud-ouptput/'
        count = 0
        while vidcap.isOpened():
            print('Opened Video Capture')
            success, image = vidcap.read()
            # print("image" , image)
            # print("success" , success)
            if success:
                print('Image in process of writing')
                cv2.imwrite(path_output_dir +".png", image)
                count += 1
                print('Image Written')
                print(os.path.join(path_output_dir, '%d.png')  %count)
                print('The path is ' , path_output_dir, count )
            else:
                break
        # cv2.destroyAllWindows()
        vidcap.release()
        print('Video capture released')
        # # Upload file to S3
        # s3 = boto3.client('s3', aws_access_key_id='AKIAXA2AJIH64LD6JL5V',
        #                   aws_secret_access_key='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')
        # print('The count is ' , count)
        # s3.upload_file( '/tmp/output-image.png', BUCKET_NAME,
        #                'recognized-faces/stream' + fragment_name + '.png')
        # # make an entry in Dynamo DB
        return True
   except Exception as e:
       print("Exception occurred in detect_new_image " , str(e))
       return False


def add_collection(image_file_path,s3_file_path ="/tmp/rekognition"):
    try:
        rekognition_client = boto3.client('rekognition',
                                          aws_access_key_id='AKIAXA2AJIH64LD6JL5V',
                                          aws_secret_access_key='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')

        s3 = boto3.client('s3', aws_access_key_id='AKIAXA2AJIH64LD6JL5V',
                          aws_secret_access_key='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')

        # path_output_dir + str(count - 1) + '.png'
        # 'stream' + fragment_name + '.png'
        s3.upload_file(image_file_path, BUCKET_NAME, s3_file_path + "img.png")
        with open(image_file_path, 'rb') as \
                image_file_ptr:
            image_bytes = image_file_ptr.read()
        # image_json = {'Bytes': base64.b64encode(image_bytes)}
        print("Uploaded image to temporary S3 location")

        image_json = {'S3Object': {'Bucket': BUCKET_NAME,'Name': s3_file_path +"img.png"}}

        index_response = rekognition_client.index_faces(CollectionId=
                                                        TEMP_COLLECTION_NAME,
                                                        Image=image_json)
        print('The index response is ' , index_response)
        face_id = index_response['FaceRecords'][0]['Face']['FaceId']
        print("The face id is " , face_id)
        search_face_response = rekognition_client.search_faces(CollectionId=
                                                               TEMP_COLLECTION_NAME,
                                                               FaceId=face_id,
                                                               MaxFaces=1,
                                                               FaceMatchThreshold=90)
        return search_face_response, face_id

    except Exception as e:
        print(" The function failed while adding new faces to the collection with exception " , e)
        return False


def upload_file_to_s3( local_file_path, s3_file_path):
    try:
        # Upload file to S3
        s3 = boto3.client('s3', aws_access_key_id='AKIAXA2AJIH64LD6JL5V',
                          aws_secret_access_key='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')

        # path_output_dir + str(count - 1) + '.png'
        # 'stream' + fragment_name + '.png'
        s3.upload_file(local_file_path, BUCKET_NAME, s3_file_path)
        return True
    except Exception as e:
        print("An error occurred while uploading files to S3 with exception " , e)
        return False


def send_sns_message(message,phone_number = OWNER_PHONE_NUMBER):
    try:
        client = boto3.client('sns', 'us-east-1',
                              aws_access_key_id = 'AKIAXA2AJIH64LD6JL5V',
                              aws_secret_access_key = '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')

        response = client.publish(
            Message=message,
            MessageStructure='string',
            PhoneNumber=str(phone_number)

        )
        print(response)
        return True
    except Exception as e:
        print('The function failed while sending SNS message to the owner '
              'with the error ' , str(e))


def get_details_from_dynamo_db(table_name,face_id):
    try:
        dynamo_db_client = boto3.client('dynamodb')
        response = dynamo_db_client.get_item(TableName=table_name, Key={"faceid":
                                                                            {
                                                                                "S":face_id}})
        name = response['Item']['name']['S']
        phno = response['Item']['phno']['S']
        return_json = {'name': name,
                       'phno' : phno
                       }
        return return_json
    except Exception as e:
        print("An exception occurred while getting user details from Dynamo DB", str(e))
        return False


def insert_entry_in_dynamo_db1(table_name, insert_json):
    try:
        dynamodb = boto3.resource('dynamodb',aws_access_key_id='AKIAXA2AJIH64LD6JL5V',
                                 aws_secret_access_key='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')
        table = dynamodb.Table(table_name)
        response = table.put_item(
            Item={
                'otp': insert_json['otp'],
                'phno': insert_json['phno'],
                'expirytimestamp': insert_json['expirytimestamp'],
                # "status": insert_json['status']
            }
        )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print("Insert in Dynamo DB table "+ table_name +" was successful")
            return True
    except Exception as e:
        print(" The execution of the function failed due to error", str(e))
        return True

def lambda_handler(event,context):
    try:

        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@2")
        print('Event' , event)
        decoded_data = base64.b64decode(event['Records'][0]['kinesis']['data']).decode()
        print("##########################################")
        print("Decoded payload: " , str(decoded_data))
        print(type(decoded_data))
        decoded_data = json.loads(decoded_data)
        ## code to get the frame no from the payload
        path_output_dir = '/tmp/output-img'
        if (len(decoded_data['FaceSearchResponse'])) == 0:
            return  True
        if len(decoded_data['FaceSearchResponse']) !=0 and len(decoded_data[
                                                                   'FaceSearchResponse'][0]['MatchedFaces']) == 0:
            fragment_name = decoded_data['InputInformation']['KinesisVideo']['FragmentNumber']
            win_output_path = 'C:/Users/tejas/Desktop/cloud-ouptput/'
            new_image_result = detect_new_image(
                local_file_path='/tmp/stream.webm',
                path_output_dir='/tmp/output-img',
                fragment_name=fragment_name)
            if new_image_result:
                print("New Image Detected and Written in local path")
            # Add a face to a temp collection if we get matching faces

            add_image_result,face_id = add_collection(image_file_path='/tmp/output-img.png')
            if not add_image_result:
                raise ("Failed while adding new image to the collection")

            if len(add_image_result['FaceMatches']) == 0:
                # No matches in the temp collection, make an entry in Dynamo DB
                # as PENDING for this face_id  and send an SNS to the Owner

                s3_path = 'https://'+BUCKET_NAME+".s3.amazonaws.com/" + 'recognized-faces/' + fragment_name + ".png"
                insert_json = {'faceid': face_id,
                               'name': None,
                               'phno': None,
                               'photo': s3_path,
                               'status': 'PENDING'}

                insert_result = insert_entry_in_dynamo_db(table_name=TABLE_NAME,
                                                          insert_json=insert_json)

                if insert_result:
                    print("Inserted record in Dynamo DB")
                    s3_file_path = 'recognized-faces/' + fragment_name + ".png"
                    upload_file_to_s3_res = upload_file_to_s3(path_output_dir + ".png", s3_file_path)

                    if upload_file_to_s3_res:
                        print("File uploaded to S3")

                    # Delete file from collection
                    # rekognition_client = boto3.client('rekognition',
                    #                                   aws_access_key_id='AKIAXA2AJIH64LD6JL5V',
                    #                                   aws_secret_access_key='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')
                    # deleted_image_response = rekognition_client.delete_faces(
                    #     CollectionId=TEMP_COLLECTION_NAME,
                    #     FaceIds=[
                    #         face_id,
                    #     ]
                    # )
                    # if len(deleted_image_response['DeletedFaces']) > 0:
                    #     print("Deleted face from collection ")

                    # Constructing the message to be sent to the OWNER

                    message = "A new person has been detected at your entrance.\n To " \
                              "allow this person, please click on the url below " \
                              "and provide details.\n  The person would be  granted " \
                              "access via an OTP. \n A link to the person's image " \
                              "captured is also included below\n" \
                              "URL: " + OWNER_WEBPAGE_URL + "\n" \
                              "Photo Link: " + s3_path
                    sns_result = send_sns_message(message)
                    if sns_result:
                        print('A message has been sent to the owner for '
                              'verification')

                        return {"status": "SUCCESS",
                                "status_code": 200}
            else:
                print("Current image is of an unknown visitor but has been "
                      "detected earlier. So no processing "
                      "would be done ")
                return {"status": "SUCCESS",
                        "status_code": 200}

        elif len(decoded_data['FaceSearchResponse']) != 0 and len(decoded_data[
                                                                      'FaceSearchResponse'][
                                                                      0][
                                                                      'MatchedFaces']) > 0:

            print("The current image is of a person who is a part of the "
                  "collection\n Getting visitor details ")

            visitor_face_id = decoded_data['FaceSearchResponse'][0][
                "MatchedFaces"][0]['Face']['FaceId']

            visitor_details_response = get_details_from_dynamo_db(table_name=
                                                                  'DB2',
                                                                  face_id=visitor_face_id)
            if not visitor_details_response:
                raise (
                    "Exception occurred while getting Visitor Details from Dynamo DB")
            else:
                vistor_name = visitor_details_response['name']
                visitor_phno = visitor_details_response['phno']

                # Generate OTP for the visitor
                otp = generate_otp()
                dateTimeObj = datetime.now() + timedelta(minutes=5)
                expirytimestamp = int(
                    (dateTimeObj - datetime(1970, 1, 1)).total_seconds())
                insert_json_otp = \
                    {'phno': visitor_phno,
                     'otp': otp,
                     'expirytimestamp': expirytimestamp
                     }
                insert_otp_result = insert_entry_in_dynamo_db1(table_name='DB1',
                                                               insert_json=insert_json_otp)
                if insert_otp_result:
                    print(
                        "OTP " + str(otp) + " generated in Dynamo DB. Proceeding to send message to the visitor ")
                    message = "Hi " + vistor_name + "\n" \
                              "Please enter the otp" + str(otp) + " by clicking on the URL below\n" \
                               "URL: " + VISITOR_WEBPAGE_URL
                    sns_result = send_sns_message(message,phone_number=visitor_phno)
                    if sns_result:
                        print(
                            "SNS sent to Visitor. Execution of Lambda function completed ")
                    return {"status": "SUCCESS",
                            "status_code": 200}
    except Exception as e:
        print("Lambda handler failed with the exception" , str(e))
        return {"status": "FAILED",
                "status_code": 200}

# if __name__ == "__main__":
#     response = lambda_handler(event='Test', context=None)







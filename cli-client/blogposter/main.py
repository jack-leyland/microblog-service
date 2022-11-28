import json
import sys, os, base64, datetime, hashlib, hmac, argparse, getpass
import requests, keyring

def create_cli_parser():
    parser = argparse.ArgumentParser(
                    prog = 'Microblog CLI Interface',
                    description = 'Simple tool to make posts to the microblog on my website.',
                    )
    parser.add_argument('-p','--post', help="Body of post to send to the microblog. Limit 500 characters.")
    parser.add_argument('-r','--reset_creds', action='store_true', default=False, help="Reset stored AWS credentials.")
    parser.add_argument('-e','--reset_endpoint', action='store_true', default=False, help="Reset API gateway endpoint.")
    return parser

def get_input():
    while True:
        post = input("Enter post (500 char. max): ")
        if len(post) > 500:
            print("Posts cannot exceed 500 characters.")
        else:
            break
    return post

# This is a little bit of a stretch of keyring's intended purpose but seems to be a quick and 
# easy way to securely store these keys. 
def get_aws_credentials(should_prompt=False):
    access_key = keyring.get_password('aws_microblog', "access_key")
    secret_key = keyring.get_password('aws_microblog', "secret_key")
    
    if not access_key or not secret_key or should_prompt:
        access_key = input("Enter AWS Access Key: ")
        secret_key = getpass.getpass(prompt='Enter AWS Secret Access key: ', stream=None)
        keyring.set_password('aws_microblog', "access_key", access_key)
        keyring.set_password('aws_microblog', "secret_key", secret_key)
    
    return access_key, secret_key

def get_endpoint(should_prompt=False):
    endpoint = keyring.get_password("aws_microblog", "endpoint")

    if not endpoint or should_prompt:
        endpoint = input("Enter posts endpoint: ")
        keyring.set_password("aws_microblog", "endpoint", endpoint)

    return endpoint 


def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def getSignatureKey(key, dateStamp, regionName, serviceName):
    kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning

def prepare_headers(access_key, secret_key, payload):
    method = 'POST'
    service = 'execute-api'
    host = '8gir80nrkh.execute-api.us-east-1.amazonaws.com'
    region = 'us-east-1'
    content_type = 'application/json'
    

    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')

    canonical_uri = '/posts'
    canonical_querystring = ''
    canonical_headers = 'content-type:' + content_type + '\n' + 'host:' + host + '\n' + 'x-amz-date:' + amz_date + '\n'
    signed_headers = 'content-type;host;x-amz-date'
    payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = date_stamp + '/' + region + '/' + service + '/' + 'aws4_request'
    string_to_sign = algorithm + '\n' +  amz_date + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
    signing_key = getSignatureKey(secret_key, date_stamp, region, service)
    signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()
    authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature

    headers = {'Content-Type':content_type,
           'X-Amz-Date':amz_date,
           'Authorization':authorization_header}
    return headers


def main():
    parser = create_cli_parser()
    args = parser.parse_args()

    if not args.post:
        post = get_input()
    else :
        if len(args.post) > 500:
            print("Posts cannot exceed 500 characters.")
            sys.exit(0)
        post = args.post

    access_key, secret_key = get_aws_credentials(args.reset_creds)
    endpoint = get_endpoint(args.reset_endpoint)
    payload = json.dumps({"post": post})
    request_headers = prepare_headers(access_key,secret_key, payload)


    res = requests.post(endpoint, data=payload, headers=request_headers)

    print(res.status_code)
    print(res.text)






if __name__ == "__main__":
    main()
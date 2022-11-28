import {DynamoDBClient, PutItemCommand} from "@aws-sdk/client-dynamodb";
import {v4 as uuidv4} from 'uuid'

const ddb = new DynamoDBClient({region: 'us-east-1'})

export const handler = async (event) => {
    let req = JSON.parse(event.body)
    let resBody;
    let postId = uuidv4()
    let params = {
      TableName: "microblog-posts",
      Item: {
        postId: {S: postId},
        added_on: {S: new Date().toISOString()},
        post: {S: req.post},
      }
    }
    return new Promise((resolve, reject) => {
      ddb.send(new PutItemCommand(params)).then((data) => {
        resBody = `Post success. PostId: ${postId}`
        resolve(formatResponse(resBody))
      }).catch((err) => {
        reject(formatError(err, 500))
      })
    })

}

const formatResponse = (body) => {
  let response = {
    "statusCode": 200,
    "headers": {
      "Content-Type": "text/plain"
    },
    "isBase64Encoded": false,
    "body": body,
  }
  return response
}

const formatError = (message, statusCode) => {
  let response = {
    "statusCode": statusCode,
    "headers": {
      "Content-Type": "application/json",
    },
    "isBase64Encoded": false,
    "body": message
  }
  return response
}
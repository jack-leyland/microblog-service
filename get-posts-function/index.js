import {DynamoDBClient, QueryCommand} from "@aws-sdk/client-dynamodb";

const ddb = new DynamoDBClient({region: 'us-east-1'})

export const handler = (event) => {
    const queryParams = {
        TableName: "microblog-posts",
        IndexName : "status-added_on-index",
        KeyConditionExpression:"#S = :status",
        ExpressionAttributeNames: {
          "#S":"status"
        },
        ExpressionAttributeValues: {
        ":status": {S:"OK"}
        },
        Limit: parseInt(event.queryStringParameters.pageSize),
        ScanIndexForward: true,
    }
    if (event.queryStringParameters.last) {
      let postId = event.queryStringParameters.id;
      let added_on = event.queryStringParameters.added_on;
      queryParams["ExclusiveStartKey"] = {
          "postId": {S: postId},
          "status": {S: "OK"},
          "added_on": {N: added_on}
      }
    }

    return new Promise((resolve, reject) => {
        ddb.send(new QueryCommand(queryParams)).then((data) => {
            delete data['$metadata']
            let items = [];
            data["Items"].forEach((item) => {
              items.push({
              "postId": item["postId"]["S"],
              "post": item["post"]["S"],
              "added_on": item["added_on"]["N"]
              })
            })
            data["Items"] = items
            if (data.LastEvaluatedKey) {
              data["LastEvaluatedKey"] = {
                "postId": data["LastEvaluatedKey"]["postId"]["S"],
                "added_on": data["LastEvaluatedKey"]["added_on"]["N"]
              }
            }
            resolve(formatResponse(JSON.stringify(data)))
        }).catch((err) => {
            reject(new Error(err))
        })
    })
}


const formatResponse = (body) => {
    let response = {
      "statusCode": 200,
      "headers": {
        "Content-Type": "application/json"
      },
      "isBase64Encoded": false,
      "body": body,
    }
    return response
  }
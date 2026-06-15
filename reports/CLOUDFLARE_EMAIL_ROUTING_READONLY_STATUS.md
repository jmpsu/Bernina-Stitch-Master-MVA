# Cloudflare Email Routing Read-Only Status

Account ID: fba49043e9bc496c1149d7452624ec96
Zone ID: 64bf2d594c7face850c6841b8fbb488c
Domain: jupiterembroideryco.com
Intake email: orders@jupiterembroideryco.com


## token_verify

HTTP_STATUS: 200

RAW_RESPONSE:
{"result":{"id":"f28355f5fb6d16c8095c1299d4b54be4","status":"active","expires_on":"2028-06-30T23:59:59Z"},"success":true,"errors":[],"messages":[{"code":10000,"message":"This API Token is valid and active","type":null}]}

## email_settings

HTTP_STATUS: 404

RAW_RESPONSE:
404 page not found


## email_addresses

HTTP_STATUS: 200

RAW_RESPONSE:
{"result":[{"id":"9b7783017e274b65bc654299ba2caf32","tag":"9b7783017e274b65bc654299ba2caf32","email":"jupiterembroideryco@gmail.com","verified":"2026-04-20T10:00:22.413694Z","created":"2026-04-20T10:00:22.413694Z","modified":"2026-04-20T10:00:22.413694Z","status":"verified"}],"success":true,"errors":[],"messages":[],"result_info":{"page":1,"per_page":20,"count":1,"total_count":1}}

## email_rules

HTTP_STATUS: 200

RAW_RESPONSE:
{"result":[{"id":"ee987316344d40638e20d43ed71b1e97","tag":"ee987316344d40638e20d43ed71b1e97","name":"","matchers":[{"type":"literal","field":"to","value":"info@jupiterembroideryco.com"}],"actions":[{"type":"forward","value":["jupiterembroideryco@gmail.com"]}],"enabled":true,"priority":0},{"id":"db0a8fe9bb714a2fad01074b2b0f54c6","tag":"db0a8fe9bb714a2fad01074b2b0f54c6","name":"","matchers":[{"type":"all"}],"actions":[{"type":"drop"}],"enabled":true,"priority":2147483647}],"success":true,"errors":[],"messages":[],"result_info":{"page":1,"per_page":20,"count":2,"total_count":2}}

No DNS or production settings were changed.

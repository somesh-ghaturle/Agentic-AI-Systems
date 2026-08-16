# The Azure Functions v2 binding. Deliberately thin.
#
# All logic lives in handler.py so it can be imported and tested without azure-functions
# installed and without a host. This file is the only part that cannot be unit-tested, so
# there is as little of it as possible.
#
# The file MUST be named function_app.py at the package root — the v2 model discovers the
# app object by that name, and a package missing it deploys successfully and then serves
# 404 on every route.

import azure.functions as func
import handler
from azure_http import json_response, request_json

app = func.FunctionApp()


# AuthLevel.ANONYMOUS is correct here and is not the same as unauthenticated. Easy Auth
# (auth_settings_v2, require_authentication = true) rejects unauthorized callers before the
# host routes the request, so a function key would be a second, weaker credential guarding
# something Entra already guards — and one that lives in app settings where it can leak.
@app.route(route="approval_validator", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def approval_validator(req: func.HttpRequest) -> func.HttpResponse:
    body, status = handler.run(request_json(req))
    return json_response(body, status=status)

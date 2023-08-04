import requests
import pandas as pd

# For REST API call testing
two_w_key = 'NRAK-S5J3BFK03G750PSM5ZTLPA3FJEJ'
bm_key = 'NRAK-YKT775HSEQE34I9S5QYOYCUBRI7'

policies_url = 'https://api.newrelic.com/v2/alerts_policies.json'
policies_headers = {
    "X-Api-Key": bm_key
}

policies_response = requests.get(policies_url, headers=policies_headers)
print(policies_response.json())

policies_df = pd.DataFrame(columns=['Client', 'Condition Type', 'Condition Name', 'Query',
                                    'Description', 'Condition ID', 'Policy ID'])

for policy in policies_response.json()['policies']:
    if 'Standard' in policy['name']:
        policies_list.append(policy['id'])

print(policies_list)

# policy_id = 0
#
# condition_url = 'https://infra-api.newrelic.com/v2/alerts/conditions'
# condition_headers = {
#     "Api-Key": bm_key
# }
# params = {
#     "policy_id": policy_id
# }
#
# response = requests.get(condition_url, headers=condition_headers)
#
# print(response.json())
#
# for data in response.json()['data']:
#     print(data)

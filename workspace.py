

import requests
import re
from utils import env , HEADERS
import utils


# core of the linkedin bot 
class WorkSpace:
    def __init__(self):
        pass

    def upload_media(self,files):
        # not to be used
        # Uploads one or multiple image files to LinkedIn and 
        # returns the corresponding upload ID (single or multi-photo collection).


        if type(files) != list:
            files = [files]

        # if one file then one upload id
        # if multi files, i send another request and i get a multi_file id
        upload_id = ""

        upload_ids = []

        for file in files:
            file_data = ""
            with open(file,"rb") as f:
                file_data = f.read()
            payload = {
                "mediaUploadType": "IMAGE_SHARING",
                "fileSize": len(file_data),
                "filename": file,
            }
            url =  "https://www.linkedin.com/voyager/api/voyagerVideoDashMediaUploadMetadata?action=upload"
            response = requests.post(url, headers=HEADERS, json=payload)

            assert response.status_code == 200 and "Failed to pre-upload file"

            response_data = response.json()

            upload_url =  response_data["data"]["value"]["singleUploadUrl"]
            upload_id = response_data["data"]["value"]["urn"]
            upload_ids.append(upload_id)
            # print("uploading to",upload_url)
            # print("uploading to",upload_id)

            response = requests.put(upload_url,headers=HEADERS | {"Content-Type": "application/png"},data=file_data)

            assert response.status_code == 201 and "Failed to upload file"



        # mutli file upload 
        if len(upload_id) > 1:
            gen_entity = lambda id:   { "category": "IMAGE", "mediaUrn": id, "tapTargets": [], "altText": ""} 
            payload = {
                "authorUrn": "urn:li:fsd_profile:" + env["authorUrn"],
                "entities": [
                    gen_entity(id) for id in upload_ids
                ]
            }
            url = "https://www.linkedin.com/voyager/api/voyagerVideoDashMultiPhotos"
            response = requests.post(url,headers=HEADERS, json=payload)
            assert response.status_code == 201 and "Failed to upload multi files (in collection)"
            

            response_data = response.json()

            upload_id = response_data["data"]["identifierUrn"]


        return upload_id

    def upload_post(self,text,media=[]):
        # Publishes a LinkedIn post with optional image media; uploads media if provided and sends a GraphQL request to create the post.

        if type(media) != list:
            media = [media]

        url = 'https://www.linkedin.com/voyager/api/graphql?action=execute&queryId=voyagerContentcreationDashShares.ceaff9980fdffc13affac0e6e1aad5af'
        payload = {
            "variables": {
                "post": {
                    "allowedCommentersScope": "ALL",
                    "intendedShareLifeCycleState": "PUBLISHED",
                    "origin": "PROFILE",
                    "visibilityDataUnion": {
                        "visibilityType": "ANYONE"
                    },
                    "commentary": {
                        "text": text,
                        "attributesV2": []
                    }
                }
            },
            "queryId": "voyagerContentcreationDashShares.ceaff9980fdffc13affac0e6e1aad5af",
            "includeWebMetadata": True
        }


        if len(media) > 0:
            if len(media) == 1:
                upload_id = self.upload_media(media) 
                payload["variables"]["post"]["media"] = {
                    "altText": "",
                    "category": "IMAGE",
                    "mediaUrn": upload_id,
                    "tapTargets": []
                }            
            else:
                upload_id = self.upload_media(media) 
                payload["variables"]["post"]["media"] = {
                    "category": "URN_REFERENCE",
                    "mediaUrn":upload_id,
                    "tapTargets": []
                }
        response = requests.post(url, headers=HEADERS, json=payload)
        print("[upload post]",response.status_code)

    def follow_member(self,id):
        # todo: there is more data about members to extract, like names
        # Sends a follow request to a LinkedIn member by ID using a complex SDUI payload; asserts success via HTTP 200 response.

        payload = {
            "requestId": "com.linkedin.sdui.requests.mynetwork.addaUpdateFollowState",
            "serverRequest": {
                "$type": "proto.sdui.actions.core.ServerRequest",
                "requestId": "com.linkedin.sdui.requests.mynetwork.addaUpdateFollowState",
                "requestedArguments": {
                    "$type": "proto.sdui.actions.requests.RequestedArguments",
                    "payload": {
                        "followStateType": "FollowStateType_FOLLOW_ACTIVE",
                        "memberUrn": {
                            "memberId": f"{id}" 
                        },
                        "postActionSentConfigs": []
                    },
                    "requestedStateKeys": [],
                    "requestMetadata": {
                        "$type": "proto.sdui.common.RequestMetadata"
                    }
                },
                "onClientRequestFailureAction": {
                    "actions": [
                        {
                            "$type": "proto.sdui.actions.core.SetState",
                            "value": {
                                "$type": "proto.sdui.actions.core.SetState",
                                "state": {
                                    "$type": "proto.sdui.State",
                                    "key": {
                                        "$type": "proto.sdui.StateKey",
                                        "value": f"urn:li:fsd_followingState:urn:li:member:{id}",
                                        "key": {
                                            "$type": "proto.sdui.Key",
                                            "value": {
                                                "$case": "id",
                                                "id": f"urn:li:fsd_followingState:urn:li:member:{id}"
                                            }
                                        },
                                        "namespace": ""
                                    },
                                    "value": {
                                        "$case": "stringValue",
                                        "stringValue": "Follow"
                                    },
                                    "isOptimistic": False
                                }
                            }
                        }
                    ]
                },
                "isStreaming": False,
                "rumPageKey": ""
            },
            "states": [],
            "requestedArguments": {
                "$type": "proto.sdui.actions.requests.RequestedArguments",
                "payload": {
                    "followStateType": "FollowStateType_FOLLOW_ACTIVE",
                    "memberUrn": {
                        "memberId": f"{id}"
                    },
                    "postActionSentConfigs": []
                },
                "requestedStateKeys": [],
                "requestMetadata": {
                    "$type": "proto.sdui.common.RequestMetadata"
                },
                "states": []
            }
        }
        url = "https://www.linkedin.com/flagship-web/rsc-action/actions/server-request?sduiid=com.linkedin.sdui.requests.mynetwork.addaUpdateFollowState"
        response = requests.post(url, headers=HEADERS, json=payload)
        assert response.status_code == 200 and f"Failed to follow a member {id}"

    def get_popular_members(self):
        # Fetches a list of popular LinkedIn member IDs by sending a pagination request and extracting member URNs from the response.
        # Returns a list of member IDs as strings.

        url = 'https://www.linkedin.com/flagship-web/rsc-action/actions/pagination?sduiid=com.linkedin.sdui.pagers.mynetwork.adda-cohorts-components'
        payload = {
            "pagerId": "com.linkedin.sdui.pagers.mynetwork.adda-cohorts-components",
            "clientArguments": {
                "$type": "proto.sdui.actions.requests.RequestedArguments",
                "payload": {
                    "startIndex": 0,
                    "token": "7350797200030875648"
                },
                "requestedStateKeys": [],
                "requestMetadata": {
                    "$type": "proto.sdui.common.RequestMetadata"
                },
                "states": []
            },
            "paginationRequest": {
                "$type": "proto.sdui.actions.requests.PaginationRequest",
                "pagerId": "com.linkedin.sdui.pagers.mynetwork.adda-cohorts-components",
                "requestedArguments": {
                    "$type": "proto.sdui.actions.requests.RequestedArguments",
                    "payload": {
                        "startIndex": 0,
                        "token": "7350797200030875648"
                    },
                    "requestedStateKeys": [],
                    "requestMetadata": {
                        "$type": "proto.sdui.common.RequestMetadata"
                    }
                },
                "trigger": {
                    "$case": "itemDistanceTrigger",
                    "itemDistanceTrigger": {
                        "$type": "proto.sdui.actions.requests.ItemDistanceTrigger",
                        "preloadDistance": 3,
                        "preloadLength": 250
                    }
                },
                "retryCount": 2
            }
        }
        response = requests.post(url,headers=HEADERS, json=payload)
        assert response.status_code == 200 and "Failed to get popularmembers"
        member_ids = re.findall(r'"value":"urn:li:fsd_followingState:urn:li:member:(\d+)', response.text)

        return member_ids

    def get_connections(self,count=12):
        # Retrieves a list of LinkedIn connection suggestions (People You May Know) with their names and profile URLs.
        # Returns a dictionary mapping member IDs to their first name, last name, and LinkedIn profile URL.

        url = 'https://www.linkedin.com/flagship-web/rsc-action/actions/pagination?sduiid=com.linkedin.sdui.pagers.mynetwork.addaCohortSeeAll'
        payload = {
            "pagerId": "com.linkedin.sdui.pagers.mynetwork.addaCohortSeeAll",
            "clientArguments": {
                "$type": "proto.sdui.actions.requests.RequestedArguments",
                "payload": {
                    "cohortReasonSource": "IN_SESSION_RELEVANCE",
                    "cohortReasonContext": "IN_SESSION_RELEVANCE",
                    "cohortReasonRelatedCompanyUrns": [],
                    "cohortReasonRelatedSkillUrns": [],
                    "cohortReasonRelatedGeoUrns": [],
                    "cohortReasonRelatedGroupUrns": [],
                    "cohortReasonRelatedIndustryUrns": [],
                    "cohortReasonRelatedMemberUrns": [],
                    "cohortReasonRelatedOrganizationUrns": [],
                    "cohortReasonRelatedSchoolUrns": [],
                    "cohortReasonRelatedSuperTitleUrns": [],
                    "shouldUseIndexPaging": False,
                    "pageSize": count,
                    "pageToken": "f8692734-6bb8-47dd-9f55-abac28883ec0",
                    "isFirstPage": False,
                    "origin": "InvitationOrigin_PYMK_COHORT_SEE_ALL"
                },
                "requestedStateKeys": [],
                "requestMetadata": {"$type": "proto.sdui.common.RequestMetadata"},
                "states": []
            },
            "paginationRequest": {
                "$type": "proto.sdui.actions.requests.PaginationRequest",
                "pagerId": "com.linkedin.sdui.pagers.mynetwork.addaCohortSeeAll",
                "requestedArguments": {
                    "$type": "proto.sdui.actions.requests.RequestedArguments",
                    "payload": {
                        "cohortReasonSource": "IN_SESSION_RELEVANCE",
                        "cohortReasonContext": "IN_SESSION_RELEVANCE",
                        "cohortReasonRelatedCompanyUrns": [],
                        "cohortReasonRelatedSkillUrns": [],
                        "cohortReasonRelatedGeoUrns": [],
                        "cohortReasonRelatedGroupUrns": [],
                        "cohortReasonRelatedIndustryUrns": [],
                        "cohortReasonRelatedMemberUrns": [],
                        "cohortReasonRelatedOrganizationUrns": [],
                        "cohortReasonRelatedSchoolUrns": [],
                        "cohortReasonRelatedSuperTitleUrns": [],
                        "shouldUseIndexPaging": False,
                        "pageSize": count,
                        "pageToken": "f8692734-6bb8-47dd-9f55-abac28883ec0",
                        "isFirstPage": False,
                        "origin": "InvitationOrigin_PYMK_COHORT_SEE_ALL"
                    },
                    "requestedStateKeys": [],
                    "requestMetadata": {"$type": "proto.sdui.common.RequestMetadata"}
                }
            },
            "trigger": {
                "$case": "itemDistanceTrigger",
                "itemDistanceTrigger": {
                    "$type": "proto.sdui.actions.requests.ItemDistanceTrigger",
                    "preloadDistance": 2,
                    "preloadLength": 250
                }
            },
            "retryCount": 1
        }


        response = requests.post(url,headers=HEADERS, json=payload)
        assert response.status_code == 200 and "Failed to fetch connections"

        members = {}
        response = response.text

        # all connection lines
        pattern = r'^[0-9a-fA-F]+:\[\["Connect",\[.*?\]\]\],?$'
        matches = re.findall(pattern, response, re.MULTILINE)
        for line in matches:
            first_name = re.search(r'"firstName":"([^"]+)"', line).group(1)
            last_name = re.search(r'"lastName":"([^"]+)"', line).group(1)
            url = re.search(r'"profileCanonicalUrl":"(https://www\.linkedin\.com/in/[^"]+)"', line).group(1)
            id = re.search(r'"value":"state:invitation:urn:li:member:(\d+)"', line).group(1)
            members[id] = {
                "first_name" : first_name, 
                "last_name" : last_name, 
                "url" : url, 
            }


        return members

    def send_connection_request(self,id,member):
        # Sends a LinkedIn connection request to a user by ID using a structured SDUI payload and asserts request success.
        url = "https://www.linkedin.com/flagship-web/rsc-action/actions/server-request?sduiid=com.linkedin.sdui.requests.mynetwork.addaAddConnection"
        payload = {
            "requestId": "com.linkedin.sdui.requests.mynetwork.addaAddConnection",
            "serverRequest": {
                "$type": "proto.sdui.actions.core.ServerRequest",
                "requestId": "com.linkedin.sdui.requests.mynetwork.addaAddConnection",
                "requestedArguments": {
                    "$type": "proto.sdui.actions.requests.RequestedArguments",
                    "payload": {
                        "inviteeUrn": {
                            "memberId": f"{id}"
                        },
                        "nonIterableProfileId": "",
                        "renderMode": "IconAndText",
                        "firstName": "",
                        "lastName": "",
                        "isDisabled": {
                            "key": "",
                            "namespace": None
                        },
                        "connectionState": {
                            "key": f"state:invitation:urn:li:member:{id}",
                            "namespace": None
                        },
                        "origin": "InvitationOrigin_PYMK_COHORT_SECTION",
                        "profileCanonicalUrl": "",
                        "profilePictureRenderPayload": "",
                        "firstFiveInviteCount": {
                            "key": "guidedFlowNumSentInvites",
                            "namespace": ""
                        },
                        "guidedFlowUrlandProfileList": {
                            "key": "guidedFlowUrlAndPictureList",
                            "namespace": "guidedFlowUrlAndPictureListNameSpace"
                        },
                        "postActionSentConfigs": []
                    },
                    "requestedStateKeys": [
                        {
                            "$type": "proto.sdui.StateKey",
                            "value": "guidedFlowNumSentInvites",
                            "key": {
                                "$type": "proto.sdui.Key",
                                "value": {
                                    "$case": "id",
                                    "id": "guidedFlowNumSentInvites"
                                }
                            },
                            "namespace": ""
                        },
                        {
                            "$type": "proto.sdui.StateKey",
                            "value": "guidedFlowUrlAndPictureList",
                            "key": {
                                "$type": "proto.sdui.Key",
                                "value": {
                                    "$case": "id",
                                    "id": "guidedFlowUrlAndPictureList"
                                }
                            },
                            "namespace": "guidedFlowUrlAndPictureListNameSpace"
                        }
                    ],
                    "requestMetadata": {
                        "$type": "proto.sdui.common.RequestMetadata"
                    }
                },
                "onClientRequestFailureAction": {
                    "actions": [
                        {
                            "$type": "proto.sdui.actions.core.SetState",
                            "value": {
                                "$type": "proto.sdui.actions.core.SetState",
                                "stateKey": "",
                                "stateValue": "",
                                "state": {
                                    "$type": "proto.sdui.State",
                                    "stateKey": "",
                                    "key": {
                                        "$type": "proto.sdui.StateKey",
                                        "value": f"state:invitation:urn:li:member:{id}",
                                        "key": {
                                            "$type": "proto.sdui.Key",
                                            "value": {
                                                "$case": "id",
                                                "id": f"state:invitation:urn:li:member:{id}"
                                            }
                                        },
                                        "namespace": ""
                                    },
                                    "value": {
                                        "$case": "stringValue",
                                        "stringValue": "Connect"
                                    },
                                    "isOptimistic": False
                                },
                                "isOptimistic": False
                            }
                        },
                        {
                            "$type": "proto.sdui.actions.core.SetState",
                            "value": {
                                "$type": "proto.sdui.actions.core.SetState",
                                "stateKey": "",
                                "stateValue": "",
                                "state": {
                                    "$type": "proto.sdui.State",
                                    "stateKey": "",
                                    "key": {
                                        "$type": "proto.sdui.StateKey",
                                        "value": "connect-button-disabled-yazid-baziz-167705128",
                                        "key": {
                                            "$type": "proto.sdui.Key",
                                            "value": {
                                                "$case": "id",
                                                "id": "connect-button-disabled-yazid-baziz-167705128"
                                            }
                                        },
                                        "namespace": ""
                                    },
                                    "value": {
                                        "$case": "booleanValue",
                                        "booleanValue": False
                                    },
                                    "isOptimistic": False
                                },
                                "isOptimistic": False
                            }
                        }
                    ]
                },
                "isStreaming": False,
                "rumPageKey": ""
            },
            "states": [
                {
                    "key": "guidedFlowNumSentInvites",
                    "namespace": "",
                    "value": 2
                }
            ],
            "requestedArguments": {
                "$type": "proto.sdui.actions.requests.RequestedArguments",
                "payload": {
                    "inviteeUrn": {
                        "memberId": f"{id}"
                    },
                    "nonIterableProfileId": "",
                    "renderMode": "IconAndText",
                    "firstName": "",
                    "lastName": "",
                    "isDisabled": {
                        "key": "",
                        "namespace": None
                    },
                    "connectionState": {
                        "key": f"state:invitation:urn:li:member:{id}",
                        "namespace": None
                    },
                    "origin": "InvitationOrigin_PYMK_COHORT_SECTION",
                    "profileCanonicalUrl": "",
                    "profilePictureRenderPayload": "",
                    "firstFiveInviteCount": {
                        "key": "guidedFlowNumSentInvites",
                        "namespace": ""
                    },
                    "guidedFlowUrlandProfileList": {
                        "key": "guidedFlowUrlAndPictureList",
                        "namespace": "guidedFlowUrlAndPictureListNameSpace"
                    },
                    "postActionSentConfigs": []
                },
                "requestedStateKeys": [
                    {
                        "$type": "proto.sdui.StateKey",
                        "value": "guidedFlowNumSentInvites",
                        "key": {
                            "$type": "proto.sdui.Key",
                            "value": {
                                "$case": "id",
                                "id": "guidedFlowNumSentInvites"
                            }
                        },
                        "namespace": ""
                    },
                    {
                        "$type": "proto.sdui.StateKey",
                        "value": "guidedFlowUrlAndPictureList",
                        "key": {
                            "$type": "proto.sdui.Key",
                            "value": {
                                "$case": "id",
                                "id": "guidedFlowUrlAndPictureList"
                            }
                        },
                        "namespace": "guidedFlowUrlAndPictureListNameSpace"
                    }
                ],
                "requestMetadata": {
                    "$type": "proto.sdui.common.RequestMetadata"
                },
                "states": [
                    {
                        "key": "guidedFlowNumSentInvites",
                        "namespace": "",
                        "value": 2
                    }
                ]
            }
        }
        response = requests.post(url, headers=HEADERS | {"Content-Type": "application/json"}, json=payload)
        assert response.status_code == 200 and f"Failed to send a connection request to {id} account is {member['url']}" 

    def send_bulk_connections(self,amount=12):
        # Sends LinkedIn connection requests in bulk to a specified number of suggested members using their IDs and profile data.
        members = self.get_connections(amount) 
        for id in members.keys():
            self.send_connection_request(id,members[id])
            # print('send request to',members[id]["first_name"],members[id]["last_name"],members[id]["url"])

    def get_my_posts(self,offset=0,count=20):
        # Retrieves a list of post URNs from the authenticated user's LinkedIn profile feed using a GraphQL query.
        # Returns a list of post IDs extracted from activity URNs.
        
        
        # smth about params is not working
        # maybe related to the encoding of ":"
        # any change in the url format will cause failure
        # todo: you can extract more info, imgs and more 
        url = f"""\
            https://www.linkedin.com/voyager/api/graphql?includeWebMetadata=true&\
            variables=(count:{count},start:{offset},profileUrn:urn%3Ali%3Afsd_profile%3A{env["authorUrn"]})&\
            queryId=voyagerFeedDashProfileUpdates.89d660b86d2c3091afff9dd268c4c484\
            """.replace("        ","")
        response = requests.get(url, headers=HEADERS)
        data = response.json()


        # if response.status_code != 200:
            # print(response.text)
        assert response.status_code == 200 and "Failed to get posts"

        posts = data["data"]["data"]["feedDashProfileUpdatesByMemberShareFeed"]["*elements"]
        for i in range(len(posts)):
            posts[i] = posts[i].split("activity:")[1].split(",")[0]


        return posts

    def delete_post(self,id):
        # Deletes a LinkedIn post by its activity ID using a specific GraphQL mutation query.

        url = "https://www.linkedin.com/voyager/api/graphql?action=execute&queryId=voyagerContentcreationDashShares.c459f081c61de601a90d103fbea46496"
        payload = {
            "variables": {
                "updateUrn": f"urn:li:fsd_update:(urn:li:activity:{id},MEMBER_SHARES,EMPTY,DEFAULT,false)"
            },
            "queryId": "voyagerContentcreationDashShares.c459f081c61de601a90d103fbea46496"
        }
        response = requests.post(url, json=payload, headers=HEADERS)
        assert response.status_code == 200 and f"Failed to delete post id='{id}'"

    def delete_posts_bulk(self,ids):
        # Deletes multiple LinkedIn posts by their IDs by calling `delete_post` for each one.
        for id in ids:
            self.delete_post(id)

    def get_feed_posts(self,offset=0,count=12):
        # Returns a list of dictionaries, each containing metadata about a matched LinkedIn post,
        # including its URN, link, author's profile link, username, and post text.

        pagination_token = "1556267518-1752613822911-63567cd0f8a5dac945186dbfd093e122"
        url = f"""https://www.linkedin.com/voyager/api/graphql?\
            variables=(start:{offset},count:{count},paginationToken:{pagination_token},sortOrder:RELEVANCE)&\
            queryId=voyagerFeedDashMainFeed.7a50ef8ba5a7865c23ad5df46f735709\
            """.replace("        ","")
        response = requests.get(url,headers=HEADERS)

        assert response.status_code == 200 and "Failed to get_feed_posts"
        data = response.json()

        posts_urnss = data["data"]["data"]["feedDashMainFeedByMainFeed"]["*elements"]
        infos = data["included"]


        posts = []

        for info in infos:
            if info["entityUrn"] in posts_urnss:
                post_link = utils.nested_get(info,["socialContent","shareUrl"],"not found")
                profile_link = utils.nested_get(info,["actor","navigationContext","actionTarget"],"not found")
                user_name = utils.nested_get(info,["actor","name","text"],"not found")
                text = utils.nested_get(info,["commentary","text","text"],"not found")
                print("=" * 100)
                print("post_link",post_link)
                print("profile_link",profile_link)
                print("user_name",user_name)
                print("text",text)
                print()

                posts.append({
                    "urn": info["entityUrn"],
                    "post_link": post_link,
                    "profile_link": profile_link,
                    "user_name": user_name,
                    "text": text
                })
        return posts

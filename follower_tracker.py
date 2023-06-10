# A simple script to track followers on instagram

import requests
import urllib
import json
import glob
import os
from notification_service import NotificationService
from config_helper import get_config

CONFIG = get_config()
IG_CONFIG = CONFIG["IG_CONFIG"]
ANDROID_APP_CONFIG = CONFIG["ANDROID_APP_CONFIG"]
INSTAGRAM_USER_ID = IG_CONFIG["INSTAGRAM_USER_ID"]
INSTAGRAM_USER_COOKIES = IG_CONFIG["COOKIES"]

def get_complete_follower_set(instagram_user_id):
    ''' Returns a set of the complete follower list of instagram user. This function constructs
    a graphql query that gets the list of followers. It queries instagram for
    a user's paginated follower data until the last page is reached
    '''
    query_hash_for_follower_list = IG_CONFIG["GRAPHQL_QUERY_HASH"]
    graphql_query_variables = {
        "id": instagram_user_id,
        "first": 50
    }

    # url encode query variables. This is the format that instagram graph api
    # wants, Otherwise it will complain.
    graphql_query_variables_quoted = urllib.parse.quote(json.dumps(graphql_query_variables), safe='~()*!.\'')

    # Example url: https://www.instagram.com/graphql/query/?query_hash=GRAPHQL_QUERY_HASH&variables=%7B%22id%22%3A%22INSTAGRAM_USER_ID%22%2C%22first%22%3A302%2C%22after%22%3A%22AFTER_HASH%3D%3D%22%7D
    graphql_get_follower_url = "https://www.instagram.com/graphql/query/?query_hash={0}&variables={1}".format(query_hash_for_follower_list, graphql_query_variables_quoted)

    # Instagram response is paginated. Request follower data until there are no
    # more pages.
    # The format of the data is as follows:
    #
    # data: {
    #     user: {
    #         edge_followed_by: {
    #             count: 302,
    #             page_info: {
    #                 has_next_page: true,
    #                 end_cursor: "hash"
    #             },
    #             edges: [
    #                 {
    #                     node: {
    #                     id: "follower_id",
    #                     username: "follower_username",
    #                     full_name: "full name",
    #                     profile_pic_url: "profile_pic_url",
    #                     is_private: true,
    #                     is_verified: false,
    #                     followed_by_viewer: true,
    #                     requested_by_viewer: false
    #                     }
    #                 }
    #             ]
    #         }
    #     }
    # }
    has_next_page = True
    complete_follower_list = []

    i = 0 # a failsafe in case of an infinite loop. End loop at 10th increment.

    while has_next_page or i < 10:
        # get a page of followers
        instagram_response = requests.get(
            url=graphql_get_follower_url,
            cookies=INSTAGRAM_USER_COOKIES)

        instagram_follower_data = instagram_response.json()["data"]["user"]["edge_followed_by"]

        current_page_of_followers = instagram_follower_data["edges"]
        complete_follower_list += [data["node"]["username"] for data in instagram_follower_data["edges"]]


        has_next_page = instagram_follower_data["page_info"]["has_next_page"]
        if has_next_page:
            # end_cursor is a property of instagram's graph api json response.
            # If end_cursor is an empty string there are no more pages.
            # Otherwise, keep requesting for followers.
            # Initialize this as null since we don't know the value of end_cursor
            # before sending our first request.
            graphql_query_variables["after"] = instagram_follower_data["page_info"]["end_cursor"]
            graphql_query_variables_quoted = urllib.parse.quote(json.dumps(graphql_query_variables), safe='~()*!.\'')
            graphql_get_follower_url = "https://www.instagram.com/graphql/query/?query_hash={0}&variables={1}".format(query_hash_for_follower_list, graphql_query_variables_quoted)

        i += 1 # increment failsafe counter

    # For some reason that I haven't figured out, follower list could have
    # duplicates. Return a set so duplicate values are removed.
    return set(complete_follower_list)

def write_follwer_set_to_file(follower_set):
    ''' Writes set of unique followers to a file. Returns a tuple of the path
    of the two most recent files, the second element being the most recent.
    '''
    latest_filename = "./followers/0"
    file_list = glob.glob('./followers/*')

    if len(file_list) > 0:
        latest_filename = max(file_list, key=os.path.getctime)

    # increment filename by 1. Filename is the number it was created
    new_filename = "./followers/" + str(int(latest_filename[-1]) + 1)

    with open(str(new_filename), 'w') as f:
        f.write(','.join(list(follower_set)))

    return latest_filename, new_filename

def get_follower_set_from_file(path):
    ''' path is the path of a csv-formatted file where each value is a
    follower.
    '''

    with open(path) as f:
        csv_contents = f.read()

    follower_list = csv_contents.split(',')
    # strip last element to get rid of newline character
    if len(follower_list) > 0:
        follower_list[-1] = follower_list[-1].strip()

    return set(follower_list)

def get_unfollower_list_from_previous_and_current_followers(previous_followers, current_followers):
    ''' Returns a list of unfollowers by comparing a previously fetched set
    of followers to the most recently fetched set of followers.
    '''
    return list(previous_followers.difference(current_followers))

def get_most_recent_filename():
    file_list = glob.glob('./followers/*')

    if len(file_list) > 0:
        latest_filename = max(file_list, key=os.path.getctime)

    return latest_filename[-1]


if __name__ == '__main__':
    follower_set = get_complete_follower_set(INSTAGRAM_USER_ID)
    previous_followers_filepath, current_followers_filepath = write_follwer_set_to_file(follower_set)


    # Compare previous and more recent followers by comparing the files
    previous_followers_set = get_follower_set_from_file(previous_followers_filepath)
    current_followers_set = get_follower_set_from_file(current_followers_filepath)

    unfollowers = get_unfollower_list_from_previous_and_current_followers(
        previous_followers_set,
        current_followers_set
        )

    # Send notification of unfollowers
    if len(unfollowers) == 1:
        message = '{} has unfollowed you! Unfollow them back!'.format(unfollowers[0])
    elif len(unfollowers) == 2:
        message = '{} and {} have unfollowed you! Unfollow them back!'.format(unfollowers[0],unfollowers[1])
    elif len(unfollowers) == 3:
        message = '{}, {}, and {} have unfollowed you! Unfollow them back!'.format(unfollowers[0],unfollowers[1],unfollowers[2])
    elif len(unfollowers) >= 4:
        message = '{}, {}, {}, and others have unfollowed you! Unfollow them back!'.format(unfollowers[0],unfollowers[1],unfollowers[2])

    if len(unfollowers) > 0:
        title = "You've been unfollowed!"
        notification_service_instance = NotificationService()
        notification_service_instance.send_notification(title, message)

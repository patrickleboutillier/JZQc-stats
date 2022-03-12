from zwift import Client
import datetime, pprint
pp = pprint.PrettyPrinter(indent=4)

today = datetime.datetime.now().strftime("%Y-%m-%d")
yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
when = yesterday

username = 'patrick.leboutillier@gmail.com'
password = '95cicciiA!'
client = Client(username, password)
jzqc_club_id = "db29559b-e475-47ac-84ef-8ac6a285f4f9"
jzqc_activity = { 'name': 'JZQc', 'date': when, 'members': 0, 'active_members': 0, 'rides':0, 'duration': 0, 'distance': 0, 'elevation': 0 , 'calories': 0 }     


def get_jzcq_members(profile):
    members = []
    batch = 100
    start = 0
    got = batch
    while got == batch:
        url = "/api/clubs/club/{}/roster?limit={}&start={}&status=MEMBER".format(jzqc_club_id, batch, start)
        json = profile.request.json(url)
        for m in json['results']:
            members.append({'id': m['id'], 'name': m['firstName'] + ' ' + m['lastName']})
        got = len(json['results'])
        start += got
    return members


# /api/activity-feed/feed/club/db29559b-e475-47ac-84ef-8ac6a285f4f9/?includeFavorites=false&includeFollowees=false&includeSelf=false&limit=50&start_after_activity_id=1033524280400298032
def get_jzqc_activities(profile):
    batch = 50
    last = None
    active_members = {}
    while True:
        after = ""
        if last is not None:
            after = "&start_after_activity_id={}".format(last)
        url = "/api/activity-feed/feed/club/{}/?includeFavorites=false&includeFollowees=false&includeSelf=false&limit={}{}".format(jzqc_club_id, batch, after)
        json = profile.request.json(url)
        print("Fetched {} activities, from {} to {} ".format(len(json), json[0]['startDate'], json[len(json)-1]['startDate']))


        skip = False
        took = False
        for a in json:
            last = a['id']
            start = a['startDate']
            end = a['endDate']
            if start.startswith(when):
                took = True
                if a['profile']['id'] in active_members:
                    active_members[a['profile']['id']] = True
                    jzqc_activity['active_members'] += 1
                active_members[a['profile']['id']] = True
                jzqc_activity['rides'] += 1
                jzqc_activity['calories'] += a['calories']
                jzqc_activity['distance'] += a['distanceInMeters'] / 1000.0    
                jzqc_activity['elevation'] += a['totalElevation'] / 1000.0
                jzqc_activity['duration'] += a['movingTimeInMs'] / 3600000.0
            elif start > when:
                skip = True
        if not took and not skip:
            return 


def add_jzqc_activity(activity):
    jzqc_activity['members'] += 1
    if activity['distance'] > 0:
        jzqc_activity['active_members'] += 1
        for k in ['rides', 'duration', 'distance', 'elevation', 'calories']:
            jzqc_activity[k] += activity[k]



# YYYY-MM-DD
def get_player_activity(client, profile):
    id = profile['id']
    activity = { 'name': profile['name'], 'rides':0, 'duration': 0, 'distance': 0, 'elevation': 0 , 'calories': 0 }     
    
    for a in client.get_activity(id).list(0, 10):
        start = a['startDate']
        if start.startswith(when):
            activity['rides'] += 1
            activity['calories'] += a['calories']
            activity['distance'] += a['distanceInMeters'] / 1000.0    
            activity['elevation'] += a['totalElevation'] / 1000.0
            dur = a['duration'].split(":")  # in hours, i.e. 1:26
            mins = 0
            if len(dur) == 1:
                mins = int(dur[0])
            else:
                if dur[1] == '':
                    dur[1] = 0
                mins = int(dur[0]) * 60 + int(dur[1])
            activity['duration'] += mins / 60.0     
    
    #if activity['distance'] > 0:
    #    print(activity)
    return activity


my_profile = client.get_profile()
#jzqc_members = get_jzcq_members(my_profile)
#print("Found {} JZQC members, compiling activity for {}".format(len(jzqc_members), when))
get_jzqc_activities(my_profile)

# Compile activity for each JZQC member
#for m in jzqc_members:
#    profile = m
#    act = get_player_activity(client, profile)
#    if act is not None:
#        add_jzqc_activity(act)    


print("")
print(jzqc_activity)
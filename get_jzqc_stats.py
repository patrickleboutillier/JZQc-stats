from zwift import Client
import creds, datetime, sys, pprint
pp = pprint.PrettyPrinter(indent=4)

when = sys.argv[1]
client = Client(creds.username, creds.password)
jzqc_club_id = "db29559b-e475-47ac-84ef-8ac6a285f4f9"


def utc_to_local(utc_str):
    dt = datetime.datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%S.%f%z")
    return dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None).isoformat()


def get_jzcq_members(profile):
    members = {}
    batch = 100
    start = 0
    got = batch
    while got == batch:
        url = "/api/clubs/club/{}/roster?limit={}&start={}&status=MEMBER".format(jzqc_club_id, batch, start)
        json = profile.request.json(url)
        for m in json['results']:
            members[m['id']] = {'id': m['id'], 'name': m['firstName'] + ' ' + m['lastName'], 'active':False, 'activities':{}}
        got = len(json['results'])
        start += got
    return members


def get_jzqc_member_activities(client, id, jzqc_members):
    for a in client.get_activity(id).list(0, 10):
        start = utc_to_local(a['startDate'])
        if start.startswith(when):
            activity = {}
            activity['id'] = a['id']
            activity['sport'] = a['sport'].lower()
            activity['calories'] = a['calories']
            activity['distance'] = a['distanceInMeters'] / 1000.0    
            activity['elevation'] = a['totalElevation']
            dur = a['duration'].split(":")  # in hours, i.e. 1:26
            mins = 0
            if len(dur) == 1:
                if dur[0] == '':
                    dur[0] = 0
                mins = int(dur[0])
            else:
                if dur[1] == '':
                    dur[1] = 0
                mins = int(dur[0]) * 60 + int(dur[1])
            activity['duration'] = mins / 60.0     

            if activity['distance'] != 0 and activity['duration'] != 0:
                jzqc_members[id]['active'] = True
                jzqc_members[id]['activities'][a['id']] = activity


profile = client.get_profile()
jzqc_members = get_jzcq_members(profile)

# Compile activity for each JZQC member
for id in jzqc_members:
    act = get_jzqc_member_activities(client, id, jzqc_members)   

jzqc_total_activity = { 'name': 'JZQc', 'date': when, 'members': len(jzqc_members.keys()), 'active_members': 0, 
    'activities': 0, 'running': 0, 'cycling': 0,
    'duration': 0, 'distance': 0, 'elevation': 0 , 'calories': 0,
    'avg_duration': 0, 'avg_distance': 0 }     
for mid in jzqc_members.keys():
    if jzqc_members[mid]['active']:
        jzqc_total_activity['active_members'] += 1
        for aid in jzqc_members[mid]['activities'].keys():
            activity = jzqc_members[mid]['activities'][aid]
            jzqc_total_activity['activities'] += 1
            if activity['sport'] in jzqc_total_activity:
                jzqc_total_activity[activity['sport']] += 1
            else:
                jzqc_total_activity[activity['sport']] = 1
            for f in ['duration', 'distance', 'elevation', 'calories']:
                jzqc_total_activity[f] += activity[f]
            jzqc_total_activity['avg_duration'] = jzqc_total_activity['duration'] / jzqc_total_activity['activities'] 
            jzqc_total_activity['avg_distance'] = jzqc_total_activity['distance'] / jzqc_total_activity['activities'] 

def verbose_report():
    print("Rapport quotidien pour la date du {}:".format(when))
    print("- Il y a {} membres dans le club Zwift JZQc".format(len(jzqc_members.keys())))
    print("- {} membres JZQC ont fait un total de {} sorties ({} vélo, {} course)".format(jzqc_total_activity['active_members'], 
        jzqc_total_activity['activities'], jzqc_total_activity['cycling'], jzqc_total_activity['running']))
    print("- Ils ont été actifs au total {:.0f} heures et ont dépensé au total {:.0f} calories".format(
        jzqc_total_activity['duration'], jzqc_total_activity['calories']))
    print("- Ils ont parcourus au total {:.0f} kilomètres et grimpé au total {:.0f} mètres".format(
        jzqc_total_activity['distance'], jzqc_total_activity['elevation']))
    print("- La sortie moyenne avait une distance {:.0f} kilomètres avec une durée de {:.0f} heures".format(
        jzqc_total_activity['avg_distance'], jzqc_total_activity['avg_duration']))
    print("# ", jzqc_total_activity)

def csv_report():
    print("{}\t{}\t{}\t{}\t{}\t{}\t{:0f}\t{:0f}\t{:0f}\t{:0f}".format(when, len(jzqc_members.keys()), jzqc_total_activity['active_members'], jzqc_total_activity['activities'],
        jzqc_total_activity['cycling'], jzqc_total_activity['running'], jzqc_total_activity['duration'], jzqc_total_activity['calories'],
        jzqc_total_activity['distance'], jzqc_total_activity['elevation']))


csv_report()
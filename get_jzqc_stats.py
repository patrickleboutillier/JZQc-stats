from zwift import Client
from multiprocessing import Pool, current_process
import creds, datetime, argparse, copy

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("date", type=str, help="date")
args = parser.parse_args()

nb_procs = 4
when = args.date
clients = {}
clients['main'] = Client(creds.username, creds.password)
jzqc_club_id = "db29559b-e475-47ac-84ef-8ac6a285f4f9"
total = 'Total JZQc'


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
            members[m['id']] = {'id': m['id'], 'name': m['firstName'] + ' ' + m['lastName'], 'active_in': {}, 'activities':{}}
        got = len(json['results'])
        start += got
    return members


def get_jzqc_member_activities(id):
    global clients
    pid = current_process().pid
    if pid not in clients:
        clients[pid] = Client(creds.username, creds.password)
    client = clients[pid]
    activities = {}
    activities['active_in'] = {}
    activities['activities'] = {}
    events = {}
    zas = client.get_activity(id).list(0, 20)
    for a in zas:
        start = utc_to_local(a['startDate'])
        event = a['name']

        if not start.startswith(when):
            continue

        if "jzqc" in event.lower():
            events[event] = {}

        activity = {}
        activity['id'] = a['id']
        activity['event'] = event
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
            activities['active_in'][total] = True
            activities['active_in'][event] = True
            activities['activities'][a['id']] = activity
    return id, events, activities


profile = clients['main'].get_profile()
jzqc_members = get_jzcq_members(profile)
jzqc_events = { total: True }
event_template = { 'event': None, 'date': when, 'active_members': 0, 
    'activities': 0, 'running': 0, 'cycling': 0, 'duration': 0, 'distance': 0, 'elevation': 0 , 'calories': 0, 'avg_duration': 0, 'avg_distance': 0 }


# Compile activity for each JZQC member
with Pool(nb_procs) as p:
    results = p.map(get_jzqc_member_activities, jzqc_members)

for id, events, activities in results:
    for e in events.keys():
        if e not in jzqc_events:
            jzqc_events[e] = events[e]
    jzqc_members[id]['active_in'] = activities['active_in']
    jzqc_members[id]['activities'] = activities['activities']

jzqc_event_activity = {}
for event in jzqc_events:
    jzqc_event_activity[event] = copy.deepcopy(event_template)
    jzqc_event_activity[event]['event'] = event  

for mid in jzqc_members.keys():
    if total in jzqc_members[mid]['active_in']:
        for event in jzqc_events:
            if event in jzqc_members[mid]['active_in']:
                jzqc_event_activity[event]['active_members'] += 1

        for aid in jzqc_members[mid]['activities'].keys():
            activity = jzqc_members[mid]['activities'][aid]
            for event in [activity['event'], total]:
                if event in jzqc_events:
                    jzqc_event_activity[event]['activities'] += 1
                    if activity['sport'] in jzqc_event_activity[event]:
                        jzqc_event_activity[event][activity['sport']] += 1
                    else:
                        jzqc_event_activity[event][activity['sport']] = 1
                    for f in ['duration', 'distance', 'elevation', 'calories']:
                        jzqc_event_activity[event][f] += activity[f]
                    jzqc_event_activity[event]['avg_duration'] = jzqc_event_activity[event]['duration'] / jzqc_event_activity[event]['activities'] 
                    jzqc_event_activity[event]['avg_distance'] = jzqc_event_activity[event]['distance'] / jzqc_event_activity[event]['activities'] 


def verbose_report():
    print("# Rapport quotidien pour la date du {}:".format(when))
    print("# - Il y a {} membres dans le club Zwift JZQc".format(len(jzqc_members.keys())))
    for event in jzqc_events:
        if jzqc_event_activity[event]['active_members'] >= 5:
          verbose_event_report(event)


def verbose_event_report(event):
    print("#   Evénement '{}':".format(event))
    print("#   - {} membres JZQc ont fait un total de {} sorties ({} vélo, {} course)".format(jzqc_event_activity[event]['active_members'], 
        jzqc_event_activity[event]['activities'], jzqc_event_activity[event]['cycling'], jzqc_event_activity[event]['running']))
    print("#   - Ils ont été actifs au total {:.0f} heures et ont dépensé au total {:.0f} calories".format(
        jzqc_event_activity[event]['duration'], jzqc_event_activity[event]['calories']))
    print("#   - Ils ont parcouru au total {:.0f} kilomètres et grimpé au total {:.0f} mètres".format(
        jzqc_event_activity[event]['distance'], jzqc_event_activity[event]['elevation']))
    print("#   - La sortie moyenne avait une distance {:.0f} kilomètres avec une durée moyenne de {:.1f} heures".format(
        jzqc_event_activity[event]['avg_distance'], jzqc_event_activity[event]['avg_duration']))


def csv_report():
    print("{},{},{},{},{},{},{:.0f},{:.0f},{:.0f},{:.0f}".format(when, len(jzqc_members.keys()), jzqc_event_activity[total]['active_members'], jzqc_event_activity[total]['activities'],
        jzqc_event_activity[total]['cycling'], jzqc_event_activity[total]['running'], jzqc_event_activity[total]['duration'], jzqc_event_activity[total]['calories'],
        jzqc_event_activity[total]['distance'], jzqc_event_activity[total]['elevation']))


csv_report()
verbose_report()

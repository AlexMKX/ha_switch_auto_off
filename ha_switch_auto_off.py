import itertools
from typing import List, Tuple, Any

import appdaemon.plugins.hass.hassapi as hass
import threading
import yaml
from collections import defaultdict
import datetime


class switchData:
    deadline: datetime.datetime
    turned_on: datetime.datetime
    timeout: int

    def __init__(self):
        self.turned_on = None
        self.deadline = datetime.datetime.now()
        self.timeout = 10


class sensorData:
    switches: list
    delay: int

    def __init__(self):
        self.switches = []


class ha_switch_auto_off(hass.Hass):
    mutex: threading.Lock
    switches: defaultdict[str]
    sensors: defaultdict[str]
    state_handle = None

    def initialize(self):
        self.mutex = threading.Lock()
        self.sensors = defaultdict(sensorData)
        self.switches = defaultdict(switchData)
        # pydevd_pycharm.settrace(suspend=False)
        self.run_in(self.load_config, 1)
        self.run_every(self.check_sensors, "now+2", 30)
        self.run_every(self.turn_off_switches, "now+5", 30)
        self.state_handle = self.listen_state(self.on_state)
        pass

    def on_state(self, entity, attribute, before, after, *args):
        if self.mutex.acquire(blocking=True, timeout=10):
            try:
                if entity in self.switches.keys() and (before, after) == ('off', 'on'):
                    switch: switchData = self.switches[entity]
                    switch.turned_on = datetime.datetime.now()
                    switch.deadline = max(datetime.datetime.now() + datetime.timedelta(minutes=switch.timeout),
                                          switch.deadline)
                    self.log(f'{entity} {before}->{after} deadline {switch.deadline}', level='DEBUG')
            finally:
                self.mutex.release()
        pass

    def turn_off_switches(self, arg):
        if self.mutex.acquire(blocking=False):
            states = self.get_state()
            to_off = [x for x in self.switches.items() if
                      x[1].deadline < datetime.datetime.now() and states.get(x[0], {}).get('state') == 'on']
            [self.turn_off(x[0]) for x in to_off]
            self.mutex.release()
        pass

    def check_sensors(self, arg):
        if self.mutex.acquire(blocking=False):
            states = self.get_state()
            signalled = [y['entity_id'] for x, y in states.items() if y['entity_id'] in self.sensors.keys() if
                         y['state'] == 'on']
            for x in signalled:
                switches = self.sensors[x].switches
                for s in switches:
                    deadline_before = self.switches[s].deadline
                    self.switches[s].deadline = max(datetime.datetime.now() + datetime.timedelta(
                        minutes=self.sensors[x].delay), self.switches[s].deadline)
                    if self.switches[s].deadline != deadline_before:
                        self.log(
                            f'Deadline change for {s} because of {x} {deadline_before}->{self.switches[s].deadline}',
                            level='DEBUG')
            self.mutex.release()
        pass

    def load_config(self, arg):
        try:
            self.mutex.acquire(blocking=True)
            with open(f"{self.app_dir}/ha_switch_auto_off/config.yml", "r") as f:
                z = yaml.safe_load(self.render_template(f.read()))
                states = self.get_state()
                for i in z['sensors']:
                    for s in i['sensors']:
                        for switch in i['switches']:
                            subnetities = states.get(switch, {}).get('attributes', {}).get('entity_id')
                            if subnetities:
                                self.sensors[s].switches.extend(subnetities)
                            else:
                                if states.get(switch, {}):
                                    self.sensors[s].switches.append(switch)
                        self.sensors[s].delay = int(i['delay'])
            conf_switches = set(itertools.chain(*[x.switches for x in self.sensors.values()]))
            for x in conf_switches:
                if x not in self.switches.keys():
                    self.switches[x] = switchData()
            for x in self.switches.keys():
                if x not in conf_switches:
                    del (self.switches[x])
            # [del self.switches[x] for x in self.switches.keys() if x not in conf_switches]
            for s in conf_switches:
                self.switches[s].timeout = max([x[1].delay for x in self.sensors.items() if s in x[1].switches])
        finally:
            self.mutex.release()
        pass

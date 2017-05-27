import random
import getpass
import time
import subprocess
import os

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub, SubscribeListener
from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNOperationType, PNStatusCategory

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Notify', '0.7')
from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import GObject
from gi.repository import Notify as notify

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

PEOPLE = {}

PUBNUB_PUBLISH_KEY="pub-c-82187f2d-a991-45eb-a554-72761d42e7a0"
PUBNUB_SUBSCRIBE_KEY="sub-c-4a0a4a3c-4222-11e7-b6a4-02ee2ddab7fe"
CHANNEL_NAME = "UbuntuPodcastTest"
APPINDICATOR_ID = 'Handsup'
CAPS_LOCK = "unknown"
pnconfig = PNConfiguration()
indicator = None
menu = None

def set_up_pubnub():
    pnconfig.subscribe_key = PUBNUB_SUBSCRIBE_KEY
    pnconfig.publish_key = PUBNUB_PUBLISH_KEY
    pnconfig.uuid = getpass.getuser() #"%s-%s" % (getpass.getuser(), random.randint(1,1000))
    pubnub = PubNub(pnconfig)
    subscribe_listener = SubscribeListener()
    pubnub.add_listener(subscribe_listener)
    pubnub.add_listener(Handler())

    pubnub.subscribe().channels(CHANNEL_NAME).with_presence().execute()
    subscribe_listener.wait_for_connect()
    pubnub.here_now().channels(CHANNEL_NAME).include_uuids(True).async(here_now_cb)
    return pubnub


class Handler(SubscribeCallback):
    def status(self, pubnub, status):
        if status.operation == PNOperationType.PNSubscribeOperation \
                or status.operation == PNOperationType.PNUnsubscribeOperation:
            if status.category == PNStatusCategory.PNConnectedCategory:
                print "connected"
            elif status.category == PNStatusCategory.PNReconnectedCategory:
                print "reconnected"
            elif status.category == PNStatusCategory.PNDisconnectedCategory:
                print "disconnected"
            elif status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
                print "unexpectedly disconnected"
            elif status.category == PNStatusCategory.PNAccessDeniedCategory:
                print "denied"
            else:
                print "some other connection error"
        elif status.operation == PNOperationType.PNSubscribeOperation:
            if status.is_error():
                print "heartbeat error"
            else:
                print "heartbeat ok"
        else:
            print "something weird happened", status
 
    def presence(self, pubnub, presence):
        if presence.state:
            update_people(presence.uuid, presence.state.get("handup", "?"))

    def message(self, pubnub, message):
        pass  # handle incoming messages

def here_now_cb(result, status):
    if status.is_error():
        return
    for channel_data in result.channels:
        for occupant in channel_data.occupants:
            state = pubnub.get_state().channels(CHANNEL_NAME).uuid(occupant.uuid).sync()
            if state:
                update_people(occupant.uuid, state.get("handup", "?"))

def update_people(person_uuid, handup):
    if person_uuid not in PEOPLE:
        mi = gtk.MenuItem(person_uuid)
        n = notify.Notification.new("", "", "")
        PEOPLE[person_uuid] = ["off", mi, n]
        menu.append(mi)
    PEOPLE[person_uuid][0] = handup
    if handup == "on":
        PEOPLE[person_uuid][1].show()
    else:
        PEOPLE[person_uuid][1].hide()
    their = "their"
    name = person_uuid
    if handup == "on":
        updown = "up"
        icon = os.path.abspath("open-green.svg")
    else:
        updown = "down"
        icon = os.path.abspath("closed.svg")
    if unicode(person_uuid) == unicode(pnconfig.uuid):
        their = "your"
        name = "You"
        if handup == "on":
            icon = os.path.abspath("open-yellow.svg")
    PEOPLE[person_uuid][2].update("%s put %s hand %s" % (name, their, updown), "", icon)
    PEOPLE[person_uuid][2].show()
    hand_state = "closed.svg"
    #print "Checking whether people have their hands up"
    for p, hm in PEOPLE.items():
        h, m, n = hm
        if h == "on":
            if unicode(p) == unicode(pnconfig.uuid):
                print "I do, so let's go with a yellow hand, unless anyone else does too"
                hand_state = "open-yellow.svg"
            else:
                print p, "does, so it's a green hand icon"
                hand_state = "open-green.svg"
                break
    indicator.set_icon(os.path.abspath(hand_state))

def check_caps(pubnub):
    global CAPS_LOCK
    try:
        out = subprocess.check_output(["xset", "q"])
    except:
        pass
    else:
        lines = [x for x in out.split("\n") if "Caps Lock" in x]
        if len(lines) == 1:
            parts = lines[0].split(None)
            cl = parts[3]
            if cl != CAPS_LOCK:
                CAPS_LOCK = cl
                #print "setting", CAPS_LOCK
                pubnub.set_state().channels(CHANNEL_NAME).state({"handup": CAPS_LOCK}).sync()
    return True

def die(menuitem, pubnub):
    pubnub.unsubscribe().channels(CHANNEL_NAME).execute()
    gtk.main_quit()

def main():
    global indicator, menu
    indicator = appindicator.Indicator.new(APPINDICATOR_ID, os.path.abspath('closed.svg'), appindicator.IndicatorCategory.SYSTEM_SERVICES)
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)

    pubnub = set_up_pubnub()

    menu = gtk.Menu()
    item = gtk.MenuItem('Quit')
    item.connect('activate', die, pubnub)
    menu.append(item)
    menu.show_all()

    indicator.set_menu(menu)
    indicator.set_icon(os.path.abspath("closed.svg"))

    notify.init(APPINDICATOR_ID)

    GObject.timeout_add_seconds(1, check_caps, pubnub)
    gtk.main()

if __name__ == "__main__":
    main()


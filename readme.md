Simple program which uses pubnub to connect many users together and show whether each one wants to talk. It's for podcast presenters. To indicate you want to talk, turn on Caps Lock. To indicate that you don't want to talk, turn Caps Lock off again.


You'll need to set up a virtualenv:

```
virtualenv --system-site-packages ./venv
source ./venv/bin/activate
pip install 'pubnub>=4.0.11'
```

and then `python handsup.py` (yes, Python 2) should run the indicator. Yellow hand means "I have my hand up and nobody else does"; green hand means "other people have their hands up". Names of people with their hands up are in the drop-down menu (and are shown by popup notification).


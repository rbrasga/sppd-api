<a href="https://sppdreplay.net"><img src="https://i.imgur.com/CRA6jPP.png" title="SPPD Replay" alt="SPPDReplay"></a>

# REST API for South Park Phone Destroyer (SPPD)

> Allows access to public game data, like leaderboards

> Allows access to your user-specific game data, like your team's chat or TVT history

> Full list of REST APIs

- get Global Player Leaderboard
- get TVT Team Leaderboard
- get TeamWar Update (Votes or Caps or Scores, depending on the day)
- get Card Requests
- get Team Details
- get TeamID Search By Name
- get Team Applications (when someone applies to the team)
- get Teamwar History (members scores/caps for last 5 weeks)
- get Events
- get Team Event Participation
- set Accept Application
- set Reject Application
- set Team Role
- set Team Details (You can no longer change your team name)
- get Team Chat
- get User Details (includes their currently selected deck, does not apply to TVT-related matches/practice)
- get User Name (recommended: request up to 20 simultaneously)
- And others.

***How Does it work***

[![GPSoAuth](http://www.google.com/logos/doodles/2015/googles-new-logo-5078286822539264.3-hp2x.gif)]()

- Login using [gpsoauth](https://github.com/simon-weber/gpsoauth). Google Player Services oAuth Protocol
- Stores necessary tokens until they expire.
- Supports multiple simultaneous tokens
- Before each request, the tokens are verified to be valid, or if invalid, then refreshed.
- Single HTTP session per URI for maximum performance, though certain APIs require two seconds between each call (or they are ignored)

---

## Example (Optional)

- Good: Add an API call at the bottom of SPPD_API.py, then `./SPPD_API.py <username> <password>`
- Better:

```python
# code away!
import SPPD_API
import json

class SingleUser():
  ...  ...  ...
  def run(self):
    SPPD_API.setUsernamePassword("you@gmail.com","pw123")
    response_body = SPPD_API.getTeamWarUpdate() #Specific to you@gmail.com's team.
    result = processTeamWarUpdate(response_body)
    if result == None:
      print("Bad Data...")
#Mode:
# 0, vote days
# 1, upgrade days
# 2, battle days
  def processTeamWarUpdate(self,json_string):
    result={}
    try:
      result = json.loads(json_string)
    except Exception as e:
      print(str(e))
    if "configuration" in result and type(result["configuration"]) == dict:
      if "upgrade_start_time" in result["configuration"].keys():
        upgrade_start_time = result["configuration"]["upgrade_start_time"]
        if upgrade_start_time != self.UPGRADE_START_TIME:
          self.resetAllUpgrades()
          self.UPGRADE_START_TIME = upgrade_start_time
          last_refresh_pretty=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.UPGRADE_START_TIME))
          print(f"UPGRADE_START_TIME: {last_refresh_pretty}")
      if "battle_start_time" in result["configuration"].keys():
        battle_start_time = result["configuration"]["battle_start_time"]
        if battle_start_time != self.BATTLE_START_TIME:
          self.BATTLE_START_TIME = battle_start_time
          last_refresh_pretty=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.BATTLE_START_TIME))
          print(f"BATTLE_START_TIME: {last_refresh_pretty}")
    if '"mode": 1' in json_string or (self.BATTLE_START_TIME > time.time() - 300 and self.UPGRADE_START_TIME < time.time() + 1800):
      return self.processTeamWarUpgrades(json_string)
    elif '"mode": 2' in json_string:
      return self.processTeamWarBracket(json_string)
    elif '"mode": 0' in json_string:
      return 0 #Success, nothing to do
    return None #Fail
```

- Best: Reach out to the dozens of developers on the SPPD Replay Discord already using this API

---

### Setup

- Python 3.8 or higher
- pip install requests pytz gpsoauth

---

## Contributing

> To get started...

### Step 1

- **Option 1**
    - 🍴 Fork this repo!

- **Option 2**
    - 👯 Clone this repo to your local machine using

### Step 2

- **HACK AWAY!** 🔨🔨🔨

### Step 3

- 🔃 Create a new pull request using <a href="https://github.com/rbrasga/sppd-api/compare/" target="_blank">`https://github.com/rbrasga/sppd-api/compare/`</a>.

---

## Team

Before going open source, I had dozens of developers using this and recommending different ideas

---

## FAQ

- **Can I use my iOS account?**
    - No. Not until someone can spare some time to be the first person in the world to reverse engineer Apple Gamecenter's oAuth.

- **Can I call Python code from NodeJS?**
    - Where there's a will, [there's a way](https://discord.com/channels/@me/694341743780560966/795113507141976064)
---

## Support

- [File an issue here](https://github.com/rbrasga/sppd-api/issues)
- [Join the Discord Server](https://discord.gg/j4Wchza)

---

## Donations (Optional)

[Donate](https://sppdreplay.net/donate)


---

## License

GPLv3

## Join the SPPD Replay Discord Server

<a href="https://discord.gg/j4Wchza"><img src="https://i.imgur.com/XpgtidC.jpg" title="SPPD Replay Discord" alt="SPPDReplay"></a>

Not affiliated with Ubisoft/Redlynx.

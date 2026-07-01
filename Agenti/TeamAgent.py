# TeamAgent.py
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import random
import ast

# koliko posto dodira lopte po utakmici tipicno odlazi na svaku poziciju
ROLE_TOUCH_WEIGHTS = {"GK": 0.05, "DEF": 0.30, "MID": 0.40, "FWD": 0.25}

# vjerojatnost akcije po poziciji (prije primjene umora/rezultata)
ROLE_ACTION_WEIGHTS = {
    "GK":  {"pass": 0.95, "shot": 0.00, "foul": 0.05},
    "DEF": {"pass": 0.70, "shot": 0.05, "foul": 0.25},
    "MID": {"pass": 0.65, "shot": 0.25, "foul": 0.10},
    "FWD": {"pass": 0.45, "shot": 0.45, "foul": 0.10},
}

# kvaliteta zavrsnice po poziciji, mnozi se s xG
ROLE_FINISHING_QUALITY = {"GK": 0.5, "DEF": 0.7, "MID": 0.9, "FWD": 1.15}

# koliko brzo koja pozicija gubi kondiciju (GK gotovo stoji, FWD najvise sprinta)
ROLE_FATIGUE_RATE = {"GK": 0.3, "DEF": 0.9, "MID": 1.1, "FWD": 1.15}

# prosjecni player rating obje postave, koristi se za normalizaciju
RATING_BASELINE = 85


class TeamAgent(Agent):

    class RespondBehaviour(CyclicBehaviour):
        def pick_player(self):
            roles = list(ROLE_TOUCH_WEIGHTS.keys())
            weights = list(ROLE_TOUCH_WEIGHTS.values())
            role = random.choices(roles, weights=weights)[0]

            candidates = [p for p in self.agent.players if p["role"] == role]
            if not candidates:
                candidates = self.agent.players
                role = candidates[0]["role"]

            player = random.choice(candidates)
            self.agent.touches[player["name"]] += 1
            return player, role

        def action_weights(self, role, minute, score_diff):
            weights = dict(ROLE_ACTION_WEIGHTS[role])

            # umor raste kroz utakmicu i cini igru nemarnijom
            fatigue = minute / 90.0
            weights["foul"] *= (1 + 0.5 * fatigue)

            # pritisak/cuvanje rezultata u zavrsnici utakmice
            if minute >= 70 and role in ("MID", "FWD"):
                if score_diff < 0:
                    weights["shot"] *= 1.4
                    weights["pass"] *= 0.85
                elif score_diff > 0:
                    weights["shot"] *= 0.7
                    weights["pass"] *= 1.15

            return weights

        async def run(self):
            msg = await self.receive(timeout=1)
            if not msg:
                return

            try:
                req = ast.literal_eval(msg.body)
            except:
                return

            if req.get("type") != "REQUEST_ACTION":
                return

            minute = req["minute"]
            score_diff = req.get("score_diff", 0)
            team = self.agent.team_name
            skill = self.agent.skill
            self.agent.current_minute = minute

            player, role = self.pick_player()
            rating_factor = player.get("rating", RATING_BASELINE) / RATING_BASELINE

            weights = self.action_weights(role, minute, score_diff)
            action = random.choices(list(weights.keys()), weights=list(weights.values()))[0]

            xg_value = 0.0
            if action == "shot":
                base_xg = random.uniform(0.05, 0.35)
                xg_value = round(min(0.9, base_xg * skill * ROLE_FINISHING_QUALITY[role] * rating_factor), 2)
                if random.random() < xg_value:
                    action = "goal"

            event = {
                "minute": minute,
                "team": team,
                "player": player["name"],
                "role": role,
                "action": action,
                "xG": xg_value,
            }

            reply = Message(to=str(msg.sender))
            reply.body = str({"type": "ACTION", "event": event})
            await self.send(reply)

    def _fatigue(self, role, touches):
        minute = getattr(self, "current_minute", 0)
        raw = (minute / 90.0 * 55 + touches * 0.9) * ROLE_FATIGUE_RATE[role]
        return round(min(100.0, raw), 1)

    def get_roster_status(self):
        return {
            "team_name": self.team_name,
            "skill": self.skill,
            "players": [
                {
                    "name": p["name"],
                    "role": p["role"],
                    "rating": p.get("rating", RATING_BASELINE),
                    "touches": self.touches.get(p["name"], 0),
                    "fatigue": self._fatigue(p["role"], self.touches.get(p["name"], 0)),
                }
                for p in self.players
            ],
        }

    async def setup(self):
        self.players = getattr(self, "players", [])
        self.team_name = getattr(self, "team_name", "Team")
        self.skill = getattr(self, "skill", 1.0)
        self.current_minute = 0
        self.touches = {p["name"]: 0 for p in self.players}
        self.add_behaviour(self.RespondBehaviour())
        print(f"{self.team_name} started with {len(self.players)} players!")

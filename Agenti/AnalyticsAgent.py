from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import ast
import csv
from datetime import datetime


class AnalyticsAgent(Agent):

    async def setup(self):
        ##statistika po timu
        self.stats = {
            "Team A": {"goals": 0, "shots": 0, "passes": 0, "fouls": 0, "xG": 0.0},
            "Team B": {"goals": 0, "shots": 0, "passes": 0, "fouls": 0, "xG": 0.0},
        }

        self.events = []

        #posjed lopte
        self.current_possession = "Team A"
        self.possession_timeline = []  
        self.possession_minutes = {"Team A": 0, "Team B": 0}
        self.last_possession = None

        # CSV fajl za event log
        timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
        self.csv_filename = f"match_events_{timestamp}.csv" 

        with open(self.csv_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Minute", "Team", "Player", "Action", "xG"])

        print("Analitički agent je započeo s radom")
        print(f"Event log se sprema tu: {self.csv_filename}")

        self.add_behaviour(self.AnalysisBehaviour())

    class AnalysisBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=1)
            if not msg:
                return

            try:
                event = ast.literal_eval(msg.body)
            except Exception:
                return

            # obrada posjeda lopte
            if event.get("type") == "POSSESSION":
                minute = event.get("minute")
                team_poss = event.get("team_in_possession")

                if minute is None or team_poss not in ["Team A", "Team B"]:
                    return

                self.agent.current_possession = team_poss
                self.agent.possession_timeline.append({"minute": minute, "team": team_poss})
                self.agent.possession_minutes[team_poss] += 1

                # ispis samo kad se promijeni
                if self.agent.last_possession != team_poss:
                    print(f"[Posjed lopte] Minuta {minute}: {team_poss}")
                    self.agent.last_possession = team_poss

                return  

            
            try:
                team = event["team"]
                action = event["action"]
                xg_value = float(event.get("xG", 0.0))
            except Exception:
                return

            
            if action == "goal":
                self.agent.stats[team]["goals"] += 1
                self.agent.stats[team]["shots"] += 1
                self.agent.stats[team]["xG"] += xg_value
            elif action == "shot":
                self.agent.stats[team]["shots"] += 1
                self.agent.stats[team]["xG"] += xg_value
            elif action == "pass":
                self.agent.stats[team]["passes"] += 1
            elif action == "foul":
                self.agent.stats[team]["fouls"] += 1

            self.agent.events.append(event)

            
            with open(self.agent.csv_filename, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    event.get("minute"),
                    event.get("team"),
                    event.get("player"),
                    event.get("action"),
                    xg_value,
                ])

            
            prediction = self.predict()

            
            viz_msg = Message(to="viz@localhost")
            viz_msg.body = str({
                "stats": self.agent.stats,
                "latest_event": event,
                "prediction": prediction,
                "possession": {
                    "current": self.agent.current_possession,
                    "minutes": self.agent.possession_minutes,
                    "timeline": self.agent.possession_timeline
                }
            })
            await self.send(viz_msg)

            #za debuganje
            if action == "goal":
                score_a = self.agent.stats["Team A"]["goals"]
                score_b = self.agent.stats["Team B"]["goals"]
                print(f"\nGOAL: [{team}] {event.get('player')} scores! (xG: {xg_value:.2f})")
                print(f"Rezultat: Team A {score_a} - {score_b} Team B")
                print(f"Predviđanje: {prediction}\n")

        def predict(self):
            #za predviđanje pobjednika koriste se performanse pomnižene s "weights"
            def score(t):
                s = self.agent.stats[t]
                return (
                    s["goals"] * 4
                    + s["shots"] * 0.2
                    + s["xG"] * 3
                    + s["passes"] * 0.05
                    + s["fouls"] * -0.5   #fauli penaliziraju tim
                )

            a = score("Team A")
            b = score("Team B")
            if a > b:
                return "Tim A ima veće šanse za pobjedu"
            elif b > a:
                return "Tim B ima veće šanse za pobjedu"
            return "Neriješeno"

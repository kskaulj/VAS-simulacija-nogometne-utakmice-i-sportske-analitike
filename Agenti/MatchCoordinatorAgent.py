from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from spade.message import Message
import ast
import random


class MatchCoordinatorAgent(Agent):
    async def setup(self):
        self.minute = 0

        # posjed lopte
        self.possession = "Team A"
        self.last_possession_sent = None

        # dodajem uzastopna dodavanja po timu jer ona utječu na posjed lopte
        self.pass_streak = {
            "Team A": 0,
            "Team B": 0,
        }

        
        self.team_jids = {
            "Team A": "teama@localhost",
            "Team B": "teamb@localhost",
        }

        self.add_behaviour(self.MatchLoop(period=1.0))
        print("Coordinator is on!")

    class MatchLoop(PeriodicBehaviour):
        async def run(self):
            self.agent.minute += 1
            minute = self.agent.minute

            if minute > 90:
                print("[Coordinator] The match is over!")
                self.kill()
                return

            #šaljemo informacije analitici
            pos_msg = Message(to="analytics@localhost")
            pos_msg.body = str({
                "type": "POSSESSION",
                "minute": minute,
                "team_in_possession": self.agent.possession
            })
            await self.send(pos_msg)
            self.agent.last_possession_sent = self.agent.possession

            #traži se akcija od tima koj ima posjed lopte
            team = self.agent.possession
            team_jid = self.agent.team_jids[team]

            req = Message(to=team_jid)
            req.body = str({"type": "REQUEST_ACTION", "minute": minute})
            await self.send(req)

            
            reply = await self.receive(timeout=1)
            if not reply:
                
                return

            try:
                data = ast.literal_eval(reply.body)
            except Exception:
                return

            if data.get("type") != "ACTION":
                return

            event = data.get("event")
            if not isinstance(event, dict):
                return

            
            event["minute"] = minute

            # proslijedi event analitici
            out = Message(to="analytics@localhost")
            out.body = str(event)
            await self.send(out)

            # PRAVILA ZA POSJED LOPTE
            action = event.get("action")
            event_team = event.get("team")  #tim koji je napravio akciju
            if event_team not in ("Team A", "Team B"):
                event_team = self.agent.possession

            other_team = "Team B" if event_team == "Team A" else "Team A"

            #pass povećava streak i s time šansu da se izgubi posjed lopte
            if action == "pass":
                self.agent.pass_streak[event_team] += 1
                streak = self.agent.pass_streak[event_team]

                turnover_prob = 0.05
                if streak >= 4:
                    turnover_prob = 0.15
                if streak >= 7:
                    turnover_prob = 0.35
                if streak >= 10:
                    turnover_prob = 0.65

                if random.random() < turnover_prob:
                    #izgubljena lopta / presječena lopta
                    self.agent.possession = other_team
                    self.agent.pass_streak[event_team] = 0

            #faul će uvijek promijenit posjed lopte
            elif action == "foul":
                self.agent.possession = other_team
                self.agent.pass_streak[event_team] = 0

            # šut i gol resetiraju streak 
            elif action in ("shot", "goal"):
                self.agent.pass_streak[event_team] = 0
                if random.random() < 0.6:
                    self.agent.possession = other_team

            
            else:
                self.agent.pass_streak[event_team] = 0

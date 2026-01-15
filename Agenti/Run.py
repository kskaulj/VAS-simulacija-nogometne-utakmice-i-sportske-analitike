import asyncio
import threading
import csv
from datetime import datetime

from TeamAgent import TeamAgent
from AnalyticsAgent import AnalyticsAgent
from VisualizationAgent import VisualizationAgent
from MatchCoordinatorAgent import MatchCoordinatorAgent
from dashboard import run_dashboard


async def main():
    print("=" * 50)
    print("POČETAK SIMULACIJE")
    print("=" * 50)

    
    team_a = TeamAgent("teama@localhost", "password")
    team_a.team_name = "Team A"
    team_a.players = [
        "Modrić", "Perišić", "Mandžukić", "Rakitić", "Vida",
        "Vrsaljko", "Rebić", "Brozović", "Kovačić", "Subašić", "Strinić"
    ]

    
    team_b = TeamAgent("teamb@localhost", "password")
    team_b.team_name = "Team B"
    team_b.players = [
        "Ronaldo", "Messi", "Neymar", "Mbappé", "Benzema",
        "De Bruyne", "Salah", "Lewandowski", "Haaland", "Neuer", "Ramos"
    ]

   
    analytics = AnalyticsAgent("analytics@localhost", "password")
    viz = VisualizationAgent("viz@localhost", "password")

   
    match = MatchCoordinatorAgent("match@localhost", "password")


    
    await analytics.start()
    await asyncio.sleep(0.5)

    await viz.start()
    await asyncio.sleep(0.5)

    await team_a.start()
    await asyncio.sleep(0.5)

    await team_b.start()
    await asyncio.sleep(0.5)

    await match.start()
    await asyncio.sleep(0.5)

    
    print("\nDASHBOARD: http://localhost:5000")
    dashboard_thread = threading.Thread(target=run_dashboard, args=(viz,), daemon=True)
    dashboard_thread.start()

    print("\nThe match has begun.")
    print("=" * 50)
    print()

 
    max_seconds = 120
    waited = 0
    while match.is_alive() and waited < max_seconds:
        await asyncio.sleep(1)
        waited += 1

   
    print("\n" + "=" * 50)
    print(
        f"FINAL RESULT: Team A {analytics.stats['Team A']['goals']} - "
        f"{analytics.stats['Team B']['goals']} Team B"
    )
    print(f"TIM A: {analytics.stats['Team A']}")
    print(f"TIM B: {analytics.stats['Team B']}")
    print("=" * 50)

   
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stats_filename = f"match_stats_{timestamp}.csv"

    with open(stats_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Team", "Goals", "Shots", "Passes", "Fouls", "xG"])
        writer.writerow([
            "Team A",
            analytics.stats["Team A"]["goals"],
            analytics.stats["Team A"]["shots"],
            analytics.stats["Team A"]["passes"],
            analytics.stats["Team A"]["fouls"],
            round(analytics.stats["Team A"]["xG"], 2),
        ])
        writer.writerow([
            "Team B",
            analytics.stats["Team B"]["goals"],
            analytics.stats["Team B"]["shots"],
            analytics.stats["Team B"]["passes"],
            analytics.stats["Team B"]["fouls"],
            round(analytics.stats["Team B"]["xG"], 2),
        ])

    print(f"\nStats saved to: {stats_filename}")
    print(f"Event log: {analytics.csv_filename}")

   
    await match.stop()
    await team_a.stop()
    await team_b.stop()
    await analytics.stop()
    await viz.stop()

    print("\nMatch is finished.")
    

    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nbye!")


if __name__ == "__main__":
    asyncio.run(main())

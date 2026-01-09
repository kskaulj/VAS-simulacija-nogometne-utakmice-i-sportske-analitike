from flask import Flask, jsonify, render_template_string

app = Flask(__name__)
viz_agent = None

HTML = """
<!doctype html>
<html>
<head>
  <title>Soccer MAS Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>

<h1>Live Soccer Dashboard</h1>
<h2 id="minute"></h2>
<h2 id="prediction"></h2>

<div id="goals"></div>
<div id="shots"></div>
<div id="xg"></div>

<h2>Goals per Player</h2>
<div id="player_goals"></div>

<h2>Top Scorers</h2>
<ul id="top_scorers"></ul>

<script>
async function update() {
  const r = await fetch("/data");
  const d = await r.json();
  if (!d.stats || !d.stats["Team A"]) return;

  document.getElementById("minute").innerText = "Minute: " + d.minute;
  document.getElementById("prediction").innerText = "Prediction: " + d.prediction;

  ["goals","shots","xg"].forEach(m => {
    Plotly.react(m, [{
      x:["Team A","Team B"],
      y:[d.stats["Team A"][m], d.stats["Team B"][m]],
      type:"bar"
    }], {title:m.toUpperCase()});
  });

  const playersA = Object.keys(d.players["Team A"]);
  const goalsA = playersA.map(p => d.players["Team A"][p].goals);
  const playersB = Object.keys(d.players["Team B"]);
  const goalsB = playersB.map(p => d.players["Team B"][p].goals);

  Plotly.react("player_goals", [
    {x: playersA, y: goalsA, type:"bar", name:"Team A"},
    {x: playersB, y: goalsB, type:"bar", name:"Team B"}
  ], {barmode:"group"});

  let all = [];
  for (const t in d.players) {
    for (const p in d.players[t]) {
      all.push({player:p, goals:d.players[t][p].goals});
    }
  }
  all.sort((a,b)=>b.goals-a.goals);

  const ul = document.getElementById("top_scorers");
  ul.innerHTML = "";
  all.slice(0,5).forEach(p=>{
    ul.innerHTML += `<li>${p.player}: ${p.goals}</li>`;
  });
}

setInterval(update, 300);
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/data")
def data():
    if not viz_agent:
        return jsonify({})
    return jsonify({
        "stats": viz_agent.stats,
        "players": viz_agent.players,
        "prediction": viz_agent.prediction,
        "minute": viz_agent.minute
    })

def run_dashboard(agent):
    global viz_agent
    viz_agent = agent
    app.run(debug=False, threaded=True)

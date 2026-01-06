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

<script>
async function update() {
  const r = await fetch("/data");
  const d = await r.json();

  if (!d.stats || !d.stats["Team A"]) return;

  document.getElementById("prediction").innerText =
      "Prediction: " + d.prediction;
  document.getElementById("minute").innerText =
      "Minute: " + d.minute;

  ["goals", "shots", "xg"].forEach(m => {
    Plotly.react(m, [{
      x: ["Team A", "Team B"],
      y: [d.stats["Team A"][m], d.stats["Team B"][m]],
      type: "bar"
    }], {
      title: m.toUpperCase()
    });
  });
}

setInterval(update, 200);
</script>

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)



@app.route("/data")
def data():
    if not viz_agent or not viz_agent.stats:
        return jsonify({
            "stats": {},
            "prediction": "Waiting...",
            "minute": 0
        })

    return jsonify({
        "stats": viz_agent.stats,
        "prediction": viz_agent.prediction,
        "minute": viz_agent.minute
    })


def run_dashboard(agent):
    global viz_agent
    viz_agent = agent
    app.run(debug=False, threaded=True)

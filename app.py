from flask import Flask, jsonify, redirect, render_template, request, url_for

from worldcup.cache import get_match_data, refresh_match_data


app = Flask(__name__)


@app.get("/")
def index():
    data = get_match_data()
    matches = data.get("matches", [])
    next_match_index = next(
        (index for index, match in enumerate(matches) if match.get("status") != "played"),
        None,
    )
    stages = sorted({match["stage"] for match in matches if match.get("stage")})
    groups = [f"Group {letter}" for letter in "ABCDEFGHIJKL"]

    return render_template(
        "index.html",
        matches=matches,
        next_match_index=next_match_index,
        metadata=data.get("metadata", {}),
        error=data.get("error"),
        stages=stages,
        groups=groups,
    )


@app.get("/refresh")
def refresh():
    refresh_match_data()
    return redirect(url_for("index"))


@app.get("/api/matches")
def api_matches():
    data = get_match_data(force_refresh=request.args.get("refresh") == "1")
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)

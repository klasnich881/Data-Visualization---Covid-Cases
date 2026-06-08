from io import StringIO

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_from_directory

app = Flask(__name__)

DATA_FILE = "COVID_Country_Sample.csv"
CLEANED_FILE = "COVID_Country_Sample_Cleaned.csv"

ALLOWED_METRICS = {
    "new_cases": "New Cases",
    "new_vaccinations": "New Vaccinations",
    "new_cases_roll3": "3-Month Rolling Cases",
}


def load_and_prepare_data():
    raw = pd.read_csv(DATA_FILE, parse_dates=["date"])

    print("\n===== head() =====")
    print(raw.head().to_string(index=False))

    print("\n===== info() =====")
    info_buffer = StringIO()
    raw.info(buf=info_buffer)
    print(info_buffer.getvalue())

    df = raw.copy()
    df = df.sort_values(["country", "date"]).reset_index(drop=True)

    if "new_vaccinations" in df.columns:
        df["new_vaccinations"] = (
            df.groupby("country")["new_vaccinations"]
            .transform(lambda s: s.interpolate(limit_direction="both"))
            .fillna(0)
        )

    for metric in ["new_cases", "new_vaccinations"]:
        if metric in df.columns:
            q1 = df.groupby("country")[metric].transform(lambda s: s.quantile(0.25))
            q3 = df.groupby("country")[metric].transform(lambda s: s.quantile(0.75))
            iqr = q3 - q1
            lower = (q1 - 1.5 * iqr).clip(lower=0)
            upper = q3 + 1.5 * iqr
            df[metric] = df[metric].clip(lower=lower, upper=upper)

   
    df["new_cases_roll3"] = (
        df.groupby("country")["new_cases"]
        .transform(lambda s: s.rolling(window=3, min_periods=1).mean())
        .round(2)
    )

    df.to_csv(CLEANED_FILE, index=False)
    return df


DF = load_and_prepare_data()


@app.route("/style/style.css")
def style_css():
    return send_from_directory("style", "style.css")


@app.route("/script.js")
def script_js():
    return send_from_directory(".", "script.js")


@app.route("/")
def index():
    countries = sorted(DF["country"].unique().tolist())
    start_date = DF["date"].min().strftime("%Y-%m-%d")
    end_date = DF["date"].max().strftime("%Y-%m-%d")
    default_country = "Canada" if "Canada" in countries else countries[0]

    return render_template(
        "index.html",
        countries=countries,
        start_date=start_date,
        end_date=end_date,
        default_country=default_country,
    )


@app.route("/data")
def data():
    country = request.args.get("country", default="Canada")
    metric = request.args.get("metric", default="new_cases")

    if metric not in ALLOWED_METRICS:
        metric = "new_cases"

    valid_countries = DF["country"].unique().tolist()
    if country not in valid_countries:
        country = "Canada" if "Canada" in valid_countries else valid_countries[0]

    filtered = DF[DF["country"] == country].sort_values("date")[["date", metric]]
    records = filtered.assign(
        date=filtered["date"].dt.strftime("%Y-%m-%d")
    ).to_dict(orient="records")

    return jsonify(
        {
            "country": country,
            "metric": metric,
            "metric_label": ALLOWED_METRICS[metric],
            "series": records,
        }
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5001)

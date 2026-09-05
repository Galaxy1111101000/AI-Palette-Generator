from flask import Flask, render_template, request
from palette_agent import generate_palette


app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    description = request.form.get("description", "").strip()

    if not description:
        return render_template(
            "index.html",
            error="Please describe the Palette you want."
        )

    palette = generate_palette(description)

    return render_template(
        "index.html",
        palette = palette,
        description = description
    )

if __name__ == "__main__":
    app.run(debug=True)
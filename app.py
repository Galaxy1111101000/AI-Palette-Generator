from flask import Flask, render_template, request
from palette_agent import generate_palette, generate_palette_from_image
from pathlib import Path
from werkzeug.utils import secure_filename



app = Flask(__name__, static_folder="styles", static_url_path="/styles")

app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    description = request.form.get("description", "").strip()
    photo = request.files.get("photo")

    if photo and photo.filename:
        if not photo.mimetype.startswith("image/"):
            return render_template(
                "index.html",
                error="Please upload an image file.",
                description=description,
            )

        upload_path = Path(app.instance_path) / "uploads" / photo.filename
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        photo.save(upload_path)

        palette = generate_palette_from_image(str(upload_path))
        return render_template("index.html", palette=palette)
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

@app.route("/preview")
def preview():
    fallback_colours = [
        "#F4F0E8",
        "#FFF8EA",
        "#B7612D",
        "#1A0E0F",
        "#75361D",
        "#D99A52",
    ]
    requested_colours = [
        colour.strip().upper()
        for colour in request.args.get("colours", "").split(",")
        if len(colour.strip()) == 7 and colour.strip().startswith("#")
    ]
    palette_colours = (requested_colours + fallback_colours)[:6]

    return render_template(
        "preview.html",
        palette_colours=palette_colours,
    )

if __name__ == "__main__":
    app.run(debug=True)
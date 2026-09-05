from flask import Flask, render_template, request
from palette_agent import generate_palette, generate_palette_from_image
from pathlib import Path
from werkzeug.utils import secure_filename



app = Flask(__name__)

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

if __name__ == "__main__":
    app.run(debug=True)
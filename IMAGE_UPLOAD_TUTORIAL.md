# Tutorial: Generate a Colour Palette from an Uploaded Photo

This tutorial shows how to extend the Palette Agent so a user can upload a photo and receive a colour palette based on the image.

The project already has two useful pieces:

- `app.py` receives form data and calls the palette agent.
- `palette_agent.py` asks the language model for a structured `Palette` containing named colours, hex values, and roles.

The new feature adds one small step between those pieces: extract representative colours from the photo, then give those colours to the existing agent so it can name them and explain how to use them.

## 1. Install the image library

Pillow is the Python library used to open images and sample their colours.

From the `palette-agent` folder, run:

```powershell
.\.venv\Scripts\python.exe -m pip install Pillow
```

If you are not using a virtual environment, use:

```powershell
python -m pip install Pillow
```

## 2. Add a colour-extraction helper

Add this function to `palette_agent.py`:

```python
from PIL import Image


def extract_image_colours(image_path: str, colour_count: int = 5) -> list[str]:
    """Return representative colours from an image as hexadecimal values."""
    with Image.open(image_path) as image:
        image = image.convert("RGB")
        image.thumbnail((200, 200))
        reduced = image.quantize(colors=colour_count)
        palette = reduced.getpalette()

        colours = []
        for red, green, blue in reduced.getcolors():
            offset = red * 3
            colour = palette[offset:offset + 3]
            colours.append("#{:02X}{:02X}{:02X}".format(*colour))

        return colours
```

The image is reduced to a small size before quantization. This makes the operation quick and prevents a large upload from consuming unnecessary memory. Quantization groups similar pixels and gives us a short list of representative colours.

For production, sort the colours by frequency before returning them. A complete version is:

```python
def extract_image_colours(image_path: str, colour_count: int = 5) -> list[str]:
    with Image.open(image_path) as image:
        image = image.convert("RGB")
        image.thumbnail((200, 200))
        reduced = image.quantize(colors=colour_count)
        palette = reduced.getpalette()

        colour_groups = sorted(
            reduced.getcolors(),
            reverse=True,
        )

        colours = []
        for pixel_count, palette_index in colour_groups:
            offset = palette_index * 3
            red, green, blue = palette[offset:offset + 3]
            colours.append("#{:02X}{:02X}{:02X}".format(red, green, blue))

        return colours
```

## 3. Let the agent accept sampled colours

The existing `generate_palette` function accepts a text description. Keep that public function, but add a second helper below it:

```python
def generate_palette_from_image(image_path: str) -> Palette:
    image_colours = extract_image_colours(image_path)
    description = (
        "Create a usable design palette from these colours sampled from an uploaded photo: "
        + ", ".join(image_colours)
        + ". Keep the sampled colours recognizable, improve contrast where needed, "
          "and assign practical roles such as background, text, primary, secondary, or accent."
    )
    return generate_palette(description)
```

This keeps the language model responsible for the part it is good at: naming colours, describing mood, and assigning design roles. Pillow remains responsible for the objective image-processing step.

## 4. Add an upload field to the HTML form

Update the form in `templates/index.html`:

```html
<form method="POST" action="/generate" enctype="multipart/form-data">
    <label for="description">Describe a palette</label>
    <input
        id="description"
        type="text"
        name="description"
        placeholder="A calm coastal palette with ocean blue and warm sand"
        value="{{ description or '' }}"
    >

    <label for="photo">Or upload a photo</label>
    <input
        id="photo"
        type="file"
        name="photo"
        accept="image/png,image/jpeg,image/webp"
    >

    <button type="submit">Generate palette</button>
</form>
```

`enctype="multipart/form-data"` is required. Without it, the browser will not send the image bytes to Flask.

The description should no longer have the `required` attribute because the user can now provide either a description or a photo.

## 5. Update the Flask route

Import the new helper in `app.py`:

```python
from palette_agent import generate_palette, generate_palette_from_image
```

Then replace the body of the `/generate` route with:

```python
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

    if description:
        palette = generate_palette(description)
        return render_template(
            "index.html",
            palette=palette,
            description=description,
        )

    return render_template(
        "index.html",
        error="Enter a description or upload a photo.",
        description=description,
    )
```

Also add this import at the top of `app.py`:

```python
from pathlib import Path
```

### Important production improvement

The example above uses the original filename for clarity. In a deployed app, never trust a filename supplied by a browser. Use Flask's `secure_filename`, generate a unique name, enforce a maximum upload size, and delete temporary files after palette generation.

At minimum, add:

```python
from werkzeug.utils import secure_filename

app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
```

Then save with a generated name rather than `photo.filename`.

## 6. Test the feature

Start the app:

```powershell
.\.venv\Scripts\python.exe .\app.py
```

Open `http://127.0.0.1:5000` and test these cases:

1. Submit only a text description. The original behaviour should still work.
2. Upload a PNG or JPEG without a description. The agent should return a palette based on the sampled colours.
3. Submit neither field. The page should show an error.
4. Upload a text file renamed as an image. The route should reject it. For stronger validation, inspect the file contents with Pillow rather than relying only on the MIME type.
5. Upload an image larger than the configured limit. Flask should reject it before processing.

## 7. The data flow

```text
Photo upload
    -> Flask receives the file
    -> Pillow reduces and quantizes the image
    -> Representative hex colours are extracted
    -> The existing palette agent names and organizes them
    -> The template renders the Palette object
```

## Why this design works

The image does not need to be sent to the language model. That keeps the feature simpler and makes the output reproducible: the image-processing library finds the colours, while the existing agent turns those colours into a useful design system. It also means your current structured `Palette` response and swatch template can remain unchanged.

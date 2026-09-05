import os
from typing import List

from html import escape
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

class Colour(BaseModel):
    name: str = Field(description="A descriptive name for the colour")
    hex: str = Field(description="A 6 digit hexadecimal colour value")
    role: str = Field(description="The colour's role, such as background, text, primary or accent")

class Palette(BaseModel):
    title: str = Field(description="A short name for the palette")
    description: str = Field(description="A brief description of a palette's mood and visual direction")
    colours: List[Colour] = Field(
        min_length = 3,
        max_length = 6,
        description = "between 3 and 6 colours"
    )

model = ChatOpenAI(
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    temperature = 0.7
)

agent = create_agent(
    model = model,
    response_format = Palette,
    system_prompt="""

    You are a colour palette expert.

    Create a clear and consistent colour palette based on the user's description
    Rules:
    - Return between 3 and 6 colours.
    - Every colour must use a valid six-digit hexadecimal value.
    - Use uppercase hexadecimal values, for example #1A2B3C.
    - Give each colour a descriptive name.
    - Assign each colour a practical role.
    - Consider contrast and readability.
    - There must be at least one dark colour, one medium tone and one light tone
    - Do not use duplicate colours.
    """
)

def generate_palette(description: str) -> Palette:
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": description,
                }
            ]
        }
    )

    return result["structured_response"]

def create_html_page(palette: Palette) -> None:
    template_path = Path("palette-agent/palette.html")
    output_path = Path("palette_preview.html")

    template = template_path.read_text(encoding="utf-8")


    swatches = "\n".join(
        f"""
        <article class="swatch" style="background-color: {escape(colour.hex)}">
            <strong>{escape(colour.name)}</strong>
            <strong>{escape(colour.hex)}</strong>
            <strong>{escape(colour.role)}</strong>
        </article>
        """

        for colour in palette.colours
    )

    page = template.replace("{{TITLE}}", escape(palette.title))
    page = page.replace("{{DESCRIPTION}}", escape(palette.description))
    page = page.replace("{{SWATCHES}}", swatches)

    output_path.write_text(page, encoding="utf-8")

if __name__ == "__main__":
    description = input("Description:")

    if not description:
        raise SystemExit("Please try again")
    
    palette = generate_palette(description)

    print(f"\n{palette.title}")
    print("\nColours")

    for colour in palette.colours:
        print(f"\n {colour.name}: {colour.hex}, {colour.role}")

    create_html_page(palette)
    print("Saved")
from pathlib import Path
from langchain_core.prompts import load_prompt

def my_prompt_load(name: str):
    path = Path(__file__).parents[2] / "prompts" / f"{name}"
    template = load_prompt(path, encoding="utf-8")
    return template
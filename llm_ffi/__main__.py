import shutil
from pathlib import Path

import click

from llm_ffi.function import FunctionSpec, find_existing_llm_code, find_llm_functions
from llm_ffi.generate import generate_files, generate_implementation
from llm_ffi.llm_connector import LLMExternalInference, LLMInterface


@click.group()
def cli():
    pass


@cli.command()
@click.argument("module_path", type=click.Path(exists=True, path_type=Path))
@click.option("--model", default="claude-sonnet-4-20250514")
@click.option("--force", is_flag=True, help="Regenerate even if spec hash unchanged")
def generate(module_path: Path, model: str, force: bool):
    specs: list[FunctionSpec] = find_llm_functions(module_path)
    try:
        existing_specs = find_existing_llm_code(
            module_path, function_names=[spec.name for spec in specs]
        )
    except FileNotFoundError:
        existing_specs = []
    if len(specs) == 0:
        click.echo(f"No @llm_impl functions found in {module_path}")
        return

    implementations = {}
    specs_to_generate = []
    external_llm: LLMInterface = LLMExternalInference.from_config(model_name=model)

    for spec in specs:
        exists = next(
            iter([s for s in existing_specs if s.spec_hash == spec.spec_hash]), None
        )
        if exists is not None and not force:
            click.echo(f"Skipping {spec.name} (unchanged spec)")
        else:
            click.echo(f"Generating {spec.name}...")
            implementations[spec.name] = generate_implementation(spec, external_llm)
            specs_to_generate.append(spec)

    if specs_to_generate:
        generate_files(module_path, specs_to_generate, implementations, model)
        click.echo(f"✓ Generated {len(specs_to_generate)} function(s)")
    else:
        click.echo("✓ All functions up to date")


@cli.command()
@click.argument("module_path", type=click.Path(exists=True, path_type=Path))
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def clear(module_path: Path, yes: bool):
    """Clear all generated code for a module"""
    if not module_path.is_file():
        click.echo(f"Error: {module_path} is not a file")
        return

    generated_dir = module_path.parent / f"{module_path.stem}_llm_generated"

    if not generated_dir.exists():
        click.echo(f"No generated code found for {module_path.name}")
        return

    if not yes:
        click.confirm(
            f"Delete {generated_dir}?",
            abort=True,
        )

    shutil.rmtree(generated_dir)
    click.echo(f"✓ Cleared generated code for {module_path.name}")


if __name__ == "__main__":
    cli()

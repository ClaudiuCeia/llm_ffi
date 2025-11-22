import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from llm_ffi.utils import compute_hash

# Import only for type checking to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from llm_ffi.generate import FunctionImplementationPrefix


@dataclass
class FunctionSpec:
    name: str
    source: str
    spec_hash: str
    code_hash: str


def find_llm_generated_function(generated_file_path: Path) -> FunctionSpec:
    """Load metadata from a single generated file - read hashes from header"""
    from llm_ffi.generate import FunctionImplementationPrefix, extract_function_from_generated_file

    file_content = generated_file_path.read_text()

    # Parse header to get metadata (spec_hash, code_hash)
    header = FunctionImplementationPrefix.from_file_content(file_content)

    # Extract function source without header
    function_source = extract_function_from_generated_file(file_content)

    return FunctionSpec(
        name=header.function_name,
        source=function_source,
        spec_hash=header.spec_hash,
        code_hash=header.code_hash,
    )


def find_existing_llm_code(
    module_path: Path, function_names: list[str]
) -> list[FunctionSpec]:
    """Find existing generated code - read metadata from headers"""
    functions = []
    if not module_path.is_file():
        raise ValueError("Expected a file, not a directory")
    target_file_dir = module_path.parent / f"{module_path.stem}_llm_generated"
    if not target_file_dir.exists():
        raise FileNotFoundError(f"Could not find {target_file_dir}")

    for generated_file in target_file_dir.glob("*.llm_generated.py"):
        spec = find_llm_generated_function(generated_file)
        if spec.name in function_names:
            functions.append(spec)

    return functions


def has_llm_impl(node: ast.AST) -> bool:
    if not hasattr(node, "decorator_list"):
        return False
    return any(
        isinstance(dec, ast.Name) and dec.id == "llm_impl"
        for dec in node.decorator_list
    )


def find_llm_functions(module_path: Path) -> list[FunctionSpec]:
    return find_functions(module_path, has_llm_impl)


def find_functions(
    module_path: Path, function_filter: Callable[[ast.AST], bool]
) -> list[FunctionSpec]:
    """Find functions in `module_path` with a @llm_impl decorator tag"""
    source = module_path.read_text()
    tree = ast.parse(source)
    specs = []

    # Only look at top-level functions, not nested ones
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if not function_filter(node):
                continue
            func_source = ast.get_source_segment(source, node)
            if func_source is None:
                raise RuntimeError(f"Could not get Source for {ast.Name}")
            spec_text = f"{node.name}{ast.unparse(node.args)}\n"
            maybe_docstring = ast.get_docstring(node)
            if maybe_docstring is not None:
                spec_text += maybe_docstring
            body_source = "\n".join(ast.unparse(stmt) for stmt in node.body)
            specs.append(
                FunctionSpec(
                    node.name,
                    func_source,
                    compute_hash(spec_text),
                    compute_hash(body_source),
                )
            )

    return specs

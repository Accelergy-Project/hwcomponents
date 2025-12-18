from docutils import nodes
from docutils.parsers.rst import Directive
import importlib
import inspect
import ast


class IncludeDocstring(Directive):
    required_arguments = 1  # fully-qualified name

    def run(self):
        fqname = self.arguments[0]
        parts = fqname.split(".")

        # --- progressively import the longest valid module ---
        module = None
        for i in range(len(parts), 0, -1):
            try:
                module = importlib.import_module(".".join(parts[:i]))
                rest = parts[i:]
                break
            except ImportError:
                continue

        if module is None:
            return []

        obj = module
        for part in rest:
            # Normal attribute
            if hasattr(obj, part):
                obj = getattr(obj, part)
                continue

            # --- Check if obj is a class with annotations ---
            if inspect.isclass(obj) and hasattr(obj, "__annotations__") and part in obj.__annotations__:
                # Try to extract inline docstring using AST
                try:
                    source = inspect.getsource(obj)
                    tree = ast.parse(source)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            for i, item in enumerate(node.body):
                                # Look for annotated assignment (attribute with type hint)
                                if isinstance(item, ast.AnnAssign):
                                    if isinstance(item.target, ast.Name) and item.target.id == part:
                                        # Check if next item is a string (docstring)
                                        if i + 1 < len(node.body):
                                            next_item = node.body[i + 1]
                                            if isinstance(next_item, ast.Expr) and isinstance(next_item.value, ast.Constant):
                                                if isinstance(next_item.value.value, str):
                                                    text = next_item.value.value.strip()
                                                    return [nodes.paragraph(text=text)]
                except (OSError, TypeError, SyntaxError):
                    pass

            # --- Pydantic v2 field ---
            if hasattr(obj, "model_fields") and part in obj.model_fields:
                field = obj.model_fields[part]
                text = (
                    field.description
                    or (field.json_schema_extra or {}).get("description")
                )
                return [nodes.paragraph(text=text)] if text else []

            # --- Pydantic v1 field ---
            if hasattr(obj, "__fields__") and part in obj.__fields__:
                field = obj.__fields__[part]
                text = field.field_info.description
                return [nodes.paragraph(text=text)] if text else []

            return []

        # Fallback: normal __doc__
        doc = getattr(obj, "__doc__", None)
        return [nodes.paragraph(text=doc.strip())] if doc else []


def setup(app):
    app.add_directive("include-docstring", IncludeDocstring)